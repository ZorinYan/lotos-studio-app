"""Подключение к PostgreSQL (Supabase) — одно соединение на запрос (PgBouncer transaction mode)."""

from __future__ import annotations

import logging
import os
import sys
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Iterator, TypeVar
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

_conninfo: str | None = None
_conn_kwargs: dict | None = None

CONNECT_TIMEOUT_SEC = 10
DB_RETRY_ATTEMPTS = 3
DB_RETRY_BACKOFF_SEC = 0.15

_RETRY_ERRORS = (
    psycopg.OperationalError,
    psycopg.InterfaceError,
)

T = TypeVar("T")


def database_configured() -> bool:
    return bool(os.getenv("DATABASE_URL", "").strip())


def _log_connection_target(url: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or "?"
    port = parsed.port or 5432
    user = parsed.username or "?"
    logger.info("PostgreSQL target: %s:%s (user=%s)", host, port, user)
    if "pooler.supabase.com" in host.lower():
        if port != 6543:
            logger.warning(
                "Supabase pooler на порту %s — для transaction mode нужен порт 6543",
                port,
            )
        if user == "postgres":
            logger.warning(
                "Supabase pooler: логин должен быть postgres.<project-ref>, не просто postgres",
            )


def require_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL не задан. Добавьте строку подключения Supabase в .env.",
        )
    normalized = _normalize_database_url(url)
    host = (urlparse(normalized).hostname or "").lower()
    if host.endswith(".supabase.co"):
        raise RuntimeError(
            "DATABASE_URL указывает на db.*.supabase.co (Direct). "
            "Используйте Transaction pooler: *.pooler.supabase.com:6543",
        )
    _log_connection_target(normalized)
    return normalized


def _uses_supabase_pgbouncer(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if "pooler.supabase.com" not in host:
        return False
    if parsed.port == 6543:
        return True
    return "pgbouncer=true" in (parsed.query or "").lower()


def _normalize_database_url(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    changed = False

    if "sslmode" not in params:
        params["sslmode"] = ["require"]
        changed = True
    if sys.platform == "win32" and "gssencmode" not in params:
        params["gssencmode"] = ["disable"]
        changed = True

    if not changed:
        return url
    query = urlencode({key: values[0] for key, values in params.items()})
    return urlunparse(parsed._replace(query=query))


def _connection_kwargs(conninfo: str) -> dict:
    kwargs: dict = {
        "row_factory": dict_row,
        "connect_timeout": CONNECT_TIMEOUT_SEC,
        "autocommit": False,
    }
    if _uses_supabase_pgbouncer(conninfo):
        kwargs["prepare_threshold"] = None
    return kwargs


def _ensure_conn_params() -> tuple[str, dict]:
    global _conninfo, _conn_kwargs
    if _conninfo is None:
        _conninfo = require_database_url()
        _conn_kwargs = _connection_kwargs(_conninfo)
    return _conninfo, _conn_kwargs


def reset_pool() -> None:
    reset_pg_state()


def reset_pg_state() -> None:
    """Сбросить кэш параметров подключения (после reload / stop)."""
    global _conninfo, _conn_kwargs
    _conninfo = None
    _conn_kwargs = None


@contextmanager
def db_cursor(*, commit: bool = True) -> Iterator[psycopg.Cursor]:
    conninfo, kwargs = _ensure_conn_params()
    conn = psycopg.connect(conninfo, **kwargs)
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_db(
    callback: Callable[[psycopg.Cursor], T],
    *,
    commit: bool = True,
) -> T:
    last_error: Exception | None = None
    for attempt in range(DB_RETRY_ATTEMPTS):
        try:
            with db_cursor(commit=commit) as cur:
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
            time.sleep(DB_RETRY_BACKOFF_SEC * (attempt + 1))
    if last_error:
        raise last_error
    raise RuntimeError("run_db finished without result")


def run_auth_db(callback: Callable[[psycopg.Cursor], T]) -> T:
    return run_db(callback)


def ping_database() -> bool:
    if not database_configured():
        return False
    try:
        run_db(lambda cur: cur.execute("SELECT 1"), commit=False)
        return True
    except Exception as exc:
        logger.warning("PostgreSQL ping failed: %s", exc)
        return False


def close_pool() -> None:
    reset_pg_state()


def startup_warm() -> bool:
    return ping_database()
