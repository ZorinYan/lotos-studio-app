"""In-memory impersonation for the studio developer (no DB writes on login)."""

from __future__ import annotations

import threading
import time

DEVELOPER_VK_USER_ID = 230959721
_SESSION_TTL_SEC = 8 * 60 * 60

_sessions: dict[int, tuple[str, str, float]] = {}
_lock = threading.Lock()


def is_developer(vk_user_id: int) -> bool:
    return vk_user_id == DEVELOPER_VK_USER_ID


def get_session(vk_user_id: int) -> dict[str, str] | None:
    with _lock:
        entry = _sessions.get(vk_user_id)
    if not entry:
        return None
    phone, client_name, cached_at = entry
    if time.monotonic() - cached_at > _SESSION_TTL_SEC:
        clear_session(vk_user_id)
        return None
    return {"phone": phone, "client_name": client_name}


def set_session(vk_user_id: int, phone: str, client_name: str) -> None:
    with _lock:
        _sessions[vk_user_id] = (phone, client_name, time.monotonic())


def clear_session(vk_user_id: int) -> None:
    with _lock:
        _sessions.pop(vk_user_id, None)


def clear_all_sessions() -> None:
    with _lock:
        _sessions.clear()
