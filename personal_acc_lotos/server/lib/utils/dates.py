from datetime import datetime

MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)
WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


def parse_datetime(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:19], fmt)
        except ValueError:
            continue
    return None


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
