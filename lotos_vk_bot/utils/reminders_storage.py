import json
from pathlib import Path

STORAGE_PATH = Path(__file__).resolve().parent.parent / "data" / "reminders.json"


def _load() -> dict:
    if not STORAGE_PATH.exists():
        return {}
    with open(STORAGE_PATH, encoding="utf-8") as file:
        return json.load(file)


def _save(data: dict) -> None:
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORAGE_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _record_key(record_id: int, reminder_type: str) -> str:
    return f"record:{record_id}:{reminder_type}"


def _abonement_key(abonement_id: int, reminder_type: str) -> str:
    return f"abonement:{abonement_id}:{reminder_type}"


def was_sent_record(record_id: int, reminder_type: str) -> bool:
    data = _load()
    if data.get(_record_key(record_id, reminder_type)):
        return True
    if reminder_type == "training_60" and data.get(str(record_id)):
        return True
    return False


def mark_sent_record(record_id: int, reminder_type: str) -> None:
    data = _load()
    data[_record_key(record_id, reminder_type)] = True
    data.pop(str(record_id), None)
    _save(data)


def was_sent_abonement(abonement_id: int, reminder_type: str) -> bool:
    return bool(_load().get(_abonement_key(abonement_id, reminder_type)))


def mark_sent_abonement(abonement_id: int, reminder_type: str) -> None:
    data = _load()
    data[_abonement_key(abonement_id, reminder_type)] = True
    _save(data)


def clear_record(record_id: int) -> None:
    data = _load()
    changed = False
    prefix = f"record:{record_id}:"
    for key in list(data.keys()):
        if key == str(record_id) or key.startswith(prefix):
            data.pop(key, None)
            changed = True
    if changed:
        _save(data)
