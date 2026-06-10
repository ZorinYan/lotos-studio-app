from datetime import datetime, timedelta


def event_window(
    start: datetime,
    duration_minutes: int | None,
    *,
    default_minutes: int = 60,
) -> dict[str, str]:
    minutes = duration_minutes if duration_minutes and duration_minutes > 0 else default_minutes
    end = start + timedelta(minutes=minutes)
    return {
        "startsAt": start.isoformat(),
        "endsAt": end.isoformat(),
    }
