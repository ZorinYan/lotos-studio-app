import requests

from _lib_path import ensure_lib_path
from booking_api import book_schedule_class
from miniapp_config import MiniAppConfig
from record_serializer import serialize_record
from rebook_api import _bookable_activities
from schedule_api import _serialize_activity
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from utils import storage  # noqa: E402
from utils.dates import studio_now  # noqa: E402
from yclients.client import YClientsClient  # noqa: E402

from auth_service import AuthError  # noqa: E402
from records_api import cancel_record  # noqa: E402


def _record_booking_prefs(record: dict) -> dict | None:
    staff_id = record.get("staffId")
    services = record.get("services") or []
    if not staff_id:
        return None
    service = services[0] if services else {}
    return {
        "staff_id": int(staff_id),
        "staff_name": record.get("staff") or "Тренер",
        "service_title": record.get("service") or service.get("title") or "Занятие",
        "service_id": service.get("id"),
    }


def _exclude_current_slot(classes: list[dict], record: dict) -> list[dict]:
    current_date = record.get("date")
    current_time = record.get("time")
    filtered = []
    for item in classes:
        if current_date and item.get("date") == current_date and item.get("time") == current_time:
            continue
        filtered.append(item)
    return filtered


def load_reschedule_slots(
    vk_user_id: int,
    record_id: int,
    config: MiniAppConfig,
    *,
    limit: int = 5,
) -> dict:
    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    now = studio_now()

    try:
        from client_cache import fetch_cabinet_data

        cabinet = fetch_cabinet_data(yclients, phone, use_cache=False)
        raw_records = yclients.get_client_records(cabinet.profile["id"])
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
    except ValueError:
        raise AuthError(
            "client_not_found",
            "По этому номеру нет карточки в студии.",
        ) from None

    raw_record = next((item for item in raw_records if item.get("id") == record_id), None)
    if not raw_record:
        raise AuthError("record_not_found", "Запись не найдена.")

    record = serialize_record(raw_record, now=now)
    if not record["canCancel"]:
        raise AuthError(
            "record_not_reschedulable",
            "Эту запись нельзя перенести — занятие уже прошло или отменено.",
        )

    prefs = _record_booking_prefs(record)
    if not prefs:
        raise AuthError(
            "reschedule_unavailable",
            "Не удалось определить занятие для переноса.",
        )

    try:
        activities = _bookable_activities(yclients, use_cache=False)
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

    classes = _exclude_current_slot(classes, record)[:limit]
    if not classes:
        raise AuthError(
            "reschedule_no_slots",
            f"Сейчас нет свободных слотов у {prefs['staff_name']} на «{prefs['service_title']}».",
        )

    return {
        "record": record,
        "prefs": {
            "staffId": prefs["staff_id"],
            "staffName": prefs["staff_name"],
            "serviceTitle": prefs["service_title"],
            "serviceId": prefs.get("service_id"),
        },
        "classes": classes,
    }


def reschedule_record(
    vk_user_id: int,
    record_id: int,
    activity_id: int,
    activity_date: str | None,
    config: MiniAppConfig,
) -> dict:
    slots = load_reschedule_slots(vk_user_id, record_id, config, limit=1)
    record = slots["record"]

    booking = book_schedule_class(
        vk_user_id,
        activity_id,
        activity_date,
        config,
    )

    try:
        cancel_record(vk_user_id, record_id, config)
    except AuthError as error:
        return {
            "success": True,
            "partial": True,
            "message": (
                "Новая запись создана, но старая не отменилась автоматически. "
                "Отмените её вручную или напишите в студию."
            ),
            "warning": str(error),
            "oldRecord": record,
            "newClass": booking["class"],
        }

    return {
        "success": True,
        "partial": False,
        "message": "Запись перенесена.",
        "oldRecord": record,
        "newClass": booking["class"],
    }
