from dataclasses import dataclass, field


@dataclass
class RecordsContext:
    step: str = "pick"
    records: list[dict] = field(default_factory=list)
    record_map: dict[str, int] = field(default_factory=dict)
    record_labels: list[str] = field(default_factory=list)
    record_page: int = 0
    selected_record: dict | None = None


_contexts: dict[int, RecordsContext] = {}


def get(user_id: int) -> RecordsContext | None:
    return _contexts.get(user_id)


def start(user_id: int) -> RecordsContext:
    ctx = RecordsContext()
    _contexts[user_id] = ctx
    return ctx


def clear(user_id: int) -> None:
    _contexts.pop(user_id, None)


def is_active(user_id: int) -> bool:
    return user_id in _contexts
