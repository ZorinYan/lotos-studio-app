"""Кэш данных клиента (главная, кабинет) — TTL 10 мин."""

from __future__ import annotations

import threading
import time
from typing import Any

from _lib_path import ensure_lib_path

ensure_lib_path()

from services.cabinet import CabinetData, CabinetService  # noqa: E402
from yclients.client import YClientsClient  # noqa: E402

CLIENT_CACHE_TTL_SEC = 600

_lock = threading.Lock()
_cabinet_raw: dict[str, tuple[float, CabinetData]] = {}
_usage_visits: dict[str, tuple[float, list[dict]]] = {}
_home_response: dict[int, tuple[float, dict[str, Any]]] = {}
_cabinet_response: dict[int, tuple[float, dict[str, Any]]] = {}
_rebook_preview: dict[int, tuple[float, dict[str, Any]]] = {}


def _phone_key(company_id: int, phone: str) -> str:
    return f"{company_id}:{phone}"


def _is_fresh(expires_at: float) -> bool:
    return expires_at > time.monotonic()


def fetch_cabinet_data(yclients: YClientsClient, phone: str) -> CabinetData:
    company_id = yclients.config.yclients_company_id
    key = _phone_key(company_id, phone)

    with _lock:
        entry = _cabinet_raw.get(key)
        if entry and _is_fresh(entry[0]):
            return entry[1]

    data = CabinetService(yclients).load(phone)

    with _lock:
        _cabinet_raw[key] = (time.monotonic() + CLIENT_CACHE_TTL_SEC, data)
    return data


def fetch_abonement_usage_visits(
    yclients: YClientsClient,
    phone: str,
    *,
    limit: int = 5,
) -> list[dict]:
    company_id = yclients.config.yclients_company_id
    key = _phone_key(company_id, phone)

    with _lock:
        entry = _usage_visits.get(key)
        if entry and _is_fresh(entry[0]):
            return entry[1]

    try:
        visits = yclients.get_abonement_usage_visits(phone, limit=limit)
    except Exception:
        visits = []

    with _lock:
        _usage_visits[key] = (time.monotonic() + CLIENT_CACHE_TTL_SEC, visits)
    return visits


def get_cached_home(vk_user_id: int) -> dict[str, Any] | None:
    with _lock:
        entry = _home_response.get(vk_user_id)
        if entry and _is_fresh(entry[0]):
            return entry[1]
    return None


def set_cached_home(vk_user_id: int, payload: dict[str, Any]) -> None:
    with _lock:
        _home_response[vk_user_id] = (time.monotonic() + CLIENT_CACHE_TTL_SEC, payload)


def get_cached_cabinet(vk_user_id: int) -> dict[str, Any] | None:
    with _lock:
        entry = _cabinet_response.get(vk_user_id)
        if entry and _is_fresh(entry[0]):
            return entry[1]
    return None


def set_cached_cabinet(vk_user_id: int, payload: dict[str, Any]) -> None:
    with _lock:
        _cabinet_response[vk_user_id] = (
            time.monotonic() + CLIENT_CACHE_TTL_SEC,
            payload,
        )


def get_cached_rebook_preview(vk_user_id: int) -> dict[str, Any] | None:
    with _lock:
        entry = _rebook_preview.get(vk_user_id)
        if entry and _is_fresh(entry[0]):
            return entry[1]
    return None


def set_cached_rebook_preview(vk_user_id: int, payload: dict[str, Any]) -> None:
    with _lock:
        _rebook_preview[vk_user_id] = (
            time.monotonic() + CLIENT_CACHE_TTL_SEC,
            payload,
        )


def invalidate_client_cache(
    *,
    vk_user_id: int | None = None,
    phone: str | None = None,
    company_id: int | None = None,
) -> None:
    with _lock:
        if vk_user_id is not None:
            _home_response.pop(vk_user_id, None)
            _cabinet_response.pop(vk_user_id, None)
            _rebook_preview.pop(vk_user_id, None)

        if phone and company_id:
            key = _phone_key(company_id, phone)
            _cabinet_raw.pop(key, None)
            _usage_visits.pop(key, None)
