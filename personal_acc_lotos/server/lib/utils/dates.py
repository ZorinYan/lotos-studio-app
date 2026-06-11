import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

DEFAULT_STUDIO_TIMEZONE = "Asia/Yekaterinburg"

MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)
WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


def studio_timezone() -> ZoneInfo:
    name = os.getenv("STUDIO_TIMEZONE", DEFAULT_STUDIO_TIMEZONE).strip()
    if not name:
        name = DEFAULT_STUDIO_TIMEZONE
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo(DEFAULT_STUDIO_TIMEZONE)


def studio_now() -> datetime:
    """Текущее время студии (naive), для сравнения с датами YClients."""
    return datetime.now(studio_timezone()).replace(tzinfo=None)


def studio_today() -> date:
    return studio_now().date()


def parse_record_datetime(raw: str) -> datetime | None:
    """Дата/время записи YClients в локальном времени студии (naive)."""
    if not raw:
        return None
    text = str(raw).strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(studio_timezone()).replace(tzinfo=None)
        return dt
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def parse_datetime(raw: str) -> datetime | None:
    return parse_record_datetime(raw)


def format_date_short(raw: str) -> str:
    dt = parse_datetime(raw)
    if not dt:
        return raw[:10] if raw else "—"
    return f"{WEEKDAYS[dt.weekday()]}, {dt.day} {MONTHS[dt.month - 1]}"


def format_datetime_short(raw: str) -> str:
    dt = parse_datetime(raw)
    if not dt:
        return raw[:16] if raw else "—"
    return (
        f"{WEEKDAYS[dt.weekday()]}, {dt.day} {MONTHS[dt.month - 1]}"
        f"  ·  {dt.strftime('%H:%M')}"
    )
