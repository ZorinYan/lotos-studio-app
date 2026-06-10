import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_BOT_ENV = Path(__file__).resolve().parent.parent.parent / "lotos_vk_bot" / ".env"
_LOCAL_ENV = Path(__file__).resolve().parent / ".env"

if _BOT_ENV.exists():
    load_dotenv(_BOT_ENV)
if _LOCAL_ENV.exists():
    load_dotenv(_LOCAL_ENV, override=True)


@dataclass(frozen=True)
class MiniAppConfig:
    yclients_partner_token: str
    yclients_user_token: str
    yclients_company_id: int
    studio_name: str
    yclients_booking_url: str
    cors_origins: tuple[str, ...]


def load_config() -> MiniAppConfig:
    partner_token = os.getenv("YCLIENTS_PARTNER_TOKEN", "")
    user_token = os.getenv("YCLIENTS_USER_TOKEN", "")

    missing = []
    if not partner_token:
        missing.append("YCLIENTS_PARTNER_TOKEN")
    if not user_token:
        missing.append("YCLIENTS_USER_TOKEN")

    if missing:
        raise RuntimeError("Заполните переменные в .env: " + ", ".join(missing))

    raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())

    return MiniAppConfig(
        yclients_partner_token=partner_token,
        yclients_user_token=user_token,
        yclients_company_id=int(os.getenv("YCLIENTS_COMPANY_ID", "0")),
        studio_name=os.getenv("STUDIO_NAME", "Лотос"),
        yclients_booking_url=os.getenv(
            "YCLIENTS_BOOKING_URL", "https://n1996926.yclients.com/"
        ),
        cors_origins=origins,
    )
