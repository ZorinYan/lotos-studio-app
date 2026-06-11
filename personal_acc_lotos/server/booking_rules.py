"""Правила записи: пробное занятие или абонемент (как в YClients)."""

from datetime import date

import requests

from _lib_path import ensure_lib_path

ensure_lib_path()

from abonement_serializer import extract_balance_services  # noqa: E402
from yclients.abonement_utils import (  # noqa: E402
    abonement_balance_count,
    abonement_expiry_date,
    is_active_abonement,
)
from yclients_adapter import YClientsError, YClientsPermissionError  # noqa: E402

from auth_service import AuthError  # noqa: E402


def requires_abonement(activity: dict) -> bool:
    service = activity.get("service") or {}
    try:
        return int(service.get("abonement_restriction") or 0) == 1
    except (TypeError, ValueError):
        return False


def _service_titles_match(activity_title: str, abonement_service_title: str) -> bool:
    left = activity_title.lower().strip()
    right = abonement_service_title.lower().strip()
    if not left or not right:
        return False
    return left in right or right in left


def _link_service_id(link: dict) -> int | None:
    service = link.get("service")
    if isinstance(service, dict) and service.get("id") is not None:
        try:
            return int(service["id"])
        except (TypeError, ValueError):
            pass
    return None


def abonement_covers_activity(abonement: dict, activity: dict) -> bool:
    if abonement.get("is_frozen"):
        return False

    balance = abonement_balance_count(abonement)
    if balance is not None and balance <= 0:
        return False

    service = activity.get("service") or {}
    activity_title = str(service.get("title") or "").strip()
    activity_service_id = service.get("id")

    if abonement.get("is_united_balance"):
        remaining = abonement_balance_count(abonement)
        return remaining is not None and remaining > 0

    for link in (abonement.get("balance_container") or {}).get("links") or []:
        link_service_id = _link_service_id(link)
        if link_service_id is not None and activity_service_id is not None:
            try:
                if int(link_service_id) == int(activity_service_id):
                    count = link.get("count")
                    if count is not None and int(count) > 0:
                        return True
            except (TypeError, ValueError):
                pass

    for svc in extract_balance_services(abonement):
        if svc["remaining"] <= 0:
            continue
        if _service_titles_match(activity_title, svc["title"]):
            return True

    return False


def _is_usable_abonement(item: dict) -> bool:
    if not is_active_abonement(item):
        return False
    if item.get("is_frozen"):
        return False
    expiry = abonement_expiry_date(item)
    if expiry and expiry < date.today():
        return False
    balance = abonement_balance_count(item)
    return balance is None or balance > 0


def has_usable_abonement_for_activity(yclients, phone: str, activity: dict) -> bool:
    try:
        items = yclients.get_abonements_by_phone(phone)
    except (YClientsError, YClientsPermissionError, requests.RequestException):
        return False

    for item in items:
        if not _is_usable_abonement(item):
            continue
        if abonement_covers_activity(item, activity):
            return True
    return False


def assert_abonement_booking_allowed(yclients, phone: str, activity: dict) -> None:
    if not requires_abonement(activity):
        return
    if has_usable_abonement_for_activity(yclients, phone, activity):
        return
    raise AuthError(
        "abonement_required",
        "Запись на это занятие только по абонементу. Оформите или продлите абонемент в студии.",
    )
