import sys
from pathlib import Path

import requests

from miniapp_config import MiniAppConfig
from schedule_api import _serialize_activity
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

BOT_ROOT = Path(__file__).resolve().parent.parent.parent / "lotos_vk_bot"
if str(BOT_ROOT) not in sys.path:
    sys.path.insert(0, str(BOT_ROOT))

from utils import storage, user_prefs  # noqa: E402
from yclients.client import YClientsClient  # noqa: E402

from auth_service import AuthError  # noqa: E402


def _infer_last_booking_from_visits(vk_user_id: int, phone: str, yclients) -> dict | None:
    try:
        visits = yclients.get_recent_visits(phone, limit=8)
    except (YClientsError, YClientsPermissionError, requests.RequestException):
        return None

    for visit in visits:
        staff = visit.get("staff", {})
        staff_id = staff.get("id")
        services = visit.get("services") or []
        if not staff_id or not services:
            continue
        service = services[0]
        prefs = {
            "staff_id": int(staff_id),
            "staff_name": (staff.get("name") or staff.get("specialization") or "Тренер").strip(),
            "service_title": str(service.get("title") or "Занятие"),
            "service_id": service.get("id"),
        }
        user_prefs.set_last_booking(vk_user_id, **prefs)
        return prefs
    return None


def _resolve_booking_prefs(vk_user_id: int, phone: str, yclients) -> dict | None:
    prefs = user_prefs.get_last_booking(vk_user_id)
    if prefs:
        return prefs
    return _infer_last_booking_from_visits(vk_user_id, phone, yclients)


def _serialize_prefs(prefs: dict) -> dict:
    return {
        "staffId": prefs["staff_id"],
        "staffName": prefs["staff_name"],
        "serviceTitle": prefs["service_title"],
        "serviceId": prefs.get("service_id"),
    }


def _matched_classes(vk_user_id: int, config: MiniAppConfig) -> tuple[dict, list[dict]]:
    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    prefs = _resolve_booking_prefs(vk_user_id, phone, yclients)
    if not prefs:
        raise AuthError(
            "rebook_unavailable",
            "Не нашли прошлую запись. Сначала посетите занятие или запишитесь через расписание.",
        )

    try:
        activities = yclients.get_bookable_activities(14)
        matched = yclients.filter_activities_like_booking(
            activities,
            staff_id=prefs["staff_id"],
            service_title=prefs["service_title"],
            service_id=prefs.get("service_id"),
        )
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

    classes = []
    for activity in matched:
        item = _serialize_activity(activity)
        if item:
            classes.append(item)

    if not classes:
        raise AuthError(
            "rebook_no_slots",
            f"Сейчас нет свободных мест у {prefs['staff_name']} на «{prefs['service_title']}».",
        )

    return _serialize_prefs(prefs), classes


def rebook_preview(vk_user_id: int, config: MiniAppConfig) -> dict:
    phone = storage.get_phone(vk_user_id)
    if not phone:
        return {"available": False}

    yclients = create_yclients_client(config)
    prefs = _resolve_booking_prefs(vk_user_id, phone, yclients)
    if not prefs:
        return {"available": False}

    try:
        activities = yclients.get_bookable_activities(14)
        matched = yclients.filter_activities_like_booking(
            activities,
            staff_id=prefs["staff_id"],
            service_title=prefs["service_title"],
            service_id=prefs.get("service_id"),
        )
    except Exception:
        return {"available": False, "prefs": _serialize_prefs(prefs)}

    return {
        "available": len(matched) > 0,
        "slotsCount": len(matched),
        "prefs": _serialize_prefs(prefs),
    }


def load_rebook_slots(vk_user_id: int, config: MiniAppConfig) -> dict:
    prefs, classes = _matched_classes(vk_user_id, config)
    return {
        "prefs": prefs,
        "classes": classes,
    }


def remember_booking_from_activity(vk_user_id: int, activity: dict) -> None:
    staff = activity.get("staff") or {}
    staff_id = YClientsClient.activity_staff_id(activity)
    if not staff_id:
        return
    service = activity.get("service") or {}
    user_prefs.set_last_booking(
        vk_user_id,
        staff_id=staff_id,
        staff_name=(staff.get("name") or staff.get("specialization") or "Тренер").strip(),
        service_title=str(service.get("title") or "Занятие"),
        service_id=service.get("id"),
    )
