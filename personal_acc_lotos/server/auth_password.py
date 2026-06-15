"""Хеширование паролей для входа в мини-приложение."""

from __future__ import annotations

import bcrypt

MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 72


def validate_password(raw_password: str) -> str | None:
    password = raw_password.strip()
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов."
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Пароль должен быть не длиннее {MAX_PASSWORD_LENGTH} символов."
    return None


def hash_password(raw_password: str) -> str:
    password = raw_password.strip()
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def passwords_match(raw_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            raw_password.strip().encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False
