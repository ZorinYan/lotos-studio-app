"""Сопоставление телефона с сотрудником YClients."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import requests

from miniapp_config import MiniAppConfig
from staff_storage import fetch_by_phone, upsert_profile
from utils.phone import normalize_phone
from yclients_adapter import (
    YClientsError,
    YClientsNetworkError,
    YClientsPermissionError,
    create_yclients_client,
)

_CACHE_TTL_SEC = 10 * 60
_cache_lock = threading.Lock()
_users_cache: tuple[float, list[dict]] | None = None
_staff_cache: tuple[float, list[dict]] | None = None


@dataclass(frozen=True)
class StaffProfile:
    phone: str
    yclients_staff_id: int
    staff_name: str
    yclients_user_id: int | None = None
    specialization: str | None = None
    position_title: str | None = None

    @classmethod
    def from_row(cls, row: dict) -> StaffProfile:
        return cls(
            phone=row["phone"],
            yclients_staff_id=int(row["yclients_staff_id"]),
            staff_name=row["staff_name"],
            yclients_user_id=row.get("yclients_user_id"),
            specialization=row.get("specialization"),
            position_title=row.get("position_title"),
        )

    @classmethod
    def from_yclients(
        cls,
        staff: dict,
        user: dict | None,
        phone: str,
    ) -> StaffProfile:
        position = staff.get("position") or {}
        position_title = position.get("title") if isinstance(position, dict) else None
        user_id = staff.get("user_id") or (user or {}).get("id")
        name = (staff.get("name") or (user or {}).get("name") or (user or {}).get("firstname") or "Сотрудник").strip()
        return cls(
            phone=phone,
            yclients_staff_id=int(staff["id"]),
            staff_name=name,
            yclients_user_id=int(user_id) if user_id else None,
            specialization=(staff.get("specialization") or None),
            position_title=position_title,
        )


class StaffResolverError(Exception):
    code: str

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def clear_staff_directory_cache() -> None:
    global _users_cache, _staff_cache
    with _cache_lock:
        _users_cache = None
        _staff_cache = None


def _get_cached_users(yclients) -> list[dict]:
    global _users_cache
    now = time.monotonic()
    with _cache_lock:
        if _users_cache and now - _users_cache[0] < _CACHE_TTL_SEC:
            return _users_cache[1]
    users = yclients.list_company_users()
    with _cache_lock:
        _users_cache = (now, users)
    return users


def _get_cached_staff(yclients) -> list[dict]:
    global _staff_cache
    now = time.monotonic()
    with _cache_lock:
        if _staff_cache and now - _staff_cache[0] < _CACHE_TTL_SEC:
            return _staff_cache[1]
    staff = yclients.list_staff()
    with _cache_lock:
        _staff_cache = (now, staff)
    return staff


def _user_phone(user: dict) -> str | None:
    for key in ("phone", "login"):
        value = user.get(key)
        if value:
            return normalize_phone(str(value))
    return None


def _is_active_staff(staff: dict) -> bool:
    return int(staff.get("fired") or 0) == 0


def resolve_staff_by_phone(phone: str, config: MiniAppConfig) -> StaffProfile | None:
    normalized = normalize_phone(phone)
    if not normalized:
        return None

    existing = fetch_by_phone(normalized)
    if existing:
        return StaffProfile.from_row(existing)

    yclients = create_yclients_client(config)
    try:
        users = _get_cached_users(yclients)
        staff_list = _get_cached_staff(yclients)
    except YClientsNetworkError:
        raise StaffResolverError(
            "yclients_timeout",
            "YClients не отвечает. Проверьте интернет и попробуйте снова.",
        ) from None
    except YClientsPermissionError:
        raise StaffResolverError(
            "service_unavailable",
            "Нет доступа к списку сотрудников в YClients. Обратитесь к администратору.",
        ) from None
    except YClientsError as error:
        raise StaffResolverError("fetch_error", str(error)) from error
    except requests.RequestException:
        raise StaffResolverError(
            "service_unavailable",
            "Не удалось связаться с YClients. Проверьте интернет и попробуйте снова.",
        ) from None

    staff_by_id = {
        int(item["id"]): item
        for item in staff_list
        if item.get("id") is not None and _is_active_staff(item)
    }
    users_by_id = {
        int(item["id"]): item for item in users if item.get("id") is not None
    }

    for user in users:
        user_phone = _user_phone(user)
        if user_phone != normalized:
            continue
        master_id = int((user.get("access") or {}).get("master_id") or 0)
        if master_id and master_id in staff_by_id:
            return StaffProfile.from_yclients(staff_by_id[master_id], user, normalized)

    for staff in staff_by_id.values():
        user_id = staff.get("user_id")
        if not user_id:
            continue
        user = users_by_id.get(int(user_id))
        if not user:
            continue
        user_phone = _user_phone(user)
        if user_phone == normalized:
            return StaffProfile.from_yclients(staff, user, normalized)

    return None


def ensure_staff_profile(profile: StaffProfile) -> None:
    upsert_profile(
        phone=profile.phone,
        yclients_staff_id=profile.yclients_staff_id,
        staff_name=profile.staff_name,
        yclients_user_id=profile.yclients_user_id,
        specialization=profile.specialization,
        position_title=profile.position_title,
    )
