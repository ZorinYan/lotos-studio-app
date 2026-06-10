import json
from pathlib import Path

STORAGE_PATH = Path(__file__).resolve().parent.parent / "data" / "users.json"


def _load() -> dict:
    if not STORAGE_PATH.exists():
        return {}
    with open(STORAGE_PATH, encoding="utf-8") as file:
        return json.load(file)


def _save(data: dict) -> None:
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORAGE_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _normalize_entry(raw) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, str):
        return {"phone": raw}
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def get_user_entry(vk_user_id: int) -> dict:
    return _normalize_entry(_load().get(str(vk_user_id)))


def update_user_entry(vk_user_id: int, **fields) -> dict:
    data = _load()
    entry = _normalize_entry(data.get(str(vk_user_id)))
    for key, value in fields.items():
        if value is None:
            entry.pop(key, None)
        else:
            entry[key] = value
    data[str(vk_user_id)] = entry
    _save(data)
    return entry


def get_phone(vk_user_id: int) -> str | None:
    phone = get_user_entry(vk_user_id).get("phone")
    return phone if phone else None


def set_phone(vk_user_id: int, phone: str) -> None:
    update_user_entry(vk_user_id, phone=phone)


def clear_phone(vk_user_id: int) -> None:
    data = _load()
    data.pop(str(vk_user_id), None)
    _save(data)


def get_all_users() -> dict[int, str]:
    result: dict[int, str] = {}
    for vk_id, raw in _load().items():
        entry = _normalize_entry(raw)
        phone = entry.get("phone")
        if phone:
            result[int(vk_id)] = phone
    return result
