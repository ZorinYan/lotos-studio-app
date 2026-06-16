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
from dev_impersonation import clear_session as clear_dev_session
from dev_impersonation import get_session as get_dev_session
from dev_impersonation import is_developer, set_session as set_dev_session
from staff_auth_service import (
    clear_pending_staff_auth,
    get_staff_auth_status,
    logout_staff,
)
from staff_resolver import StaffProfile, StaffResolverError, ensure_staff_profile, resolve_staff_by_phone
from staff_storage import has_password as staff_has_password
from utils import storage  # noqa: E402

_PENDING_TTL_SEC = 600
_pending: dict[int, tuple[str, dict, float]] = {}
_pending_lock = threading.Lock()


def clear_pending_auth() -> None:
    with _pending_lock:
        _pending.clear()
    clear_pending_staff_auth()


@dataclass(frozen=True)
class AuthStatus:
    authenticated: bool
    role: Literal["client", "staff"] = "client"
    phone: str | None = None
    phone_display: str | None = None
    client_name: str | None = None
    staff_name: str | None = None
    staff_id: int | None = None
    specialization: str | None = None
    position_title: str | None = None


@dataclass(frozen=True)
class PhoneCheckResult:
    step: Literal["name", "password", "authenticated", "setPassword"]
    phone: str
    account_type: Literal["client", "staff"] = "client"
    requires_surname: bool = False
    phone_display: str | None = None
    client_name: str | None = None
    staff_name: str | None = None
    specialization: str | None = None
    position_title: str | None = None


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
    staff_status = get_staff_auth_status(vk_user_id)
    if staff_status.authenticated:
        return AuthStatus(
            authenticated=True,
            role="staff",
            phone=staff_status.phone,
            phone_display=staff_status.phone_display,
            staff_name=staff_status.staff_name,
            staff_id=staff_status.staff_id,
            specialization=staff_status.specialization,
            position_title=staff_status.position_title,
        )

    if is_developer(vk_user_id):
        session = get_dev_session(vk_user_id)
        if session:
            phone = session["phone"]
            return AuthStatus(
                authenticated=True,
                phone=phone,
                phone_display=format_phone_display(phone),
                client_name=session.get("client_name") or None,
            )
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
    staff_status = get_staff_auth_status(vk_user_id)
    if staff_status.authenticated:
        from staff_storage import fetch_by_vk_user_id
        from settings_api import normalize_color_scheme

        row = fetch_by_vk_user_id(vk_user_id) or {}
        prefs = {
            "colorScheme": normalize_color_scheme(row.get("color_scheme")),
            "welcomeBannerSeen": True,
        }
        return get_auth_status(vk_user_id), prefs

    row = storage.get_user_auth_state(vk_user_id)
    scheme = row.get("color_scheme") or "light"
    if scheme not in ("light", "dark"):
        scheme = "light"
    prefs = {
        "colorScheme": scheme,
        "welcomeBannerSeen": bool(row.get("welcome_banner_seen")),
    }
    return get_auth_status(vk_user_id), prefs


def _begin_staff_phone_login(
    vk_user_id: int,
    profile: StaffProfile,
) -> PhoneCheckResult:
    from staff_auth_service import remember_staff_phone_step

    ensure_staff_profile(profile)
    remember_staff_phone_step(vk_user_id, profile.phone, profile)
    step: Literal["password", "setPassword"] = (
        "password" if staff_has_password(profile.phone) else "setPassword"
    )
    return PhoneCheckResult(
        step=step,
        phone=profile.phone,
        account_type="staff",
        phone_display=format_phone_display(profile.phone),
        staff_name=profile.staff_name,
        specialization=profile.specialization,
        position_title=profile.position_title,
    )


def check_phone(vk_user_id: int, raw_phone: str, config: MiniAppConfig) -> PhoneCheckResult:
    phone = normalize_phone(raw_phone)
    if not phone:
        raise AuthError(
            "invalid_phone",
            "Не удалось распознать номер. Попробуйте, например: 89991234567",
        )

    if not is_developer(vk_user_id):
        try:
            staff_profile = resolve_staff_by_phone(phone, config)
        except StaffResolverError as error:
            raise AuthError(error.code, str(error)) from error

        if staff_profile:
            return _begin_staff_phone_login(vk_user_id, staff_profile)

    profile = _fetch_client_profile(phone, config)
    if not profile:
        raise AuthError(
            "client_not_found",
            "По этому номеру нет карточки в студии. "
            f"Если вы ещё не записывались — оформите первую запись онлайн: {config.yclients_booking_url}",
        )

    if is_developer(vk_user_id):
        client_name = _client_name(profile)
        set_dev_session(vk_user_id, phone, client_name)
        return PhoneCheckResult(
            step="authenticated",
            phone=phone,
            account_type="client",
            phone_display=format_phone_display(phone),
            client_name=client_name,
        )

    _remember_phone_step(vk_user_id, phone, profile)

    if storage.has_password_for_phone(phone):
        return PhoneCheckResult(step="password", phone=phone, requires_surname=False)

    return PhoneCheckResult(
        step="name",
        phone=phone,
        account_type="client",
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
    _forget_phone_step(vk_user_id)

    if is_developer(vk_user_id):
        set_dev_session(vk_user_id, normalized_phone, client_name)
        return VerifyResult(
            phone=normalized_phone,
            phone_display=format_phone_display(normalized_phone),
            needs_password=False,
            client_name=client_name,
        )

    try:
        storage.upsert_verified_user(vk_user_id, normalized_phone, client_name)
    except RuntimeError as error:
        raise AuthError("phone_already_linked", str(error)) from error

    return VerifyResult(
        phone=normalized_phone,
        phone_display=format_phone_display(normalized_phone),
        needs_password=True,
        client_name=client_name,
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
    logout_staff(vk_user_id)
    invalidate_client_cache(vk_user_id=vk_user_id)
    if is_developer(vk_user_id):
        clear_dev_session(vk_user_id)
        return
    storage.clear_session(vk_user_id)
