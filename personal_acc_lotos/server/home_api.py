import requests

from _lib_path import ensure_lib_path
from abonement_serializer import serialize_abonement
from home_alerts import build_home_alerts
from miniapp_config import MiniAppConfig
from record_serializer import serialize_record
from client_cache import fetch_cabinet_data, get_cached_home, set_cached_home
from rebook_api import rebook_preview
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from utils import storage  # noqa: E402

from auth_service import AuthError  # noqa: E402


def load_home(vk_user_id: int, config: MiniAppConfig) -> dict:
    cached = get_cached_home(vk_user_id)
    if cached is not None:
        return cached

    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    try:
        data = fetch_cabinet_data(yclients, phone)
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
    except ValueError:
        raise AuthError(
            "client_not_found",
            "По этому номеру нет карточки в студии.",
        ) from None

    abonements = [serialize_abonement(item) for item in data.abonements]
    primary_abonement = abonements[0] if abonements else None
    next_record = (
        serialize_record(data.upcoming_records[0])
        if data.upcoming_records
        else None
    )

    payload = {
        "studioName": config.studio_name,
        "abonement": primary_abonement,
        "nextRecord": next_record,
        "alerts": build_home_alerts(primary_abonement),
        "rebook": rebook_preview(vk_user_id, config),
    }
    set_cached_home(vk_user_id, payload)
    return payload
