"""Авторизация сотрудников студии."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Literal

from auth_password import hash_password, passwords_match, validate_password
from miniapp_config import MiniAppConfig
from staff_resolver import StaffProfile, StaffResolverError, ensure_staff_profile, resolve_staff_by_phone
from staff_storage import clear_session as clear_staff_session
from staff_storage import fetch_by_phone, fetch_by_vk_user_id, finish_password_login, has_password, save_password
from utils.phone import format_phone_display, normalize_phone

_PENDING_TTL_SEC = 600
_pending: dict[int, tuple[str, StaffProfile, float]] = {}
_pending_lock = threading.Lock()


def clear_pending_staff_auth() -> None:
    with _pending_lock:
        _pending.clear()


@dataclass(frozen=True)
class StaffAuthStatus:
    authenticated: bool
    role: Literal["staff"] = "staff"
    phone: str | None = None
    phone_display: str | None = None
    staff_name: str | None = None
    staff_id: int | None = None
    specialization: str | None = None
    position_title: str | None = None


@dataclass(frozen=True)
class StaffPhoneCheckResult:
    step: Literal["password", "setPassword"]
    phone: str
    phone_display: str
    staff_name: str
    specialization: str | None = None
    position_title: str | None = None


@dataclass(frozen=True)
class StaffVerifyResult:
    phone: str
    phone_display: str
    staff_name: str
    staff_id: int
    specialization: str | None = None
    position_title: str | None = None


class StaffAuthError(Exception):
    code: str

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def remember_staff_phone_step(vk_user_id: int, phone: str, profile: StaffProfile) -> None:
    _remember_phone_step(vk_user_id, phone, profile)


def _remember_phone_step(vk_user_id: int, phone: str, profile: StaffProfile) -> None:
    with _pending_lock:
        _pending[vk_user_id] = (phone, profile, time.monotonic())


def _take_phone_step(vk_user_id: int, phone: str) -> StaffProfile | None:
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


def get_staff_auth_status(vk_user_id: int) -> StaffAuthStatus:
    row = fetch_by_vk_user_id(vk_user_id)
    if not row or not row.get("password_hash"):
        return StaffAuthStatus(authenticated=False)

    phone = row["phone"]
    return StaffAuthStatus(
        authenticated=True,
        phone=phone,
        phone_display=format_phone_display(phone),
        staff_name=row.get("staff_name"),
        staff_id=row.get("yclients_staff_id"),
        specialization=row.get("specialization"),
        position_title=row.get("position_title"),
    )


def check_staff_phone(vk_user_id: int, raw_phone: str, config: MiniAppConfig) -> StaffPhoneCheckResult:
    phone = normalize_phone(raw_phone)
    if not phone:
        raise StaffAuthError(
            "invalid_phone",
            "Не удалось распознать номер. Попробуйте, например: 89991234567",
        )

    try:
        profile = resolve_staff_by_phone(phone, config)
    except StaffResolverError as error:
        raise StaffAuthError(error.code, str(error)) from error

    if not profile:
        raise StaffAuthError(
            "staff_not_found",
            "Этот номер не найден среди сотрудников студии.",
        )

    ensure_staff_profile(profile)
    _remember_phone_step(vk_user_id, phone, profile)

    if has_password(phone):
        return StaffPhoneCheckResult(
            step="password",
            phone=phone,
            phone_display=format_phone_display(phone),
            staff_name=profile.staff_name,
            specialization=profile.specialization,
            position_title=profile.position_title,
        )

    return StaffPhoneCheckResult(
        step="setPassword",
        phone=phone,
        phone_display=format_phone_display(phone),
        staff_name=profile.staff_name,
        specialization=profile.specialization,
        position_title=profile.position_title,
    )


def verify_staff_password(
    vk_user_id: int,
    phone: str,
    raw_password: str,
    config: MiniAppConfig,
) -> StaffVerifyResult:
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise StaffAuthError("invalid_phone", "Некорректный номер телефона.")

    row = fetch_by_phone(normalized_phone)
    password_hash = row.get("password_hash") if row else None
    if not password_hash:
        raise StaffAuthError(
            "password_not_set",
            "Пароль ещё не задан. Войдите по номеру и задайте пароль.",
        )

    if not passwords_match(raw_password, str(password_hash)):
        raise StaffAuthError("password_verification_failed", "Неверный пароль.")

    finish_password_login(vk_user_id, normalized_phone, row)
    _forget_phone_step(vk_user_id)

    return StaffVerifyResult(
        phone=normalized_phone,
        phone_display=format_phone_display(normalized_phone),
        staff_name=row.get("staff_name") or "Сотрудник",
        staff_id=int(row["yclients_staff_id"]),
        specialization=row.get("specialization"),
        position_title=row.get("position_title"),
    )


def set_staff_password(
    vk_user_id: int,
    phone: str,
    raw_password: str,
    config: MiniAppConfig,
) -> StaffVerifyResult:
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise StaffAuthError("invalid_phone", "Некорректный номер телефона.")

    password_error = validate_password(raw_password)
    if password_error:
        raise StaffAuthError("invalid_password", password_error)

    profile = _take_phone_step(vk_user_id, normalized_phone)
    if profile is None:
        raise StaffAuthError(
            "session_expired",
            "Сессия входа истекла. Введите номер телефона ещё раз.",
        )

    ensure_staff_profile(profile)
    try:
        save_password(vk_user_id, normalized_phone, hash_password(raw_password))
    except LookupError:
        raise StaffAuthError(
            "staff_not_found",
            "Не удалось сохранить пароль сотрудника.",
        ) from None

    _forget_phone_step(vk_user_id)

    return StaffVerifyResult(
        phone=normalized_phone,
        phone_display=format_phone_display(normalized_phone),
        staff_name=profile.staff_name,
        staff_id=profile.yclients_staff_id,
        specialization=profile.specialization,
        position_title=profile.position_title,
    )


def logout_staff(vk_user_id: int) -> None:
    _forget_phone_step(vk_user_id)
    clear_staff_session(vk_user_id)
