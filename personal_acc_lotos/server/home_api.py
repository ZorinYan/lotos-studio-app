import sys
from pathlib import Path

import requests

from abonement_serializer import serialize_abonement
from home_alerts import build_home_alerts
from miniapp_config import MiniAppConfig
from record_serializer import serialize_record
from rebook_api import rebook_preview
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

BOT_ROOT = Path(__file__).resolve().parent.parent.parent / "lotos_vk_bot"
if str(BOT_ROOT) not in sys.path:
    sys.path.insert(0, str(BOT_ROOT))

from services.cabinet import CabinetService  # noqa: E402
from utils import storage  # noqa: E402

from auth_service import AuthError  # noqa: E402


def load_home(vk_user_id: int, config: MiniAppConfig) -> dict:
    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    service = CabinetService(yclients)
    try:
        data = service.load(phone)
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

    return {
        "studioName": config.studio_name,
        "abonement": primary_abonement,
        "nextRecord": next_record,
        "alerts": build_home_alerts(primary_abonement),
        "rebook": rebook_preview(vk_user_id, config),
    }
