import requests

from _lib_path import ensure_lib_path
from abonement_serializer import pick_primary_abonement, serialize_abonement
from client_cache import fetch_abonements_fresh
from home_alerts import build_home_alerts
from miniapp_config import MiniAppConfig
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from utils import storage  # noqa: E402

from auth_service import AuthError  # noqa: E402


def load_abonements(vk_user_id: int, config: MiniAppConfig) -> dict:
    """Остаток занятий на абонементе — всегда напрямую из YClients, без кэша."""
    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    try:
        raw_items = fetch_abonements_fresh(yclients, phone)
    except YClientsPermissionError:
        raise AuthError(
            "service_unavailable",
            "Сервис временно недоступен. Обратитесь к администратору студии.",
        ) from None
    except YClientsError as error:
        raise AuthError("fetch_error", str(error)) from error
    except requests.RequestException:
        raise AuthError(
            "service_unavailable",
            "Не удалось связаться с YClients. Проверьте интернет и попробуйте снова.",
        ) from None

    abonements = [serialize_abonement(item) for item in raw_items]
    primary = pick_primary_abonement(abonements)

    return {
        "abonements": abonements,
        "primary": primary,
        "alerts": build_home_alerts(primary),
    }


def merge_fresh_abonements(payload: dict, vk_user_id: int, config: MiniAppConfig) -> dict:
    """Подмешивает свежий остаток абонемента в уже собранный ответ home/cabinet."""
    try:
        fresh = load_abonements(vk_user_id, config)
    except AuthError:
        return payload

    merged = {**payload, "abonements": fresh["abonements"]}
    if "abonement" in payload:
        primary = fresh["primary"]
        merged["abonement"] = primary
        merged["alerts"] = fresh.get("alerts") or build_home_alerts(primary)
    return merged
