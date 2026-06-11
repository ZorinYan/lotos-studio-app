"""Периодический ping /health — не даёт Free Web Service на Render заснуть."""

from __future__ import annotations

import logging
import os
import threading
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SEC = 540


def _collect_base_urls() -> list[str]:
    urls: list[str] = []
    primary = os.getenv("KEEPALIVE_URL") or os.getenv("RENDER_EXTERNAL_URL")
    if primary:
        urls.append(primary.strip().rstrip("/"))

    extra = os.getenv("KEEPALIVE_EXTRA_URLS", "")
    for part in extra.split(","):
        part = part.strip().rstrip("/")
        if part and part not in urls:
            urls.append(part)
    return urls


class KeepAliveService:
    def __init__(self, base_urls: list[str], interval_sec: int) -> None:
        self.urls = [f"{url}/health" for url in base_urls]
        self.interval_sec = max(interval_sec, 300)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, name="keepalive", daemon=True)
        self._thread.start()
        logger.info(
            "Keep-alive: %s каждые %s сек",
            ", ".join(self.urls),
            self.interval_sec,
        )

    def stop(self) -> None:
        self._stop.set()

    def _ping(self, url: str) -> None:
        request = Request(url, method="GET")
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                logger.warning("Keep-alive %s: HTTP %s", url, response.status)

    def _loop(self) -> None:
        self._stop.wait(30)
        while not self._stop.is_set():
            for url in self.urls:
                if self._stop.is_set():
                    break
                try:
                    self._ping(url)
                except URLError as error:
                    logger.warning("Keep-alive %s: %s", url, error)
                except Exception:
                    logger.exception("Keep-alive %s", url)
            self._stop.wait(self.interval_sec)


def start_from_env() -> KeepAliveService | None:
    if os.getenv("KEEPALIVE_ENABLED", "true").strip().lower() in {"0", "false", "no", "off"}:
        return None

    urls = _collect_base_urls()
    if not urls:
        return None

    interval = int(os.getenv("KEEPALIVE_INTERVAL_SEC", str(DEFAULT_INTERVAL_SEC)))
    service = KeepAliveService(urls, interval)
    service.start()
    return service
