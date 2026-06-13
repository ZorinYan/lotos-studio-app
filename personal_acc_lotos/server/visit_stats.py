from __future__ import annotations

from datetime import datetime

from record_serializer import is_upcoming, service_titles, staff_name
from yclients.client import YClientsClient

from utils.dates import format_date_short, studio_now

VISIT_RECORDS_DAYS_BACK = 365
VISIT_RECORDS_LIMIT = 200


def _record_date_iso(record: dict) -> str | None:
    dt = YClientsClient._parse_record_datetime(record)
    if not dt:
        return None
    return dt.date().isoformat()


def _record_sort_key(record: dict) -> datetime:
    return YClientsClient._parse_record_datetime(record) or datetime.min


def build_visit_stats(raw_records: list[dict], *, now: datetime | None = None) -> dict:
    """Считает визиты по всем прошедшим записям клиента, как во вкладке «Записи»."""
    current = now or studio_now()
    past_records: list[dict] = []

    for record in raw_records:
        if record.get("deleted"):
            continue
        if is_upcoming(record, now=current):
            continue
        past_records.append(record)

    past_records.sort(key=_record_sort_key)

    visit_history: list[dict] = []
    for record in past_records:
        date_iso = _record_date_iso(record)
        if not date_iso:
            continue
        visit_history.append(
            {
                "dateIso": date_iso,
                "service": service_titles(record),
            }
        )

    recent_records = list(reversed(past_records[-5:]))
    recent_visits = [
        {
            "date": format_date_short(
                record.get("datetime") or record.get("date", "") or "",
            ),
            "dateIso": _record_date_iso(record),
            "service": service_titles(record),
            "staff": staff_name(record),
        }
        for record in recent_records
        if _record_date_iso(record)
    ]

    profile_total = len(past_records)

    return {
        "totalVisits": profile_total,
        "visitHistory": visit_history,
        "recentVisits": recent_visits,
    }
