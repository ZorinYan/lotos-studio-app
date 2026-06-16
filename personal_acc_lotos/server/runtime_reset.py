"""Сброс in-memory состояния API при старте и остановке (dev / reload)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def reset_runtime_state() -> None:
    """Очистить кэши и сбросить DB-слой — вызывать при старте и shutdown."""
    from client_cache import clear_all_client_caches
    from schedule_cache import invalidate_schedule_cache
    from vk_group_content import clear_feed_cache
    from auth_service import clear_pending_auth
    from dev_impersonation import clear_all_sessions
    from staff_resolver import clear_staff_directory_cache
    from staff_auth_service import clear_pending_staff_auth
    from utils.postgres import reset_pg_state

    clear_all_client_caches()
    invalidate_schedule_cache(None)
    clear_feed_cache()
    clear_pending_auth()
    clear_pending_staff_auth()
    clear_staff_directory_cache()
    clear_all_sessions()
    reset_pg_state()
    logger.debug("Runtime state reset")
