"""Кэш расписания YClients (TTL 10 мин) — один запрос на 14 дней вместо множества."""

from __future__ import annotations

import threading
import time
from datetime import date, datetime, timedelta

from _lib_path import ensure_lib_path

ensure_lib_path()

from yclients.client import YClientsClient  # noqa: E402

SCHEDULE_CACHE_TTL_SEC = 600
SCHEDULE_DAYS_AHEAD = 14

_lock = threading.Lock()
_cache: dict[str, tuple[float, list[dict]]] = {}


def _range_key(company_id: int, start: date, end: date) -> str:
    return f"{company_id}:{start.isoformat()}:{end.isoformat()}"


def invalidate_schedule_cache(company_id: int | None = None) -> None:
    with _lock:
        if company_id is None:
            _cache.clear()
            return
        prefix = f"{company_id}:"
        for key in list(_cache):
            if key.startswith(prefix):
                del _cache[key]


def fetch_schedule_activities(yclients: YClientsClient, days: int = SCHEDULE_DAYS_AHEAD) -> list[dict]:
    today = date.today()
    end = today + timedelta(days=days - 1)
    company_id = yclients.config.yclients_company_id
    key = _range_key(company_id, today, end)
    now = time.monotonic()

    with _lock:
        entry = _cache.get(key)
        if entry and entry[0] > now:
            return entry[1]

    activities = yclients.get_schedule_activities(days)

    with _lock:
        _cache[key] = (time.monotonic() + SCHEDULE_CACHE_TTL_SEC, activities)
    return activities


def activities_for_date(activities: list[dict], target: date) -> list[dict]:
    now = datetime.now()
    filtered: list[dict] = []
    for activity in activities:
        dt = YClientsClient._parse_activity_datetime(activity)
        if not dt or dt.date() != target:
            continue
        if target == date.today() and dt < now:
            continue
        filtered.append(activity)

    filtered.sort(key=lambda item: YClientsClient._parse_activity_datetime(item) or now)
    return filtered


def extract_schedule_filters(activities: list[dict]) -> dict:
    trainers: dict[int, str] = {}
    services: dict[int, str] = {}
    service_titles: dict[str, str] = {}

    for activity in activities:
        staff = activity.get("staff") or {}
        staff_id = staff.get("id")
        if staff_id:
            name = (staff.get("name") or staff.get("specialization") or "Тренер").strip()
            trainers[int(staff_id)] = name

        service = activity.get("service") or {}
        service_id = service.get("id")
        title = str(service.get("title") or "Занятие").strip()
        if service_id:
            services[int(service_id)] = title
        elif title:
            service_titles[title.lower()] = title

    trainer_list = [
        {"id": staff_id, "name": name}
        for staff_id, name in sorted(trainers.items(), key=lambda item: item[1].lower())
    ]
    service_list = [
        {"id": service_id, "title": title}
        for service_id, title in sorted(services.items(), key=lambda item: item[1].lower())
    ]
    for title in sorted(service_titles.values(), key=str.lower):
        if title not in {item["title"] for item in service_list}:
            service_list.append({"id": None, "title": title})

    return {
        "trainers": trainer_list,
        "services": service_list,
    }
