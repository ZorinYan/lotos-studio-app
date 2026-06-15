"""Подключение к PostgreSQL (Supabase / Neon) через пул psycopg."""

from __future__ import annotations

import logging
import os
import threading
import time
from contextlib import contextmanager
from typing import Iterator
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()
_db_gate = threading.Lock()
_db_keepalive_stop = threading.Event()
_db_keepalive_thread: threading.Thread | None = None

DB_KEEPALIVE_INTERVAL_SEC = 90
CONNECT_TIMEOUT_SEC = 45
POOL_WAIT_TIMEOUT_SEC = 60
POOL_MAX_SIZE = 2
MAX_IDLE_SEC = 45
MAX_LIFETIME_SEC = 300
DB_RETRY_ATTEMPTS = 4
DB_RETRY_BACKOFF_SEC = 1.2

_POOL_RESET_ERRORS = (
    psycopg.OperationalError,
    psycopg.InterfaceError,
)
_RETRY_ERRORS = _POOL_RESET_ERRORS + (PoolTimeout,)


def _check_connection(conn: psycopg.Connection) -> None:
    old_autocommit = conn.autocommit
    conn.autocommit = True
    try:
        conn.execute("SELECT 1")
    finally:
        conn.autocommit = old_autocommit


def database_configured() -> bool:
    return bool(os.getenv("DATABASE_URL", "").strip())


def require_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL не задан. Добавьте строку подключения Supabase (или Neon) в .env.",
        )
    return _normalize_database_url(url)


def _uses_supabase_pgbouncer(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if "supabase.com" not in host:
        return False
    if parsed.port == 6543:
        return True
    return "pgbouncer=true" in (parsed.query or "").lower()


def _warn_connection_mode(url: str) -> None:
    host = urlparse(url).hostname or ""
    if "supabase.com" in host and not _uses_supabase_pgbouncer(url):
        logger.warning(
            "DATABASE_URL Supabase без transaction pooler (порт 6543). "
            "В Dashboard → Connect → URI выберите «Transaction pooler».",
        )


def _normalize_database_url(url: str) -> str:
    import sys

    from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    changed = False

    if "sslmode" not in params:
        params["sslmode"] = ["require"]
        changed = True

    if sys.platform == "win32":
        if "gssencmode" not in params:
            params["gssencmode"] = ["disable"]
            changed = True
        if params.get("channel_binding", [""])[0] == "require":
            params["channel_binding"] = ["disable"]
            changed = True

    if not changed:
        _warn_connection_mode(url)
        return url

    query = urlencode({key: values[0] for key, values in params.items()})
    normalized = urlunparse(parsed._replace(query=query))
    _warn_connection_mode(normalized)
    return normalized


def _connection_kwargs(conninfo: str) -> dict:
    kwargs: dict = {
        "row_factory": dict_row,
        "connect_timeout": CONNECT_TIMEOUT_SEC,
    }
    if _uses_supabase_pgbouncer(conninfo):
        kwargs["prepare_threshold"] = None
    return kwargs


def reset_pool() -> None:
    global _pool
    with _pool_lock:
        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                logger.exception("Failed to close DB pool")
            _pool = None


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is not None:
        return _pool

    with _pool_lock:
        if _pool is None:
            conninfo = require_database_url()
            _pool = ConnectionPool(
                conninfo,
                min_size=0,
                max_size=POOL_MAX_SIZE,
                max_idle=MAX_IDLE_SEC,
                max_lifetime=MAX_LIFETIME_SEC,
                timeout=POOL_WAIT_TIMEOUT_SEC,
                check=_check_connection,
                kwargs=_connection_kwargs(conninfo),
            )
        return _pool


@contextmanager
def db_cursor(*, commit: bool = True, timeout: float | None = None) -> Iterator[psycopg.Cursor]:
    wait_timeout = POOL_WAIT_TIMEOUT_SEC if timeout is None else timeout
    with _get_pool().connection(timeout=wait_timeout) as conn:
        with conn.cursor() as cur:
            yield cur
            if commit:
                conn.commit()


def _run_db_once(callback, *, commit: bool, timeout: float | None):
    last_error: Exception | None = None
    base_timeout = POOL_WAIT_TIMEOUT_SEC if timeout is None else timeout

    for attempt in range(DB_RETRY_ATTEMPTS):
        wait_timeout = max(base_timeout, 60.0) if attempt > 0 else base_timeout
        try:
            with db_cursor(commit=commit, timeout=wait_timeout) as cur:
                return callback(cur)
        except _RETRY_ERRORS as exc:
            last_error = exc
            logger.warning(
                "DB attempt %s/%s failed: %s",
                attempt + 1,
                DB_RETRY_ATTEMPTS,
                exc,
            )
            if attempt + 1 >= DB_RETRY_ATTEMPTS:
                raise
            if isinstance(exc, _POOL_RESET_ERRORS):
                reset_pool()
            time.sleep(DB_RETRY_BACKOFF_SEC * (attempt + 1))

    if last_error:
        raise last_error
    raise RuntimeError("run_db finished without result")


def run_db(callback, *, commit: bool = True, timeout: float | None = None):
    with _db_gate:
        return _run_db_once(callback, commit=commit, timeout=timeout)


def warm_pool(*, timeout: float | None = None) -> None:
    run_db(
        lambda cur: cur.execute("SELECT 1") or cur.fetchone(),
        timeout=timeout,
    )


def ping_database() -> bool:
    if not database_configured():
        return False
    try:
        warm_pool()
        return True
    except Exception:
        logger.exception("PostgreSQL ping failed")
        return False


def close_pool() -> None:
    stop_db_keepalive()
    reset_pool()


def _db_keepalive_loop() -> None:
    while not _db_keepalive_stop.wait(DB_KEEPALIVE_INTERVAL_SEC):
        if not _db_gate.acquire(blocking=False):
            continue
        try:
            _run_db_once(
                lambda cur: cur.execute("SELECT 1") or cur.fetchone(),
                commit=True,
                timeout=POOL_WAIT_TIMEOUT_SEC,
            )
        except PoolTimeout:
            logger.debug("DB keep-alive: пропущен, пул занят")
        except Exception:
            logger.warning("DB keep-alive: не удалось прогреть пул", exc_info=True)
        finally:
            _db_gate.release()


def start_db_keepalive() -> None:
    global _db_keepalive_thread
    if not database_configured():
        return
    if _db_keepalive_thread and _db_keepalive_thread.is_alive():
        return
    _db_keepalive_stop.clear()
    _db_keepalive_thread = threading.Thread(
        target=_db_keepalive_loop,
        name="postgres-keepalive",
        daemon=True,
    )
    _db_keepalive_thread.start()


def stop_db_keepalive() -> None:
    _db_keepalive_stop.set()
