from dataclasses import dataclass
import threading
import time
from typing import Literal

import requests

from _lib_path import ensure_lib_path
from auth_password import hash_password, passwords_match, validate_password
from miniapp_config import MiniAppConfig
from yclients_adapter import (
    YClientsError,
    YClientsNetworkError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from yclients.formatters_cabinet import _client_name  # noqa: E402
from utils.client_name import client_has_surname, client_names_match  # noqa: E402
from utils.phone import format_phone_display, normalize_phone  # noqa: E402
from utils import storage  # noqa: E402

_PENDING_TTL_SEC = 600
_pending: dict[int, tuple[str, dict, float]] = {}
_pending_lock = threading.Lock()


def clear_pending_auth() -> None:
    with _pending_lock:
        _pending.clear()


@dataclass(frozen=True)
class AuthStatus:
    authenticated: bool
    phone: str | None = None
    phone_display: str | None = None
    client_name: str | None = None


@dataclass(frozen=True)
class PhoneCheckResult:
    step: Literal["name", "password"]
    phone: str
    requires_surname: bool


@dataclass(frozen=True)
class VerifyResult:
    phone: str
    phone_display: str
    needs_password: bool = False
    client_name: str | None = None


class AuthError(Exception):
    code: str

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _remember_phone_step(vk_user_id: int, phone: str, profile: dict) -> None:
    with _pending_lock:
        _pending[vk_user_id] = (phone, profile, time.monotonic())


def _take_phone_step(vk_user_id: int, phone: str) -> dict | None:
    with _pending_lock:
        entry = _pending.get(vk_user_id)
    if not entry:
        return None
    pending_phone, profile, cached_at = entry
    if time.monotonic() - cached_at > _PENDING_TTL_SEC:
        with _pending_lock:
            _pending.pop(vk_user_id, None)
        return None
    if pending_phone != phone:
        return None
    return profile


def _forget_phone_step(vk_user_id: int) -> None:
    with _pending_lock:
        _pending.pop(vk_user_id, None)


def _fetch_client_profile(phone: str, config: MiniAppConfig) -> dict | None:
    yclients = create_yclients_client(config)
    try:
        return yclients.find_client_by_phone(phone)
    except YClientsNetworkError:
        raise AuthError(
            "yclients_timeout",
            "YClients не отвечает. Проверьте интернет; попробуйте с VPN или без него.",
        ) from None
    except YClientsPermissionError:
        raise AuthError(
            "service_unavailable",
            "Сервис временно недоступен. Обратитесь к администратору студии.",
        ) from None
    except YClientsError as error:
        raise AuthError("fetch_error", str(error)) from error
    except requests.RequestException:
        raise AuthError(
            "service_unavailable",
            "Не удалось связаться с YClients. Проверьте интернет и попробуйте снова.",
        ) from None


def _is_authenticated_row(row: dict) -> bool:
    if not row.get("phone") or not row.get("password_hash"):
        return False
    return row.get("logged_in") is not False


def get_auth_status(vk_user_id: int, config: MiniAppConfig | None = None) -> AuthStatus:
    return auth_status_from_row(storage.get_user_auth_state(vk_user_id))


def auth_status_from_row(row: dict) -> AuthStatus:
    if not _is_authenticated_row(row):
        return AuthStatus(authenticated=False)

    phone = row["phone"]
    return AuthStatus(
        authenticated=True,
        phone=phone,
        phone_display=format_phone_display(phone),
        client_name=row.get("client_name") or None,
    )


def get_boot_state(vk_user_id: int) -> tuple[AuthStatus, dict]:
    row = storage.get_user_auth_state(vk_user_id)
    scheme = row.get("color_scheme") or "light"
    if scheme not in ("light", "dark"):
        scheme = "light"
    prefs = {
        "colorScheme": scheme,
        "welcomeBannerSeen": bool(row.get("welcome_banner_seen")),
    }
    return auth_status_from_row(row), prefs


def check_phone(vk_user_id: int, raw_phone: str, config: MiniAppConfig) -> PhoneCheckResult:
    phone = normalize_phone(raw_phone)
    if not phone:
        raise AuthError(
            "invalid_phone",
            "Не удалось распознать номер. Попробуйте, например: 89991234567",
        )

    profile = _fetch_client_profile(phone, config)
    if not profile:
        raise AuthError(
            "client_not_found",
            "По этому номеру нет карточки в студии. "
            f"Если вы ещё не записывались — оформите первую запись онлайн: {config.yclients_booking_url}",
        )

    _remember_phone_step(vk_user_id, phone, profile)

    if storage.has_password_for_phone(phone):
        return PhoneCheckResult(step="password", phone=phone, requires_surname=False)

    return PhoneCheckResult(
        step="name",
        phone=phone,
        requires_surname=client_has_surname(profile),
    )


def verify_name(
    vk_user_id: int,
    phone: str,
    raw_name: str,
    config: MiniAppConfig,
) -> VerifyResult:
    name = raw_name.strip()
    if not name:
        raise AuthError(
            "invalid_name",
            "Напишите имя (и фамилию, если она есть в студии).",
        )

    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise AuthError("invalid_phone", "Некорректный номер телефона.")

    profile = _take_phone_step(vk_user_id, normalized_phone)
    if profile is None:
        raise AuthError(
            "session_expired",
            "Сессия входа истекла. Введите номер телефона ещё раз.",
        )

    if not client_names_match(profile, name):
        raise AuthError(
            "name_verification_failed",
            "Имя не совпадает с данными в студии. "
            f"Проверьте номер и попробуйте снова или запишитесь онлайн: {config.yclients_booking_url}",
        )

    client_name = _client_name(profile)
    try:
        storage.upsert_verified_user(vk_user_id, normalized_phone, client_name)
    except RuntimeError as error:
        raise AuthError("phone_already_linked", str(error)) from error

    _forget_phone_step(vk_user_id)
    return VerifyResult(
        phone=normalized_phone,
        phone_display=format_phone_display(normalized_phone),
        needs_password=True,
    )


def verify_password(
    vk_user_id: int,
    phone: str,
    raw_password: str,
    config: MiniAppConfig,
) -> VerifyResult:
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise AuthError("invalid_phone", "Некорректный номер телефона.")

    row = storage.fetch_row_by_phone(normalized_phone)
    password_hash = row.get("password_hash") if row else None
    if not password_hash:
        raise AuthError(
            "password_not_set",
            "Пароль ещё не задан. Войдите по имени, как в студии.",
        )

    if not passwords_match(raw_password, str(password_hash)):
        raise AuthError("password_verification_failed", "Неверный пароль.")

    storage.finish_password_login(vk_user_id, normalized_phone, row)

    return VerifyResult(
        phone=normalized_phone,
        phone_display=format_phone_display(normalized_phone),
        needs_password=False,
        client_name=row.get("client_name") or None,
    )


def set_password(
    vk_user_id: int,
    phone: str,
    raw_password: str,
    config: MiniAppConfig,
) -> VerifyResult:
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise AuthError("invalid_phone", "Некорректный номер телефона.")

    password_error = validate_password(raw_password)
    if password_error:
        raise AuthError("invalid_password", password_error)

    try:
        storage.save_password(
            vk_user_id,
            normalized_phone,
            hash_password(raw_password),
        )
    except LookupError:
        raise AuthError(
            "identity_not_verified",
            "Сначала подтвердите имя по номеру телефона.",
        ) from None

    return VerifyResult(
        phone=normalized_phone,
        phone_display=format_phone_display(normalized_phone),
        needs_password=False,
        client_name=storage.get_user_entry(vk_user_id).get("client_name"),
    )


def logout(vk_user_id: int) -> None:
    from client_cache import invalidate_client_cache

    _forget_phone_step(vk_user_id)
    invalidate_client_cache(vk_user_id=vk_user_id)
    storage.clear_session(vk_user_id)
