"""????????????? ????????? ????-?????????? ? PostgreSQL (Supabase)."""

from __future__ import annotations

from typing import Any

from psycopg.types.json import Json

from utils.postgres import db_cursor, run_db

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
    "logged_in": "logged_in",
    "color_scheme": "color_scheme",
    "welcome_banner_seen": "welcome_banner_seen",
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
    if row.get("password_hash"):
        entry["password_hash"] = row["password_hash"]
    if "logged_in" in row:
        entry["logged_in"] = bool(row["logged_in"])
    scheme = row.get("color_scheme") or "light"
    entry["color_scheme"] = scheme if scheme in ("light", "dark") else "light"
    if "welcome_banner_seen" in row:
        entry["welcome_banner_seen"] = bool(row["welcome_banner_seen"])
    if row.get("linked_at"):
        entry["linked_at"] = row["linked_at"].isoformat()
    return entry


def _prepare_column_value(column: str, value: Any) -> Any:
    if column == "last_booking" and value is not None:
        return Json(value)
    return value


def _fetch_row(vk_user_id: int) -> dict | None:
    def query(cur):
        cur.execute("SELECT * FROM users WHERE vk_user_id = %s", (vk_user_id,))
        return cur.fetchone()

    return run_db(query, commit=False)


def fetch_row_by_phone(phone: str) -> dict | None:
    def query(cur):
        cur.execute("SELECT * FROM users WHERE phone = %s LIMIT 1", (phone,))
        return cur.fetchone()

    return run_db(query, commit=False)


def _fetch_by_phone(phone: str) -> dict | None:
    return fetch_row_by_phone(phone)


def _dev_impersonation_entry(vk_user_id: int) -> dict | None:
    from dev_impersonation import get_session, is_developer

    if not is_developer(vk_user_id):
        return None
    session = get_session(vk_user_id)
    if not session:
        return None
    phone = session["phone"]
    row = fetch_row_by_phone(phone)
    if row:
        return _row_to_entry(row)
    entry: dict[str, Any] = {"phone": phone, "logged_in": True}
    if session.get("client_name"):
        entry["client_name"] = session["client_name"]
    return entry


def _resolve_storage_vk_user_id(vk_user_id: int) -> int:
    from dev_impersonation import get_session, is_developer

    if not is_developer(vk_user_id):
        return vk_user_id
    session = get_session(vk_user_id)
    if not session:
        return vk_user_id
    row = fetch_row_by_phone(session["phone"])
    if row:
        return int(row["vk_user_id"])
    return vk_user_id


def get_user_entry(vk_user_id: int) -> dict:
    impersonated = _dev_impersonation_entry(vk_user_id)
    if impersonated is not None:
        return impersonated
    return _row_to_entry(_fetch_row(vk_user_id))


def get_user_auth_state(vk_user_id: int) -> dict:
    return get_user_entry(vk_user_id)


def update_user_entry(vk_user_id: int, **fields) -> dict:
    from dev_impersonation import dev_impersonation_skips_db_writes

    if dev_impersonation_skips_db_writes(vk_user_id):
        return get_user_entry(vk_user_id)

    vk_user_id = _resolve_storage_vk_user_id(vk_user_id)
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

    def mutate(cur):
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
                f"UPDATE users SET {', '.join(set_parts)} WHERE vk_user_id = %s RETURNING *",
                params,
            )
            row = cur.fetchone()
            if row is not None:
                return _row_to_entry(row)

            phone = updates.get("phone")
            if not phone:
                raise LookupError(f"user {vk_user_id} not found")

            columns = ["vk_user_id", *updates.keys()]
            placeholders = ["%s"] * len(columns)
            values = [vk_user_id, *updates.values()]
            cur.execute(
                f"INSERT INTO users ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING *",
                values,
            )
            row = cur.fetchone()
            if row is None:
                raise LookupError(f"user {vk_user_id} not found")
            return _row_to_entry(row)

        cur.execute("SELECT * FROM users WHERE vk_user_id = %s", (vk_user_id,))
        row = cur.fetchone()
        if row is None:
            raise LookupError(f"user {vk_user_id} not found")
        return _row_to_entry(row)

    return run_db(mutate)


def get_phone(vk_user_id: int) -> str | None:
    impersonated = _dev_impersonation_entry(vk_user_id)
    if impersonated is not None:
        phone = impersonated.get("phone")
        return phone if phone else None
    phone = _row_to_entry(_fetch_row(vk_user_id)).get("phone")
    return phone if phone else None


def set_phone(vk_user_id: int, phone: str) -> None:
    update_user_entry(vk_user_id, phone=phone)


def clear_phone(vk_user_id: int) -> None:
    def delete(cur):
        cur.execute("DELETE FROM users WHERE vk_user_id = %s", (vk_user_id,))

    run_db(delete)


def get_all_users() -> dict[int, str]:
    def query(cur):
        cur.execute(
            "SELECT vk_user_id, phone FROM users WHERE phone IS NOT NULL ORDER BY vk_user_id",
        )
        return cur.fetchall()

    rows = run_db(query, commit=False)
    return {int(row["vk_user_id"]): row["phone"] for row in rows}


def has_password_for_phone(phone: str) -> bool:
    def query(cur):
        cur.execute(
            """
            SELECT 1
            FROM users
            WHERE phone = %s AND password_hash IS NOT NULL
            LIMIT 1
            """,
            (phone,),
        )
        return cur.fetchone() is not None

    return run_db(query, commit=False)


def get_password_hash_for_phone(vk_user_id: int, phone: str) -> str | None:
    row = _fetch_by_phone(phone)
    if not row or row.get("phone") != phone:
        return None
    value = row.get("password_hash")
    return str(value) if value else None


def upsert_verified_user(vk_user_id: int, phone: str, client_name: str) -> None:
    def mutate(cur):
        cur.execute(
            """
            SELECT vk_user_id
            FROM users
            WHERE phone = %s AND vk_user_id <> %s
            LIMIT 1
            """,
            (phone, vk_user_id),
        )
        if cur.fetchone():
            raise RuntimeError("???? ????? ??? ???????? ? ??????? ????????.")

        cur.execute(
            """
            INSERT INTO users (vk_user_id, phone, client_name, logged_in)
            VALUES (%s, %s, %s, FALSE)
            ON CONFLICT (vk_user_id) DO UPDATE SET
              phone = EXCLUDED.phone,
              client_name = EXCLUDED.client_name,
              logged_in = FALSE
            """,
            (vk_user_id, phone, client_name),
        )

    run_db(mutate)


def save_password(vk_user_id: int, phone: str, password_hash: str) -> None:
    def mutate(cur):
        cur.execute(
            """
            UPDATE users
            SET password_hash = %s,
                auth_method = 'password',
                logged_in = TRUE
            WHERE vk_user_id = %s AND phone = %s
            """,
            (password_hash, vk_user_id, phone),
        )
        if cur.rowcount == 0:
            raise LookupError("identity not verified")

    run_db(mutate)


def finish_password_login(vk_user_id: int, phone: str, row: dict) -> None:
    owner_vk_user_id = int(row["vk_user_id"])

    def mutate(cur):
        if owner_vk_user_id == vk_user_id:
            cur.execute(
                """
                UPDATE users
                SET logged_in = TRUE, auth_method = COALESCE(auth_method, 'password')
                WHERE vk_user_id = %s AND phone = %s
                """,
                (vk_user_id, phone),
            )
            if cur.rowcount == 0:
                raise LookupError("identity not verified")
            return

        cur.execute("DELETE FROM users WHERE vk_user_id = %s", (owner_vk_user_id,))
        cur.execute(
            """
            INSERT INTO users (
              vk_user_id, phone, client_name, password_hash, auth_method,
              favorite_staff_id, favorite_staff_name, last_booking,
              notifications_enabled, color_scheme, welcome_banner_seen, logged_in
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (vk_user_id) DO UPDATE SET
              phone = EXCLUDED.phone,
              client_name = EXCLUDED.client_name,
              password_hash = EXCLUDED.password_hash,
              auth_method = EXCLUDED.auth_method,
              favorite_staff_id = EXCLUDED.favorite_staff_id,
              favorite_staff_name = EXCLUDED.favorite_staff_name,
              last_booking = EXCLUDED.last_booking,
              notifications_enabled = EXCLUDED.notifications_enabled,
              color_scheme = EXCLUDED.color_scheme,
              welcome_banner_seen = EXCLUDED.welcome_banner_seen,
              logged_in = TRUE
            """,
            (
                vk_user_id,
                row["phone"],
                row.get("client_name"),
                row["password_hash"],
                row.get("auth_method") or "password",
                row.get("favorite_staff_id"),
                row.get("favorite_staff_name"),
                Json(row["last_booking"]) if row.get("last_booking") else None,
                row.get("notifications_enabled"),
                row.get("color_scheme") or "light",
                bool(row.get("welcome_banner_seen")),
            ),
        )

    run_db(mutate)


def complete_password_login(vk_user_id: int, phone: str) -> None:
    row = fetch_row_by_phone(phone)
    if not row or not row.get("password_hash"):
        raise LookupError("password not set")
    finish_password_login(vk_user_id, phone, row)


def clear_session(vk_user_id: int) -> None:
    def mutate(cur):
        cur.execute(
            """
            UPDATE users
            SET logged_in = FALSE
            WHERE vk_user_id = %s AND password_hash IS NOT NULL
            """,
            (vk_user_id,),
        )
        if cur.rowcount == 0:
            cur.execute("DELETE FROM users WHERE vk_user_id = %s", (vk_user_id,))

    run_db(mutate)


def set_logged_in(vk_user_id: int, *, logged_in: bool) -> None:
    update_user_entry(vk_user_id, logged_in=logged_in)


def mark_password_auth(vk_user_id: int) -> None:
    update_user_entry(vk_user_id, auth_method="password", logged_in=True)
