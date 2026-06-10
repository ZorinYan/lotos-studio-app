import logging
import os
import threading
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SEC = 600


class KeepAliveService:
    """Периодически дергает /health, чтобы Free Web Service на Render не засыпал."""

    def __init__(self, url: str, interval_sec: int) -> None:
        self.url = url.rstrip("/") + "/health"
        self.interval_sec = max(interval_sec, 300)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, name="keepalive", daemon=True)
        self._thread.start()
        logger.info("Keep-alive: %s каждые %s сек", self.url, self.interval_sec)

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        self._stop.wait(30)
        while not self._stop.is_set():
            try:
                request = Request(self.url, method="GET")
                with urlopen(request, timeout=30) as response:
                    if response.status == 200:
                        logger.debug("Keep-alive OK")
                    else:
                        logger.warning("Keep-alive: HTTP %s", response.status)
            except URLError as error:
                logger.warning("Keep-alive ошибка: %s", error)
            except Exception:
                logger.exception("Keep-alive ошибка")
            self._stop.wait(self.interval_sec)


def start_from_env() -> KeepAliveService | None:
    if os.getenv("KEEPALIVE_ENABLED", "true").strip().lower() in {"0", "false", "no", "off"}:
        return None

    url = os.getenv("KEEPALIVE_URL") or os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        return None

    interval = int(os.getenv("KEEPALIVE_INTERVAL_SEC", str(DEFAULT_INTERVAL_SEC)))
    service = KeepAliveService(url, interval)
    service.start()
    return service
