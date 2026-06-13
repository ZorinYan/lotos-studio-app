"""Сериализация абонементов YClients для мини-приложения."""

import re

from _lib_path import ensure_lib_path

ensure_lib_path()

from yclients.abonement_utils import (
    _parse_balance_string_value,
    abonement_balance_count,
    abonement_expiry_date,
    is_active_abonement,
)
from yclients.formatters import status_icon
from yclients.formatters_cabinet import _service_titles, _staff_name
from utils.dates import format_date_short, format_datetime_short
from yclients.abonement_utils import format_abonement_expiry, format_abonement_freeze


def _clean_expiry(expiry: str | None) -> str | None:
    if not expiry:
        return None
    return (
        expiry.replace("📅  Действует до:  ", "")
        .replace("📅  ", "")
        .strip()
        or None
    )


def _format_ts(raw) -> str | None:
    if not raw:
        return None
    text = str(raw)
    if text.isdigit():
        from datetime import datetime

        try:
            return format_date_short(datetime.fromtimestamp(int(text)).isoformat())
        except (ValueError, OSError):
            pass
    return format_date_short(text)


def _link_title(link: dict) -> str | None:
    service = link.get("service")
    if isinstance(service, dict) and service.get("title"):
        return str(service["title"]).strip()

    category = link.get("category")
    if isinstance(category, dict) and category.get("title"):
        return str(category["title"]).strip()

    return None


def extract_balance_services(item: dict) -> list[dict]:
    services: list[dict] = []
    container = item.get("balance_container") or {}
    links = container.get("links") or []

    parsed_total = _parse_balance_string_value(item.get("balance_string"))
    link_count = sum(1 for link in links if isinstance(link, dict))

    for link in links:
        if not isinstance(link, dict):
            continue
        title = _link_title(link)
        if title is None:
            continue
        count = link.get("count")
        remaining: int | None = None
        if count is not None:
            try:
                remaining = int(count)
            except (TypeError, ValueError):
                remaining = None
        elif (
            parsed_total is not None
            and parsed_total > 0
            and link_count == 1
            and is_active_abonement(item)
        ):
            # balance_string — только если у единственной услуги нет count в link
            remaining = parsed_total
        if remaining is None:
            continue
        services.append({"title": title, "remaining": remaining})

    if services:
        return services

    if item.get("is_united_balance"):
        remaining = abonement_balance_count(item)
        if remaining is not None:
            label = "Общий баланс"
            if item.get("united_balance_services_count"):
                label = "Любые услуги абонемента"
            return [{"title": label, "remaining": remaining}]

    remaining = abonement_balance_count(item)
    if remaining is not None:
        title = item.get("type", {}).get("title", "Абонемент")
        return [{"title": str(title), "remaining": remaining}]

    return []


def total_remaining(services: list[dict], item: dict) -> int | None:
    fallback = abonement_balance_count(item)
    if not services:
        return fallback
    total = sum(service["remaining"] for service in services)
    if total > 0:
        return total
    return fallback


def abonement_balance_total(item: dict) -> int | None:
    raw = item.get("united_balance_services_count")
    if raw is not None:
        try:
            total = int(raw)
            if total > 0:
                return total
        except (TypeError, ValueError):
            pass

    abonement_type = item.get("type") or {}
    for key in ("count", "visits_count", "amount"):
        raw = abonement_type.get(key)
        if raw is None:
            continue
        try:
            total = int(raw)
            if total > 0:
                return total
        except (TypeError, ValueError):
            continue
    return None


def serialize_usage_visit(visit: dict) -> dict:
    date_iso = None
    dt_raw = visit.get("datetime") or visit.get("date", "")
    if dt_raw:
        from yclients.client import YClientsClient

        dt = YClientsClient._parse_record_datetime({"datetime": dt_raw, "date": dt_raw})
        if dt:
            date_iso = dt.date().isoformat()

    return {
        "datetime": format_datetime_short(dt_raw),
        "dateIso": date_iso,
        "service": _service_titles(visit),
        "staff": _staff_name(visit),
    }


def pick_primary_abonement(abonements: list[dict]) -> dict | None:
    """Первый активный абонемент с ненулевым остатком (как в интерфейсе YClients)."""
    if not abonements:
        return None

    inactive_markers = ("просроч", "законч", "архив", "исчерп", "замороз")

    for item in abonements:
        if item.get("isFrozen"):
            continue
        status = str(item.get("status", "")).lower()
        if any(marker in status for marker in inactive_markers):
            continue
        remaining = item.get("balanceRemaining")
        if remaining is not None and remaining > 0:
            return item

    for item in abonements:
        if not item.get("isFrozen"):
            return item

    return abonements[0]


def serialize_abonement(item: dict) -> dict:
    status = item.get("status", {})
    status_title = status.get("extended_title") or status.get("title", "—")
    expiry = format_abonement_expiry(item)
    services = extract_balance_services(item)
    abonement_type = item.get("type") or {}
    expiry_dt = abonement_expiry_date(item)

    return {
        "id": item.get("id"),
        "title": abonement_type.get("title", "Абонемент"),
        "balanceRemaining": total_remaining(services, item),
        "balanceTotal": abonement_balance_total(item),
        "services": services,
        "isUnitedBalance": bool(item.get("is_united_balance")),
        "status": status_title,
        "statusIcon": status_icon(status_title),
        "number": str(item.get("number", "—")),
        "expiry": _clean_expiry(expiry),
        "expiryDate": expiry_dt.isoformat() if expiry_dt else None,
        "activatedDate": _format_ts(item.get("activated_date")),
        "createdDate": _format_ts(item.get("created_date")),
        "isFrozen": bool(item.get("is_frozen")),
        "allowFreeze": bool(abonement_type.get("allow_freeze")),
        "freezeLimit": abonement_type.get("freeze_limit"),
        "typeCost": abonement_type.get("cost"),
        "freezeLines": [
            line.replace("❄️  ", "") for line in format_abonement_freeze(item)
        ],
    }
