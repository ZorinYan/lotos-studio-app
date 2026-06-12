from _lib_path import ensure_lib_path

ensure_lib_path()

from utils import storage  # noqa: E402
from utils import user_prefs  # noqa: E402


def load_settings(vk_user_id: int) -> dict:
    entry = storage.get_user_entry(vk_user_id)
    favorite = user_prefs.get_favorite_staff(vk_user_id)
    return {
        "favoriteTrainer": (
            {"id": favorite["id"], "name": favorite["name"]} if favorite else None
        ),
        "notificationsEnabled": bool(entry.get("vk_notifications_enabled")),
    }


def update_settings(
    vk_user_id: int,
    *,
    favorite_staff_id: int | None = None,
    favorite_staff_name: str | None = None,
    clear_favorite: bool = False,
    notifications_enabled: bool | None = None,
) -> dict:
    if clear_favorite:
        user_prefs.clear_favorite_staff(vk_user_id)
    elif favorite_staff_id is not None and favorite_staff_name:
        user_prefs.set_favorite_staff(
            vk_user_id,
            favorite_staff_id,
            favorite_staff_name.strip() or "Тренер",
        )

    if notifications_enabled is not None:
        storage.update_user_entry(
            vk_user_id,
            vk_notifications_enabled=notifications_enabled,
        )

    return load_settings(vk_user_id)
