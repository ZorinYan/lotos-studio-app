from _lib_path import ensure_lib_path

ensure_lib_path()

from utils import storage  # noqa: E402

_VALID_COLOR_SCHEMES = frozenset({"light", "dark"})


def normalize_color_scheme(value: str | None) -> str:
    if value in _VALID_COLOR_SCHEMES:
        return value
    return "light"


def prefs_from_entry(entry: dict) -> dict:
    return {
        "colorScheme": normalize_color_scheme(entry.get("color_scheme")),
        "welcomeBannerSeen": bool(entry.get("welcome_banner_seen")),
    }


def _favorite_from_entry(entry: dict) -> dict | None:
    staff_id = entry.get("favorite_staff_id")
    if not staff_id:
        return None
    return {
        "id": int(staff_id),
        "name": entry.get("favorite_staff_name") or "Тренер",
    }


def build_settings_response(
    vk_user_id: int,
    *,
    entry: dict | None = None,
    color_scheme_override: str | None = None,
    welcome_banner_seen_override: bool | None = None,
) -> dict:
    if entry is None:
        entry = storage.get_user_entry(vk_user_id)

    prefs = prefs_from_entry(entry)
    color_scheme = (
        normalize_color_scheme(color_scheme_override)
        if color_scheme_override is not None
        else prefs["colorScheme"]
    )
    welcome_banner_seen = (
        bool(welcome_banner_seen_override)
        if welcome_banner_seen_override is not None
        else prefs["welcomeBannerSeen"]
    )

    favorite = _favorite_from_entry(entry)
    return {
        "favoriteTrainer": (
            {"id": favorite["id"], "name": favorite["name"]} if favorite else None
        ),
        "notificationsEnabled": bool(entry.get("vk_notifications_enabled")),
        "colorScheme": color_scheme,
        "welcomeBannerSeen": welcome_banner_seen,
    }


def load_user_prefs(vk_user_id: int) -> dict:
    return prefs_from_entry(storage.get_user_entry(vk_user_id))


def load_settings(vk_user_id: int) -> dict:
    return build_settings_response(vk_user_id)


def update_settings(
    vk_user_id: int,
    *,
    favorite_staff_id: int | None = None,
    favorite_staff_name: str | None = None,
    clear_favorite: bool = False,
    notifications_enabled: bool | None = None,
    color_scheme: str | None = None,
    welcome_banner_seen: bool | None = None,
) -> dict:
    storage_fields: dict = {}
    saved_color_scheme: str | None = None
    saved_welcome_banner_seen: bool | None = None

    if clear_favorite:
        storage_fields["favorite_staff_id"] = None
        storage_fields["favorite_staff_name"] = None
    elif favorite_staff_id is not None and favorite_staff_name:
        storage_fields["favorite_staff_id"] = favorite_staff_id
        storage_fields["favorite_staff_name"] = (
            favorite_staff_name.strip() or "Тренер"
        )

    if notifications_enabled is not None:
        storage_fields["vk_notifications_enabled"] = notifications_enabled
    if color_scheme is not None:
        saved_color_scheme = normalize_color_scheme(color_scheme)
        storage_fields["color_scheme"] = saved_color_scheme
    if welcome_banner_seen is not None:
        saved_welcome_banner_seen = bool(welcome_banner_seen)
        storage_fields["welcome_banner_seen"] = saved_welcome_banner_seen

    updated_entry: dict | None = None
    if storage_fields:
        try:
            updated_entry = storage.update_user_entry(vk_user_id, **storage_fields)
        except LookupError as exc:
            raise RuntimeError(
                "Профиль пользователя не найден. Выйдите и войдите снова.",
            ) from exc

    return build_settings_response(
        vk_user_id,
        entry=updated_entry,
        color_scheme_override=saved_color_scheme,
        welcome_banner_seen_override=saved_welcome_banner_seen,
    )
