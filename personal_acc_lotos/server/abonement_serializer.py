"""Сериализация абонементов YClients для мини-приложения."""

import re

from _lib_path import ensure_lib_path

ensure_lib_path()

from yclients.abonement_utils import (
    _parse_balance_string_value,
    abonement_balance_count,
    abonement_expiry_date,
    is_active_abonement,
    is_issued_abonement,
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
            and (is_active_abonement(item) or is_issued_abonement(item))
        ):
            # balance_string — только если у единственной услуги нет count в link
            remaining = parsed_total
        if remaining is None:
            continue
        services.append({"title": title, "remaining": remaining})

    if services:
        return _sync_services_balance(services, item)

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


def _sync_services_balance(services: list[dict], item: dict) -> list[dict]:
    """Согласовать остаток: в links бывает count=0, а реальный остаток — в balance_string."""
    if not services:
        return services
    link_total = sum(service["remaining"] for service in services)
    if link_total > 0:
        return services

    actual = abonement_balance_count(item)
    if actual is None or actual <= 0:
        return services

    if len(services) == 1:
        return [{**services[0], "remaining": actual}]

    if item.get("is_united_balance"):
        label = "Общий баланс"
        if item.get("united_balance_services_count"):
            label = "Любые услуги абонемента"
        return [{"title": label, "remaining": actual}]

    title = str((item.get("type") or {}).get("title") or services[0]["title"])
    return [{"title": title, "remaining": actual}]


def total_remaining(services: list[dict], item: dict) -> int | None:
    if services:
        return sum(service["remaining"] for service in services)
    return abonement_balance_count(item)


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


def _status_text(item: dict) -> str:
    return str(item.get("status", "")).lower()


def _is_primary_inactive(item: dict) -> bool:
    if item.get("isFrozen"):
        return True
    inactive_markers = (
        "просроч",
        "законч",
        "архив",
        "исчерп",
        "использован",
        "неактив",
        "закрыт",
        "заверш",
        "замороз",
    )
    status = _status_text(item)
    return any(marker in status for marker in inactive_markers)


def _is_issued_status(item: dict) -> bool:
    status = _status_text(item)
    return any(marker in status for marker in ("выпущ", "issued", "created", "создан"))


def _is_active_status(item: dict) -> bool:
    status = _status_text(item)
    return "актив" in status or _is_issued_status(item)


def _primary_balance(item: dict) -> int | None:
    remaining = item.get("balanceRemaining")
    if remaining is not None and remaining > 0:
        return remaining
    if _is_issued_status(item):
        total = item.get("balanceTotal")
        if total is not None and total > 0:
            return total
    return remaining


def pick_primary_abonement(abonements: list[dict]) -> dict | None:
    """Абонемент для главной: активный или выпущенный, без просроченных."""
    if not abonements:
        return None

    candidates = [item for item in abonements if not _is_primary_inactive(item)]
    if not candidates:
        return abonements[0]

    for item in candidates:
        balance = _primary_balance(item)
        if balance is not None and balance > 0:
            return item

    for item in candidates:
        if _is_active_status(item):
            return item

    return candidates[0]


def serialize_abonement(item: dict) -> dict:
    status = item.get("status", {})
    status_title = status.get("extended_title") or status.get("title", "—")
    expiry = format_abonement_expiry(item)
    services = extract_balance_services(item)
    abonement_type = item.get("type") or {}
    expiry_dt = abonement_expiry_date(item)
    remaining = total_remaining(services, item)
    total = abonement_balance_total(item)
    if (remaining is None or remaining == 0) and is_issued_abonement(item):
        remaining = total

    return {
        "id": item.get("id"),
        "title": abonement_type.get("title", "Абонемент"),
        "balanceRemaining": remaining,
        "balanceTotal": total,
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
