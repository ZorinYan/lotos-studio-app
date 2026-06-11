from dataclasses import dataclass
from typing import Literal

import requests

from _lib_path import ensure_lib_path
from auth_otp import send_login_code, verify_login_code
from miniapp_config import MiniAppConfig
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)  # create_yclients_client used in get_auth_status backfill

ensure_lib_path()

from yclients.formatters_cabinet import _client_name  # noqa: E402
from utils.client_name import client_has_surname, client_names_match  # noqa: E402
from utils.phone import format_phone_display, normalize_phone  # noqa: E402
from utils import storage  # noqa: E402


@dataclass(frozen=True)
class AuthStatus:
    authenticated: bool
    phone: str | None = None
    phone_display: str | None = None
    client_name: str | None = None


@dataclass(frozen=True)
class PhoneCheckResult:
    step: Literal["otp", "name"]
    phone: str
    requires_surname: bool
    otp_sent: bool = False


@dataclass(frozen=True)
class VerifyResult:
    phone: str
    phone_display: str


class AuthError(Exception):
    code: str

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def get_auth_status(vk_user_id: int, config: MiniAppConfig | None = None) -> AuthStatus:
    entry = storage.get_user_entry(vk_user_id)
    phone = entry.get("phone")
    if not phone:
        return AuthStatus(authenticated=False)

    client_name = entry.get("client_name")
    if not client_name and config:
        try:
            profile = create_yclients_client(config).find_client_by_phone(phone)
            if profile:
                client_name = _client_name(profile)
                storage.update_user_entry(vk_user_id, client_name=client_name)
        except (YClientsError, YClientsPermissionError, requests.RequestException):
            pass

    return AuthStatus(
        authenticated=True,
        phone=phone,
        phone_display=format_phone_display(phone),
        client_name=client_name or None,
    )


def _load_client_profile(raw_phone: str, config: MiniAppConfig) -> tuple[str, dict]:
    phone = normalize_phone(raw_phone)
    if not phone:
        raise AuthError("invalid_phone", "Не удалось распознать номер. Попробуйте, например: 89991234567")

    yclients = create_yclients_client(config)
    try:
        profile = yclients.find_client_by_phone(phone)
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

    if not profile:
        raise AuthError(
            "client_not_found",
            "По этому номеру нет карточки в студии. "
            f"Если вы ещё не записывались — оформите первую запись онлайн: {config.yclients_booking_url}",
        )

    return phone, profile


def check_phone(
    vk_user_id: int,
    raw_phone: str,
    config: MiniAppConfig,
    *,
    messages_allowed: bool = False,
) -> PhoneCheckResult:
    phone, profile = _load_client_profile(raw_phone, config)
    requires_surname = client_has_surname(profile)

    if messages_allowed:
        sent, _error = send_login_code(vk_user_id, phone, config)
        if sent:
            return PhoneCheckResult(
                step="otp",
                phone=phone,
                requires_surname=requires_surname,
                otp_sent=True,
            )

    return PhoneCheckResult(
        step="name",
        phone=phone,
        requires_surname=requires_surname,
        otp_sent=False,
    )


def resend_otp(vk_user_id: int, raw_phone: str, config: MiniAppConfig) -> PhoneCheckResult:
    phone, profile = _load_client_profile(raw_phone, config)
    sent, error = send_login_code(vk_user_id, phone, config)
    if not sent:
        raise AuthError(
            "otp_send_failed",
            error or "Не удалось отправить код. Войдите по имени и фамилии.",
        )
    return PhoneCheckResult(
        step="otp",
        phone=phone,
        requires_surname=client_has_surname(profile),
        otp_sent=True,
    )


def _complete_login(vk_user_id: int, phone: str, config: MiniAppConfig) -> VerifyResult:
    yclients = create_yclients_client(config)
    try:
        profile = yclients.find_client_by_phone(phone)
    except (YClientsPermissionError, YClientsError, requests.RequestException):
        profile = None

    client_name = _client_name(profile) if profile else None
    storage.update_user_entry(
        vk_user_id,
        phone=phone,
        client_name=client_name,
    )
    return VerifyResult(
        phone=phone,
        phone_display=format_phone_display(phone),
    )


def verify_otp(
    vk_user_id: int,
    phone: str,
    raw_code: str,
    config: MiniAppConfig,
) -> VerifyResult:
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise AuthError("invalid_phone", "Некорректный номер телефона.")

    ok, message = verify_login_code(vk_user_id, normalized_phone, raw_code)
    if not ok:
        raise AuthError("otp_verification_failed", message or "Неверный код.")

    return _complete_login(vk_user_id, normalized_phone, config)


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

    yclients = create_yclients_client(config)
    try:
        profile = yclients.find_client_by_phone(normalized_phone)
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

    if not profile or not client_names_match(profile, name):
        raise AuthError(
            "name_verification_failed",
            "Имя не совпадает с данными в студии. "
            f"Проверьте номер и попробуйте снова или запишитесь онлайн: {config.yclients_booking_url}",
        )

    return _complete_login(vk_user_id, normalized_phone, config)


def logout(vk_user_id: int) -> None:
    from client_cache import invalidate_client_cache

    invalidate_client_cache(vk_user_id=vk_user_id)
    storage.clear_phone(vk_user_id)
