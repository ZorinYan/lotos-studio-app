from collections import defaultdict
from datetime import datetime

from utils.text_style import format_class_block, join_lines, page_header, section
from yclients.client import YClientsClient

WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)
MAX_MESSAGE_LENGTH = 3900


def _format_day_header(dt: datetime) -> str:
    return f"{WEEKDAYS[dt.weekday()]}, {dt.day} {MONTHS[dt.month - 1]}"


def _format_activity_block(activity: dict, dt: datetime) -> str:
    service = activity.get("service", {})
    staff = activity.get("staff", {})
    title = service.get("title", "Занятие")
    trainer = staff.get("name") or staff.get("specialization") or "—"
    return format_class_block(
        dt.strftime("%H:%M"),
        title,
        trainer,
        capacity=activity.get("capacity") or 0,
        booked=activity.get("records_count") or 0,
    )


def _schedule_title(days: int, title: str | None) -> str:
    if title:
        return title
    return f"{days} дней"


def format_schedule(activities: list[dict], days: int, *, title: str | None = None) -> list[str]:
    period_label = _schedule_title(days, title)
    if not activities:
        return [
            f"{page_header('📅', f'Расписание · {period_label}')}\n\n"
            "В выбранном периоде занятий пока нет.\n"
            "Попробуйте другой период или напишите администратору студии."
        ]

    by_day: dict[str, list[tuple[datetime, dict]]] = defaultdict(list)
    for activity in activities:
        dt = YClientsClient._parse_activity_datetime(activity)
        if not dt:
            continue
        by_day[dt.date().isoformat()].append((dt, activity))

    header = f"{page_header('📅', f'Расписание · {period_label}')}\n"
    messages: list[str] = []
    current = header

    for day_key in sorted(by_day.keys()):
        day_items = sorted(by_day[day_key], key=lambda item: item[0])
        day_header = _format_day_header(day_items[0][0])
        class_blocks = [
            _format_activity_block(activity, dt) for dt, activity in day_items
        ]
        day_block = section("📆", day_header) + "\n\n" + join_lines(class_blocks) + "\n"

        if len(current) + len(day_block) > MAX_MESSAGE_LENGTH:
            messages.append(current.rstrip())
            current = f"{page_header('📅', 'Расписание · продолжение')}\n{day_block}"
        else:
            current += day_block

    if current.strip():
        messages.append(current.rstrip())

    return messages or [
        f"{page_header('📅', f'Расписание · {period_label}')}\n\n"
        "Не удалось сформировать расписание."
    ]
