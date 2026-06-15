"""Журнал отправленных напоминаний в PostgreSQL (Neon)."""

from __future__ import annotations

from utils.postgres import db_cursor


def was_sent_record(record_id: int, reminder_type: str) -> bool:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM reminder_log
            WHERE kind = %s AND entity_id = %s
            LIMIT 1
            """,
            (reminder_type, str(record_id)),
        )
        return cur.fetchone() is not None


def mark_sent_record(vk_user_id: int, record_id: int, reminder_type: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO reminder_log (vk_user_id, kind, entity_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (vk_user_id, kind, entity_id) DO NOTHING
            """,
            (vk_user_id, reminder_type, str(record_id)),
        )


def was_sent_abonement(abonement_id: int, reminder_type: str) -> bool:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM reminder_log
            WHERE kind = %s AND entity_id = %s
            LIMIT 1
            """,
            (reminder_type, str(abonement_id)),
        )
        return cur.fetchone() is not None


def mark_sent_abonement(vk_user_id: int, abonement_id: int, reminder_type: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO reminder_log (vk_user_id, kind, entity_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (vk_user_id, kind, entity_id) DO NOTHING
            """,
            (vk_user_id, reminder_type, str(abonement_id)),
        )


def clear_record(record_id: int) -> None:
    entity_id = str(record_id)
    with db_cursor() as cur:
        cur.execute(
            """
            DELETE FROM reminder_log
            WHERE entity_id = %s
              AND (kind LIKE 'training_%%' OR kind LIKE 'record:%%')
            """,
            (entity_id,),
        )
