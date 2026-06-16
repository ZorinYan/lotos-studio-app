from staff_auth_service import StaffAuthError, get_staff_auth_status
from staff_storage import fetch_by_vk_user_id, update_color_scheme
from settings_api import normalize_color_scheme
from utils.phone import format_phone_display


def _require_staff(vk_user_id: int) -> dict:
    status = get_staff_auth_status(vk_user_id)
    if not status.authenticated:
        raise StaffAuthError("not_authenticated", "Войдите как сотрудник.")
    row = fetch_by_vk_user_id(vk_user_id)
    if not row:
        raise StaffAuthError("not_authenticated", "Войдите как сотрудник.")
    return row


def load_staff_settings(vk_user_id: int) -> dict:
    row = _require_staff(vk_user_id)
    phone = row.get("phone")
    return {
        "staffName": row.get("staff_name"),
        "phoneDisplay": format_phone_display(phone) if phone else None,
        "colorScheme": normalize_color_scheme(row.get("color_scheme")),
    }


def update_staff_settings(
    vk_user_id: int,
    *,
    color_scheme: str | None = None,
) -> dict:
    _require_staff(vk_user_id)
    if color_scheme is None:
        return load_staff_settings(vk_user_id)

    try:
        row = update_color_scheme(vk_user_id, color_scheme)
    except LookupError as exc:
        raise StaffAuthError(
            "staff_not_found",
            "Профиль сотрудника не найден. Выйдите и войдите снова.",
        ) from exc
    except RuntimeError as exc:
        raise StaffAuthError("staff_storage_unavailable", str(exc)) from exc

    return {
        "staffName": row.get("staff_name"),
        "phoneDisplay": format_phone_display(row["phone"]) if row.get("phone") else None,
        "colorScheme": normalize_color_scheme(row.get("color_scheme")),
    }
