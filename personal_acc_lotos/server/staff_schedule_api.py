from __future__ import annotations

from datetime import date
from typing import Any

import requests

from _lib_path import ensure_lib_path
from miniapp_config import MiniAppConfig
from record_serializer import is_upcoming
from staff_auth_service import StaffAuthError, get_staff_auth_status
from utils.dates import studio_now
from utils.phone import format_phone_display, normalize_phone
from yclients_adapter import (
    YClientsError,
    YClientsNetworkError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()


def _client_full_name(client: dict) -> str:
    name = (client.get("name") or client.get("firstname") or "").strip()
    surname = (client.get("surname") or client.get("lastname") or "").strip()
    if name and surname:
        return f"{name} {surname}"
    return name or surname or "Клиент"


def load_staff_activity_clients(
    vk_user_id: int,
    *,
    activity_id: int,
    activity_date: str,
    config: MiniAppConfig,
) -> dict[str, Any]:
    status = get_staff_auth_status(vk_user_id)
    if not status.authenticated or status.staff_id is None:
        raise StaffAuthError("not_authenticated", "Войдите как сотрудник.")

    staff_id = status.staff_id
    try:
        day = date.fromisoformat(activity_date)
    except ValueError as exc:
        raise StaffAuthError("invalid_date", "Некорректная дата занятия.") from exc

    yclients = create_yclients_client(config)
    try:
        day_records = yclients.get_records_for_staff(
            staff_id,
            start_date=day,
            end_date=day,
            count=250,
            page=1,
        )
    except YClientsPermissionError:
        raise StaffAuthError(
            "service_unavailable",
            "Нет доступа к записям сотрудников в YClients.",
        ) from None
    except YClientsNetworkError:
        raise StaffAuthError(
            "yclients_timeout",
            "YClients не отвечает. Проверьте интернет и попробуйте снова.",
        ) from None
    except YClientsError as error:
        raise StaffAuthError("fetch_error", str(error)) from None
    except requests.RequestException:
        raise StaffAuthError(
            "service_unavailable",
            "Не удалось связаться с YClients. Проверьте интернет и попробуйте снова.",
        ) from None

    activity_records = [
        r
        for r in day_records
        if int(r.get("activity_id") or 0) == activity_id and not r.get("deleted")
    ]

    by_client_id: dict[int, dict] = {}
    for r in activity_records:
        client = r.get("client") or {}
        cid = client.get("id") or r.get("client_id")
        if not cid:
            continue
        cid_i = int(cid)
        if cid_i not in by_client_id:
            by_client_id[cid_i] = r

    now = studio_now()
    visits_cache: dict[int, int] = {}

    clients_out: list[dict[str, Any]] = []
    for cid, record in by_client_id.items():
        if cid not in visits_cache:
            client_records = yclients.get_client_records(cid, days_back=365, count=200)
            count = 0
            for cr in client_records:
                if cr.get("deleted"):
                    continue
                if cr.get("attendance") == -1:
                    continue
                if is_upcoming(cr, now=now):
                    continue
                cr_staff = cr.get("staff") or {}
                if int(cr_staff.get("id") or 0) != staff_id:
                    continue
                count += 1
            visits_cache[cid] = count

        client = record.get("client") or {}
        raw_phone = str(client.get("phone") or "").strip()
        normalized_phone = normalize_phone(raw_phone) if raw_phone else None
        phone_display = (
            format_phone_display(normalized_phone) if normalized_phone else None
        )

        clients_out.append(
            {
                "clientId": cid,
                "fullName": _client_full_name(client),
                "phoneDisplay": phone_display,
                "visitsToTrainer": visits_cache.get(cid) or 0,
            }
        )

    clients_out.sort(key=lambda x: x["fullName"].lower())
    return {"clients": clients_out}

