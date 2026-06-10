from dataclasses import dataclass, field
from datetime import date


@dataclass
class BookingContext:
    mode: str = "normal"
    step: str = "day"
    all_activities: list[dict] = field(default_factory=list)
    day_map: dict[str, date] = field(default_factory=dict)
    day_labels: list[str] = field(default_factory=list)
    day_page: int = 0
    selected_date: date | None = None
    day_activities: list[dict] = field(default_factory=list)
    staff_map: dict[str, int] = field(default_factory=dict)
    staff_names: list[str] = field(default_factory=list)
    staff_page: int = 0
    selected_staff_id: int | None = None
    filtered_activities: list[dict] = field(default_factory=list)
    class_map: dict[str, int] = field(default_factory=dict)
    class_labels: list[str] = field(default_factory=list)
    class_page: int = 0
    selected_activity: dict | None = None


_contexts: dict[int, BookingContext] = {}


def get(user_id: int) -> BookingContext | None:
    return _contexts.get(user_id)


def start(user_id: int) -> BookingContext:
    ctx = BookingContext()
    _contexts[user_id] = ctx
    return ctx


def clear(user_id: int) -> None:
    _contexts.pop(user_id, None)


def is_active(user_id: int) -> bool:
    return user_id in _contexts
