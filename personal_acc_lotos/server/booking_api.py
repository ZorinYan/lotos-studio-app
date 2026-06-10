from datetime import date, timedelta

import requests

from _lib_path import ensure_lib_path
from miniapp_config import MiniAppConfig
from schedule_api import _serialize_activity
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from utils import storage  # noqa: E402
from utils.phone import format_phone_display  # noqa: E402
from yclients.client import YClientsClient  # noqa: E402

from rebook_api import remember_booking_from_activity

from auth_service import AuthError  # noqa: E402


def _resolve_fullname(vk_user_id: int, phone: str, yclients) -> tuple[str, str]:
    try:
        client = yclients.find_client_by_phone(phone)
        if client:
            name = str(client.get("name", "")).strip()
            surname = str(client.get("surname", "")).strip()
            if name:
                return name, surname
    except (YClientsError, YClientsPermissionError, requests.RequestException):
        pass

    stored = storage.get_user_entry(vk_user_id).get("client_name", "")
    parts = str(stored).strip().split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    if parts:
        return parts[0], ""
    return "Клиент", ""


def _find_activity(yclients, activity_id: int, activity_date: str | None) -> dict | None:
    if activity_date:
        try:
            target = date.fromisoformat(activity_date)
        except ValueError:
            target = None
        if target:
            for activity in yclients.get_activities_for_date(target):
                if activity.get("id") == activity_id:
                    return activity

    for offset in range(14):
        target = date.today() + timedelta(days=offset)
        for activity in yclients.get_activities_for_date(target):
            if activity.get("id") == activity_id:
                return activity
    return None


def book_schedule_class(
    vk_user_id: int,
    activity_id: int,
    activity_date: str | None,
    config: MiniAppConfig,
) -> dict:
    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    try:
        activity = _find_activity(yclients, activity_id, activity_date)
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

    if not activity:
        raise AuthError("activity_not_found", "Занятие не найдено или уже прошло.")

    if not YClientsClient.activity_has_free_spots(activity):
        raise AuthError("activity_full", "На это занятие больше нет свободных мест.")

    fullname, surname = _resolve_fullname(vk_user_id, phone, yclients)

    try:
        yclients.book_activity(
            activity_id,
            phone,
            fullname,
            surname,
            comment="Запись через мини-приложение Lotos",
        )
    except YClientsError as error:
        raise AuthError("booking_failed", str(error)) from error
    except requests.RequestException:
        raise AuthError(
            "service_unavailable",
            "Не удалось связаться с YClients. Проверьте интернет и попробуйте снова.",
        ) from None

    remember_booking_from_activity(vk_user_id, activity)
    serialized = _serialize_activity(activity)
    return {
        "success": True,
        "phoneDisplay": format_phone_display(phone),
        "class": serialized,
        "message": "Вы успешно записаны на занятие.",
    }
