"""Адаптер к локальному YClientsClient (server/lib)."""

from dataclasses import dataclass

from _lib_path import ensure_lib_path
from miniapp_config import MiniAppConfig, load_config

ensure_lib_path()

from yclients import YClientsClient, YClientsError, YClientsNetworkError, YClientsPermissionError  # noqa: E402


@dataclass(frozen=True)
class BotConfigAdapter:
    yclients_partner_token: str
    yclients_user_token: str
    yclients_company_id: int
    studio_name: str
    yclients_booking_url: str
    vk_token: str = ""
    reminder_offsets_minutes: tuple[int, ...] = ()
    reminder_check_interval_sec: int = 120


def create_yclients_client(config: MiniAppConfig | None = None) -> YClientsClient:
    cfg = config or load_config()
    adapter = BotConfigAdapter(
        yclients_partner_token=cfg.yclients_partner_token,
        yclients_user_token=cfg.yclients_user_token,
        yclients_company_id=cfg.yclients_company_id,
        studio_name=cfg.studio_name,
        yclients_booking_url=cfg.yclients_booking_url,
    )
    client = YClientsClient(adapter)  # type: ignore[arg-type]
    # Игнорируем системный SOCKS/HTTP-прокси (VPN) — иначе requests падает без PySocks.
    client.session.trust_env = False
    return client


__all__ = [
    "YClientsError",
    "YClientsNetworkError",
    "YClientsPermissionError",
    "create_yclients_client",
]
