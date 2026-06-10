import sys
from pathlib import Path

import requests

from abonement_serializer import serialize_abonement, serialize_usage_visit
from miniapp_config import MiniAppConfig
from record_serializer import serialize_record, service_titles, staff_name
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
from utils.phone import format_phone_display  # noqa: E402
from yclients.formatters_cabinet import _client_name  # noqa: E402
from utils.dates import format_date_short  # noqa: E402

from auth_service import AuthError  # noqa: E402


def _serialize_visit(visit: dict) -> dict:
    return {
        "date": format_date_short(visit.get("date", "")),
        "service": service_titles(visit),
        "staff": staff_name(visit),
    }


def load_cabinet(vk_user_id: int, config: MiniAppConfig) -> dict:
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
            "По этому номеру нет карточки в студии. "
            f"Если вы ещё не записывались — оформите первую запись онлайн: {config.yclients_booking_url}",
        ) from None

    profile = data.profile
    client_name = _client_name(profile)

    usage_visits: list[dict] = []
    try:
        usage_visits = [
            serialize_usage_visit(visit)
            for visit in yclients.get_abonement_usage_visits(phone, limit=5)
        ]
    except Exception:
        pass

    return {
        "profile": {
            "name": client_name,
            "phone": phone,
            "phoneDisplay": format_phone_display(phone),
            "visits": profile.get("visits") or 0,
            "spent": profile.get("spent") or 0,
            "discount": profile.get("discount") or 0,
            "firstVisitDate": format_date_short(profile.get("first_visit_date") or "")
            if profile.get("first_visit_date")
            else None,
            "lastVisitDate": format_date_short(profile.get("last_visit_date") or "")
            if profile.get("last_visit_date")
            else None,
        },
        "abonements": [serialize_abonement(item) for item in data.abonements],
        "abonementUsageVisits": usage_visits,
        "upcomingRecords": [serialize_record(record) for record in data.upcoming_records],
        "recentVisits": [_serialize_visit(visit) for visit in data.recent_visits],
    }
