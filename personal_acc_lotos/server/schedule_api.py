from datetime import date, timedelta

import requests

from _lib_path import ensure_lib_path
from calendar_utils import event_window
from miniapp_config import MiniAppConfig
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from utils.dates import format_date_short  # noqa: E402
from yclients.client import YClientsClient  # noqa: E402

from auth_service import AuthError  # noqa: E402

WEEKDAYS_SHORT = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


def _day_chip_label(target: date, today: date) -> str:
    if target == today:
        return "Сегодня"
    if target == today + timedelta(days=1):
        return "Завтра"
    return f"{WEEKDAYS_SHORT[target.weekday()]}, {target.day}"


def build_day_options(days_ahead: int = 14) -> list[dict]:
    today = date.today()
    return [
        {
            "date": (today + timedelta(days=offset)).isoformat(),
            "label": _day_chip_label(today + timedelta(days=offset), today),
            "isToday": offset == 0,
        }
        for offset in range(days_ahead)
    ]


def _duration_minutes(activity: dict) -> int | None:
    """YClients хранит длительность в секундах (length, duration, seance_length)."""
    service = activity.get("service") or {}
    for raw in (
        activity.get("length"),
        activity.get("duration"),
        service.get("seance_length"),
        service.get("duration"),
        service.get("length"),
    ):
        if raw is None:
            continue
        try:
            seconds = int(raw)
        except (TypeError, ValueError):
            continue
        if seconds <= 0:
            continue
        minutes = round(seconds / 60)
        if minutes > 0:
            return minutes
    return None


def _serialize_activity(activity: dict) -> dict | None:
    dt = YClientsClient._parse_activity_datetime(activity)
    if not dt:
        return None

    capacity = int(activity.get("capacity") or 0)
    booked = int(activity.get("records_count") or 0)
    free_spots = max(capacity - booked, 0) if capacity > 0 else None
    is_full = capacity > 0 and booked >= capacity

    service = activity.get("service") or {}
    staff = activity.get("staff") or {}
    trainer = staff.get("name") or staff.get("specialization") or "—"
    duration_minutes = _duration_minutes(activity)
    calendar = event_window(dt, duration_minutes)

    return {
        "id": activity.get("id"),
        "time": dt.strftime("%H:%M"),
        "date": dt.date().isoformat(),
        "dateLabel": format_date_short(dt.isoformat()),
        "serviceTitle": service.get("title") or "Занятие",
        "serviceId": service.get("id"),
        "trainer": trainer,
        "staffId": staff.get("id"),
        "capacity": capacity,
        "booked": booked,
        "freeSpots": free_spots,
        "isFull": is_full,
        "durationMinutes": duration_minutes,
        "startsAt": calendar["startsAt"],
        "endsAt": calendar["endsAt"],
        "comment": (activity.get("comment") or "").strip() or None,
    }


def load_schedule(target_date: date, config: MiniAppConfig) -> dict:
    if target_date < date.today():
        raise AuthError("invalid_date", "Нельзя посмотреть расписание за прошедший день.")

    yclients = create_yclients_client(config)
    try:
        activities = yclients.get_activities_for_date(target_date)
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
    for activity in activities:
        item = _serialize_activity(activity)
        if item:
            classes.append(item)

    return {
        "date": target_date.isoformat(),
        "dateLabel": format_date_short(target_date.isoformat()),
        "dayLabel": _day_chip_label(target_date, date.today()),
        "classes": classes,
        "days": build_day_options(),
    }
