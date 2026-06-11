from utils import storage


def get_favorite_staff(user_id: int) -> dict | None:
    entry = storage.get_user_entry(user_id)
    staff_id = entry.get("favorite_staff_id")
    if not staff_id:
        return None
    name = entry.get("favorite_staff_name") or "Тренер"
    return {"id": int(staff_id), "name": name}


def set_favorite_staff(user_id: int, staff_id: int, staff_name: str) -> None:
    storage.update_user_entry(
        user_id,
        favorite_staff_id=staff_id,
        favorite_staff_name=staff_name,
    )


def clear_favorite_staff(user_id: int) -> None:
    storage.update_user_entry(
        user_id,
        favorite_staff_id=None,
        favorite_staff_name=None,
    )


def get_last_booking(user_id: int) -> dict | None:
    entry = storage.get_user_entry(user_id)
    raw = entry.get("last_booking")
    if not isinstance(raw, dict):
        return None
    staff_id = raw.get("staff_id")
    service_title = raw.get("service_title")
    if not staff_id or not service_title:
        return None
    return {
        "staff_id": int(staff_id),
        "staff_name": raw.get("staff_name") or "Тренер",
        "service_title": str(service_title),
        "service_id": raw.get("service_id"),
    }


def set_last_booking(
    user_id: int,
    *,
    staff_id: int,
    staff_name: str,
    service_title: str,
    service_id: int | None = None,
) -> None:
    storage.update_user_entry(
        user_id,
        last_booking={
            "staff_id": staff_id,
            "staff_name": staff_name,
            "service_title": service_title,
            "service_id": service_id,
        },
    )
