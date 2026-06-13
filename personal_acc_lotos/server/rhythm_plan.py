from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from schedule_api import _serialize_activity
from rebook_api import _bookable_activities, _resolve_booking_prefs

WEEKDAY_SHORT = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
WEEKDAY_HABIT = [
    "понедельникам",
    "вторникам",
    "средам",
    "четвергам",
    "пятницам",
    "субботам",
    "воскресеньям",
]
WEEKDAY_NEXT = [
    "понедельник",
    "вторник",
    "среду",
    "четверг",
    "пятницу",
    "субботу",
    "воскресенье",
]

MONTH_GENITIVE = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    text = str(raw)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _collect_visit_dates(visit_history: list[dict], recent_visits: list[dict]) -> list[date]:
    dates: list[date] = []
    seen: set[str] = set()
    for item in visit_history:
        parsed = _parse_date(item.get("dateIso"))
        if not parsed:
            continue
        key = parsed.isoformat()
        if key in seen:
            continue
        seen.add(key)
        dates.append(parsed)
    for item in recent_visits:
        parsed = _parse_date(item.get("dateIso"))
        if not parsed:
            continue
        key = parsed.isoformat()
        if key in seen:
            continue
        seen.add(key)
        dates.append(parsed)
    return sorted(dates)


def _favorite_service_weekdays(visit_history: list[dict]) -> tuple[str | None, list[int]]:
    if not visit_history:
        return None, []

    service_counts: Counter[str] = Counter()
    service_weekdays: dict[str, Counter[int]] = {}

    for item in visit_history:
        service = (item.get("service") or "Занятие").strip()
        parsed = _parse_date(item.get("dateIso"))
        if not parsed:
            continue
        service_counts[service] += 1
        service_weekdays.setdefault(service, Counter())[parsed.weekday()] += 1

    if not service_counts:
        return None, []

    top_service = service_counts.most_common(1)[0][0]
    weekdays = [
        day
        for day, _count in service_weekdays.get(top_service, Counter()).most_common(3)
    ]
    return top_service, weekdays


def _format_weekday_pattern(weekdays: list[int]) -> str:
    if not weekdays:
        return ""
    return "/".join(WEEKDAY_SHORT[day] for day in sorted(weekdays))


def _format_next_date(value: date) -> str:
    return f"{value.day} {MONTH_GENITIVE[value.month - 1]}"


def _next_weekday_on_or_after(anchor: date, weekday: int) -> date:
    delta = (weekday - anchor.weekday()) % 7
    if delta == 0:
        return anchor
    return anchor + timedelta(days=delta)


def _count_slots_on_date(
    yclients,
    prefs: dict,
    target: date,
    *,
    use_cache: bool = True,
) -> tuple[int, str | None]:
    try:
        activities = _bookable_activities(yclients, use_cache=use_cache)
        matched = yclients.filter_activities_like_booking(
            activities,
            staff_id=prefs["staff_id"],
            service_title=prefs["service_title"],
            service_id=prefs.get("service_id"),
        )
    except Exception:
        return 0, None

    target_iso = target.isoformat()
    day_slots = []
    for activity in matched:
        item = _serialize_activity(activity)
        if not item or item.get("date") != target_iso:
            continue
        day_slots.append(item)

    if not day_slots:
        return 0, None

    return len(day_slots), _format_next_date(target)


def build_rhythm_plan(
    vk_user_id: int,
    phone: str,
    yclients,
    *,
    visit_history: list[dict] | None = None,
    recent_visits: list[dict] | None = None,
    use_cache: bool = True,
) -> dict | None:
    visit_history = visit_history or []
    recent_visits = recent_visits or []
    dates = _collect_visit_dates(visit_history, recent_visits)
    if len(dates) < 2:
        return None

    weekday_counts = Counter(item.weekday() for item in dates)
    top_weekday = weekday_counts.most_common(1)[0][0]

    prefs = _resolve_booking_prefs(
        vk_user_id,
        phone,
        yclients,
        recent_visits=recent_visits,
    )
    if not prefs:
        return {
            "message": f"Вы обычно ходите по {WEEKDAY_HABIT[top_weekday]}.",
            "detail": None,
            "slotsCount": 0,
            "nextDateLabel": None,
            "serviceTitle": None,
            "staffName": None,
            "weekdayPattern": _format_weekday_pattern([top_weekday]),
        }

    today = date.today()
    slots_count = 0
    next_label: str | None = None
    for offset in range(0, 21):
        candidate = today + timedelta(days=offset)
        if candidate.weekday() != top_weekday:
            continue
        count, label = _count_slots_on_date(
            yclients,
            prefs,
            candidate,
            use_cache=use_cache,
        )
        if count > 0:
            slots_count = count
            next_label = label
            break

    detail = None
    if slots_count > 0 and next_label:
        places = "место" if slots_count == 1 else "места" if slots_count < 5 else "мест"
        detail = (
            f"Ближайший {WEEKDAY_NEXT[top_weekday]}, {next_label} — "
            f"{slots_count} свободных {places}"
        )

    return {
        "message": f"Вы обычно ходите по {WEEKDAY_HABIT[top_weekday]}.",
        "detail": detail,
        "slotsCount": slots_count,
        "nextDateLabel": next_label,
        "serviceTitle": prefs["service_title"],
        "staffName": prefs["staff_name"],
        "weekdayPattern": _format_weekday_pattern([top_weekday]),
    }


def build_inactive_hint_detail(visit_history: list[dict]) -> str | None:
    service, weekdays = _favorite_service_weekdays(visit_history)
    if not service:
        return None
    pattern = _format_weekday_pattern(weekdays)
    if pattern:
        return f"Ваше любимое: {service} · {pattern}"
    return f"Ваше любимое: {service}"
