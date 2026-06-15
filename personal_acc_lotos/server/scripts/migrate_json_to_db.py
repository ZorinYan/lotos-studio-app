#!/usr/bin/env python3
"""Однократный перенос users.json в Neon PostgreSQL.

Примеры:
  cd personal_acc_lotos/server
  set DATABASE_URL=postgresql://...
  python scripts/migrate_json_to_db.py ../../lotos_vk_bot/data/users.json
  python scripts/migrate_json_to_db.py data/users.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _lib_path import ensure_lib_path

ensure_lib_path()

from utils import storage  # noqa: E402
from utils.postgres import ping_database  # noqa: E402


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, dict) else {}


def _normalize_raw_entry(raw) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, str):
        return {"phone": raw}
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def migrate_users(path: Path) -> tuple[int, int]:
    data = _load_json(path)
    migrated = 0
    skipped = 0

    for vk_id_raw, raw_entry in data.items():
        try:
            vk_user_id = int(vk_id_raw)
        except (TypeError, ValueError):
            skipped += 1
            continue

        entry = _normalize_raw_entry(raw_entry)
        phone = entry.get("phone")
        if not phone:
            skipped += 1
            continue

        fields = {
            "phone": str(phone),
            "client_name": entry.get("client_name"),
            "favorite_staff_id": entry.get("favorite_staff_id"),
            "favorite_staff_name": entry.get("favorite_staff_name"),
            "last_booking": entry.get("last_booking"),
        }
        notifications = entry.get("vk_notifications_enabled")
        if notifications is None:
            notifications = entry.get("notifications_enabled")
        if notifications is not None:
            fields["vk_notifications_enabled"] = bool(notifications)
        if entry.get("auth_method"):
            fields["auth_method"] = entry.get("auth_method")

        scheme = entry.get("color_scheme") or entry.get("colorScheme")
        if scheme in ("light", "dark"):
            fields["color_scheme"] = scheme
        welcome = entry.get("welcome_banner_seen")
        if welcome is None:
            welcome = entry.get("welcomeBannerSeen")
        if welcome is not None:
            fields["welcome_banner_seen"] = bool(welcome)

        storage.update_user_entry(vk_user_id, **fields)
        migrated += 1

    return migrated, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Перенос users.json в Neon PostgreSQL")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Пути к users.json (можно несколько; позже перезаписывают по vk_user_id)",
    )
    args = parser.parse_args()

    if not ping_database():
        print("Не удалось подключиться к DATABASE_URL", file=sys.stderr)
        return 1

    paths = [Path(p) for p in args.paths]
    if not paths:
        default_candidates = [
            Path(__file__).resolve().parent.parent / "data" / "users.json",
            Path(__file__).resolve().parents[3] / "lotos_vk_bot" / "data" / "users.json",
        ]
        paths = [p for p in default_candidates if p.exists()]

    if not paths:
        print("users.json не найден. Укажите путь аргументом.", file=sys.stderr)
        return 1

    total_migrated = 0
    total_skipped = 0
    for path in paths:
        migrated, skipped = migrate_users(path)
        print(f"{path}: перенесено {migrated}, пропущено {skipped}")
        total_migrated += migrated
        total_skipped += skipped

    print(f"Итого: {total_migrated} пользователей, пропущено {total_skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
