"""Сериализация абонементов YClients для мини-приложения."""

import re

from _lib_path import ensure_lib_path

ensure_lib_path()

from yclients.abonement_utils import abonement_balance_count, abonement_expiry_date
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

    for link in links:
        title = _link_title(link)
        count = link.get("count")
        if title is None or count is None:
            continue
        try:
            remaining = int(count)
        except (TypeError, ValueError):
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
    if not services:
        return abonement_balance_count(item)
    if item.get("is_united_balance") and len(services) == 1:
        return services[0]["remaining"]
    return sum(service["remaining"] for service in services)


def serialize_usage_visit(visit: dict) -> dict:
    return {
        "datetime": format_datetime_short(visit.get("datetime") or visit.get("date", "")),
        "service": _service_titles(visit),
        "staff": _staff_name(visit),
    }


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
