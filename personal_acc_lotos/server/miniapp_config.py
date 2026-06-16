import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_SERVER_DIR = Path(__file__).resolve().parent


def _load_env_files() -> None:
    # .env важнее переменных терминала — иначе старые YCLIENTS_* из shell перекрывают файл.
    for env_file in (_SERVER_DIR.parent / ".env", _SERVER_DIR / ".env"):
        if env_file.exists():
            load_dotenv(env_file, override=True)


_load_env_files()


def _clean_token(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _optional_float(value: str) -> float | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


@dataclass(frozen=True)
class MiniAppConfig:
    yclients_partner_token: str
    yclients_user_token: str
    yclients_company_id: int
    studio_name: str
    yclients_booking_url: str
    cors_origins: tuple[str, ...]
    vk_app_secret: str
    vk_group_token: str
    vk_service_token: str
    vk_group_id: int
    studio_address: str
    studio_hours: str
    studio_phone: str
    studio_latitude: float | None
    studio_longitude: float | None
    skip_vk_sign: bool


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

    vk_app_secret = os.getenv("VK_APP_SECRET", "")
    skip_vk_sign = os.getenv("SKIP_VK_SIGN", "").lower() in ("1", "true", "yes")
    skip_vk_sign_env = os.getenv("SKIP_VK_SIGN", "").strip().lower()
    if skip_vk_sign_env in ("0", "false", "no"):
        skip_vk_sign = False
    elif not vk_app_secret:
        skip_vk_sign = True
    elif any("localhost" in origin or "127.0.0.1" in origin for origin in origins):
        skip_vk_sign = True

    return MiniAppConfig(
        yclients_partner_token=partner_token,
        yclients_user_token=user_token,
        yclients_company_id=int(os.getenv("YCLIENTS_COMPANY_ID", "0")),
        studio_name=os.getenv("STUDIO_NAME", "Лотос"),
        yclients_booking_url=os.getenv(
            "YCLIENTS_BOOKING_URL", "https://n1996926.yclients.com/"
        ),
        cors_origins=origins,
        vk_app_secret=vk_app_secret,
        vk_group_token=_clean_token(os.getenv("VK_GROUP_TOKEN", "")),
        vk_service_token=_clean_token(os.getenv("VK_SERVICE_TOKEN", "")),
        vk_group_id=int(os.getenv("VK_GROUP_ID", "0") or "0"),
        studio_address=os.getenv("STUDIO_ADDRESS", ""),
        studio_hours=os.getenv("STUDIO_HOURS", ""),
        studio_phone=os.getenv("STUDIO_PHONE", ""),
        studio_latitude=_optional_float(os.getenv("STUDIO_LATITUDE", "")),
        studio_longitude=_optional_float(os.getenv("STUDIO_LONGITUDE", "")),
        skip_vk_sign=skip_vk_sign,
    )
