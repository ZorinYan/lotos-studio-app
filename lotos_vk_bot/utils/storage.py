"""Хранение привязки VK → клиент студии в PostgreSQL (Neon)."""

from __future__ import annotations

from typing import Any

from psycopg.types.json import Json

from utils.postgres import db_cursor

_FIELD_TO_COLUMN = {
    "phone": "phone",
    "client_name": "client_name",
    "favorite_staff_id": "favorite_staff_id",
    "favorite_staff_name": "favorite_staff_name",
    "last_booking": "last_booking",
    "vk_notifications_enabled": "notifications_enabled",
    "notifications_enabled": "notifications_enabled",
    "auth_method": "auth_method",
    "linked_at": "linked_at",
    "password_hash": "password_hash",
}


def _normalize_entry(raw: Any) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, str):
        return {"phone": raw}
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def _row_to_entry(row: dict | None) -> dict:
    if not row:
        return {}

    entry: dict[str, Any] = {}
    if row.get("phone"):
        entry["phone"] = row["phone"]
    if row.get("client_name"):
        entry["client_name"] = row["client_name"]
    if row.get("favorite_staff_id") is not None:
        entry["favorite_staff_id"] = row["favorite_staff_id"]
    if row.get("favorite_staff_name"):
        entry["favorite_staff_name"] = row["favorite_staff_name"]
    if row.get("last_booking"):
        entry["last_booking"] = row["last_booking"]
    entry["vk_notifications_enabled"] = bool(row.get("notifications_enabled"))
    if row.get("auth_method"):
        entry["auth_method"] = row["auth_method"]
    if row.get("linked_at"):
        entry["linked_at"] = row["linked_at"].isoformat()
    return entry


def _prepare_column_value(column: str, value: Any) -> Any:
    if column == "last_booking" and value is not None:
        return Json(value)
    return value


def _fetch_row(vk_user_id: int) -> dict | None:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE vk_user_id = %s", (vk_user_id,))
        return cur.fetchone()


def get_user_entry(vk_user_id: int) -> dict:
    return _row_to_entry(_fetch_row(vk_user_id))


def update_user_entry(vk_user_id: int, **fields) -> dict:
    if not fields:
        return get_user_entry(vk_user_id)

    updates: dict[str, Any] = {}
    clears: list[str] = []

    for key, value in fields.items():
        column = _FIELD_TO_COLUMN.get(key)
        if not column:
            continue
        if value is None:
            clears.append(column)
        else:
            updates[column] = _prepare_column_value(column, value)

    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE vk_user_id = %s", (vk_user_id,))
        exists = cur.fetchone() is not None

        if exists:
            set_parts: list[str] = []
            params: list[Any] = []
            for column, value in updates.items():
                set_parts.append(f"{column} = %s")
                params.append(value)
            for column in clears:
                set_parts.append(f"{column} = NULL")
            if set_parts:
                params.append(vk_user_id)
                cur.execute(
                    f"UPDATE users SET {', '.join(set_parts)} WHERE vk_user_id = %s",
                    params,
                )
        else:
            phone = updates.get("phone")
            if not phone:
                return {}
            columns = ["vk_user_id", *updates.keys()]
            placeholders = ["%s"] * len(columns)
            values = [vk_user_id, *updates.values()]
            cur.execute(
                f"INSERT INTO users ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                values,
            )

        cur.execute("SELECT * FROM users WHERE vk_user_id = %s", (vk_user_id,))
        return _row_to_entry(cur.fetchone())


def get_phone(vk_user_id: int) -> str | None:
    phone = get_user_entry(vk_user_id).get("phone")
    return phone if phone else None


def set_phone(vk_user_id: int, phone: str) -> None:
    update_user_entry(vk_user_id, phone=phone)


def clear_phone(vk_user_id: int) -> None:
    with db_cursor() as cur:
        cur.execute("DELETE FROM users WHERE vk_user_id = %s", (vk_user_id,))


def get_all_users() -> dict[int, str]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT vk_user_id, phone FROM users WHERE phone IS NOT NULL ORDER BY vk_user_id",
        )
        rows = cur.fetchall()
    return {int(row["vk_user_id"]): row["phone"] for row in rows}


def has_password_for_phone(vk_user_id: int, phone: str) -> bool:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM users
            WHERE vk_user_id = %s AND phone = %s AND password_hash IS NOT NULL
            LIMIT 1
            """,
            (vk_user_id, phone),
        )
        return cur.fetchone() is not None


def get_password_hash_for_phone(vk_user_id: int, phone: str) -> str | None:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT password_hash
            FROM users
            WHERE vk_user_id = %s AND phone = %s
            LIMIT 1
            """,
            (vk_user_id, phone),
        )
        row = cur.fetchone()
    if not row:
        return None
    value = row.get("password_hash")
    return str(value) if value else None


def set_password_hash(vk_user_id: int, password_hash: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE vk_user_id = %s",
            (password_hash, vk_user_id),
        )
