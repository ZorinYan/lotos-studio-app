import re
import sys
from datetime import datetime
from pathlib import Path

BOT_ROOT = Path(__file__).resolve().parent.parent.parent / "lotos_vk_bot"
if str(BOT_ROOT) not in sys.path:
    sys.path.insert(0, str(BOT_ROOT))

from calendar_utils import event_window
from utils.dates import format_date_short, format_datetime_short  # noqa: E402
from yclients.client import YClientsClient  # noqa: E402

ATTENDANCE_LABELS = {
    0: "⏳  Ожидаем",
    1: "✅  Пришёл",
    2: "📌  Подтвердил",
    -1: "❌  Не пришёл",
}


def service_titles(record: dict) -> str:
    services = record.get("services", [])
    if not services:
        return "Занятие"
    return ", ".join(item.get("title", "Услуга") for item in services)


def staff_name(record: dict) -> str:
    staff = record.get("staff", {})
    return staff.get("name") or staff.get("specialization") or "—"


def attendance_label(attendance: int) -> str:
    raw = ATTENDANCE_LABELS.get(attendance, "Запись")
    return re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", "", raw).strip() or "Запись"


def _duration_minutes(record: dict) -> int | None:
    services = record.get("services") or []
    first_service = services[0] if services else {}
    for raw in (
        record.get("seance_length"),
        record.get("length"),
        first_service.get("seance_length"),
        first_service.get("duration"),
        first_service.get("length"),
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


def is_upcoming(record: dict, now: datetime | None = None) -> bool:
    if record.get("attendance") == -1:
        return False
    dt = YClientsClient._parse_record_datetime(record)
    if not dt:
        return False
    current = now or datetime.now()
    return dt >= current


def serialize_record(record: dict, *, now: datetime | None = None) -> dict:
    dt = YClientsClient._parse_record_datetime(record)
    attendance = int(record.get("attendance", 0))
    services = record.get("services") or []
    staff = record.get("staff") or {}
    upcoming = is_upcoming(record, now)
    duration_minutes = _duration_minutes(record)
    calendar = event_window(dt, duration_minutes) if dt else {"startsAt": None, "endsAt": None}

    return {
        "id": record.get("id"),
        "datetime": format_datetime_short(record.get("datetime") or record.get("date", "")),
        "date": dt.date().isoformat() if dt else None,
        "time": dt.strftime("%H:%M") if dt else None,
        "dateLabel": format_date_short(dt.isoformat()) if dt else None,
        "service": service_titles(record),
        "services": [
            {
                "id": item.get("id"),
                "title": item.get("title") or "Услуга",
            }
            for item in services
        ],
        "staff": staff_name(record),
        "staffId": staff.get("id"),
        "attendance": attendance_label(attendance),
        "attendanceCode": attendance,
        "durationMinutes": duration_minutes,
        "startsAt": calendar["startsAt"],
        "endsAt": calendar["endsAt"],
        "comment": (record.get("comment") or "").strip() or None,
        "activityId": record.get("activity_id"),
        "isUpcoming": upcoming,
        "canCancel": upcoming,
    }
