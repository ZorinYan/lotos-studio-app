"""Одноразовые коды входа через сообщения VK."""

from __future__ import annotations

import secrets
import threading
import time

from miniapp_config import MiniAppConfig
from vk_messages import send_user_message

OTP_TTL_SEC = 300
OTP_COOLDOWN_SEC = 60
OTP_MAX_SENDS_PER_HOUR = 5
OTP_MAX_VERIFY_ATTEMPTS = 5

_lock = threading.Lock()
_pending: dict[str, dict] = {}
_send_log: dict[str, list[float]] = {}


def _key(vk_user_id: int, phone: str) -> str:
    return f"{vk_user_id}:{phone}"


def _cleanup_locked(now: float) -> None:
    expired = [key for key, entry in _pending.items() if entry["expires_at"] <= now]
    for key in expired:
        _pending.pop(key, None)


def _can_send_locked(vk_user_id: int, now: float) -> bool:
    key = str(vk_user_id)
    recent = [ts for ts in _send_log.get(key, []) if now - ts < 3600]
    _send_log[key] = recent
    return len(recent) < OTP_MAX_SENDS_PER_HOUR


def _record_send_locked(vk_user_id: int, now: float) -> None:
    key = str(vk_user_id)
    _send_log.setdefault(key, []).append(now)


def send_login_code(vk_user_id: int, phone: str, config: MiniAppConfig) -> tuple[bool, str | None]:
    """Генерирует код и отправляет в ЛС VK. Возвращает (успех, текст ошибки)."""
    now = time.monotonic()
    with _lock:
        _cleanup_locked(now)
        if not _can_send_locked(vk_user_id, now):
            return False, "Слишком много запросов кода. Попробуйте позже."

        entry_key = _key(vk_user_id, phone)
        existing = _pending.get(entry_key)
        if existing and now - existing["sent_at"] < OTP_COOLDOWN_SEC:
            return False, "Подождите минуту перед повторной отправкой."

        code = f"{secrets.randbelow(900_000) + 100_000:06d}"
        _pending[entry_key] = {
            "code": code,
            "phone": phone,
            "sent_at": now,
            "expires_at": now + OTP_TTL_SEC,
            "attempts": 0,
        }
        _record_send_locked(vk_user_id, now)

    text = (
        f"Код для входа в {config.studio_name}: {code}\n"
        "Если вы не запрашивали вход — просто проигнорируйте сообщение."
    )
    result = send_user_message(config.vk_group_token, vk_user_id, text)
    if result.ok:
        return True, None

    with _lock:
        _pending.pop(_key(vk_user_id, phone), None)

    if result.error_code in {901, 902, 15}:
        return False, "Не удалось отправить сообщение. Разрешите сообщения от сообщества."
    return False, result.error_message or "Не удалось отправить код в VK."


def verify_login_code(vk_user_id: int, phone: str, raw_code: str) -> tuple[bool, str | None]:
    code = raw_code.strip()
    if not code.isdigit() or len(code) != 6:
        return False, "Введите 6-значный код из сообщения VK."

    now = time.monotonic()
    with _lock:
        _cleanup_locked(now)
        entry = _pending.get(_key(vk_user_id, phone))
        if not entry:
            return False, "Код устарел или не запрашивался. Запросите новый или войдите по имени."

        if entry["attempts"] >= OTP_MAX_VERIFY_ATTEMPTS:
            _pending.pop(_key(vk_user_id, phone), None)
            return False, "Превышено число попыток. Войдите по имени и фамилии."

        entry["attempts"] += 1
        if entry["code"] != code:
            return False, "Неверный код. Проверьте сообщение от сообщества студии."

        _pending.pop(_key(vk_user_id, phone), None)
        return True, None
