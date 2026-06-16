"""Хранение аккаунтов сотрудников в PostgreSQL."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

import psycopg

from utils.postgres import run_db

logger = logging.getLogger(__name__)

T = TypeVar("T")

_staff_table_missing_logged = False


def _is_missing_staff_table(error: BaseException) -> bool:
    if isinstance(error, psycopg.errors.UndefinedTable):
        return "staff_accounts" in str(error)
    sqlstate = getattr(error, "sqlstate", None)
    if sqlstate == "42P01":
        return "staff_accounts" in str(error).lower()
    message = str(error).lower()
    return "staff_accounts" in message and "does not exist" in message


def _log_missing_staff_table_once() -> None:
    global _staff_table_missing_logged
    if _staff_table_missing_logged:
        return
    _staff_table_missing_logged = True
    logger.warning(
        "Таблица staff_accounts не найдена — вход сотрудников отключён до миграции БД.",
    )


def staff_table_available() -> bool:
    def query(cur):
        cur.execute("SELECT to_regclass('public.staff_accounts') AS table_name")
        row = cur.fetchone()
        return bool(row and row.get("table_name"))

    return _run_staff_read(lambda: run_db(query, commit=False), False)


def _run_staff_read(operation: Callable[[], T], default: T) -> T:
    try:
        return operation()
    except psycopg.Error as error:
        if _is_missing_staff_table(error):
            _log_missing_staff_table_once()
            return default
        raise


def _run_staff_write(operation: Callable[[], T]) -> T:
    try:
        return operation()
    except psycopg.Error as error:
        if _is_missing_staff_table(error):
            _log_missing_staff_table_once()
            raise RuntimeError(
                "Таблица staff_accounts не создана. Выполните миграцию из server/schema.sql.",
            ) from error
        raise


def _row_to_profile(row: dict | None) -> dict | None:
    if not row:
        return None
    return {
        "phone": row["phone"],
        "yclients_staff_id": int(row["yclients_staff_id"]),
        "yclients_user_id": int(row["yclients_user_id"]) if row.get("yclients_user_id") else None,
        "staff_name": row["staff_name"],
        "specialization": row.get("specialization"),
        "position_title": row.get("position_title"),
        "vk_user_id": int(row["vk_user_id"]) if row.get("vk_user_id") else None,
        "password_hash": row.get("password_hash"),
        "logged_in": bool(row.get("logged_in")),
        "color_scheme": row.get("color_scheme") or "light",
    }


def fetch_by_phone(phone: str) -> dict | None:
    def query(cur):
        cur.execute("SELECT * FROM staff_accounts WHERE phone = %s LIMIT 1", (phone,))
        return cur.fetchone()

    return _row_to_profile(
        _run_staff_read(lambda: run_db(query, commit=False), None),
    )


def fetch_by_vk_user_id(vk_user_id: int) -> dict | None:
    def query(cur):
        cur.execute(
            """
            SELECT *
            FROM staff_accounts
            WHERE vk_user_id = %s AND logged_in IS TRUE
            LIMIT 1
            """,
            (vk_user_id,),
        )
        return cur.fetchone()

    return _row_to_profile(
        _run_staff_read(lambda: run_db(query, commit=False), None),
    )


def has_password(phone: str) -> bool:
    def query(cur):
        cur.execute(
            """
            SELECT 1
            FROM staff_accounts
            WHERE phone = %s AND password_hash IS NOT NULL
            LIMIT 1
            """,
            (phone,),
        )
        return cur.fetchone() is not None

    return _run_staff_read(lambda: run_db(query, commit=False), False)


def upsert_profile(
    *,
    phone: str,
    yclients_staff_id: int,
    staff_name: str,
    yclients_user_id: int | None = None,
    specialization: str | None = None,
    position_title: str | None = None,
) -> None:
    def mutate(cur):
        cur.execute(
            """
            INSERT INTO staff_accounts (
              phone, yclients_staff_id, yclients_user_id,
              staff_name, specialization, position_title
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (phone) DO UPDATE SET
              yclients_staff_id = EXCLUDED.yclients_staff_id,
              yclients_user_id = COALESCE(EXCLUDED.yclients_user_id, staff_accounts.yclients_user_id),
              staff_name = EXCLUDED.staff_name,
              specialization = EXCLUDED.specialization,
              position_title = EXCLUDED.position_title
            """,
            (
                phone,
                yclients_staff_id,
                yclients_user_id,
                staff_name,
                specialization,
                position_title,
            ),
        )

    _run_staff_write(lambda: run_db(mutate))


def save_password(vk_user_id: int, phone: str, password_hash: str) -> None:
    def mutate(cur):
        cur.execute(
            """
            UPDATE staff_accounts
            SET password_hash = %s,
                vk_user_id = %s,
                logged_in = TRUE,
                last_login_at = NOW()
            WHERE phone = %s
            """,
            (password_hash, vk_user_id, phone),
        )
        if cur.rowcount == 0:
            raise LookupError("staff profile not found")

    _run_staff_write(lambda: run_db(mutate))


def finish_password_login(vk_user_id: int, phone: str, row: dict[str, Any]) -> None:
    def mutate(cur):
        cur.execute(
            "UPDATE staff_accounts SET logged_in = FALSE WHERE vk_user_id = %s AND phone <> %s",
            (vk_user_id, phone),
        )
        cur.execute(
            """
            UPDATE staff_accounts
            SET vk_user_id = %s,
                logged_in = TRUE,
                last_login_at = NOW()
            WHERE phone = %s
            """,
            (vk_user_id, phone),
        )
        if cur.rowcount == 0:
            raise LookupError("staff profile not found")

    _run_staff_write(lambda: run_db(mutate))


def clear_session(vk_user_id: int) -> None:
    def mutate(cur):
        cur.execute(
            "UPDATE staff_accounts SET logged_in = FALSE WHERE vk_user_id = %s",
            (vk_user_id,),
        )

    _run_staff_read(lambda: run_db(mutate), None)


def update_color_scheme(vk_user_id: int, color_scheme: str) -> dict:
    scheme = color_scheme if color_scheme in ("light", "dark") else "light"

    def mutate(cur):
        cur.execute(
            """
            UPDATE staff_accounts
            SET color_scheme = %s
            WHERE vk_user_id = %s AND logged_in IS TRUE
            RETURNING *
            """,
            (scheme, vk_user_id),
        )
        row = cur.fetchone()
        if not row:
            raise LookupError("staff profile not found")
        return row

    result = _run_staff_write(lambda: run_db(mutate))
    profile = _row_to_profile(result)
    if not profile:
        raise LookupError("staff profile not found")
    return profile
