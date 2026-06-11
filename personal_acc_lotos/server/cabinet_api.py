import requests

from _lib_path import ensure_lib_path
from abonement_serializer import serialize_abonement, serialize_usage_visit
from client_cache import (
    clear_client_data_caches,
    fetch_abonement_usage_visits,
    fetch_cabinet_data,
    get_cached_cabinet,
    set_cached_cabinet,
)
from miniapp_config import MiniAppConfig
from record_serializer import serialize_record, service_titles, staff_name
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from utils import storage  # noqa: E402
from utils.phone import format_phone_display  # noqa: E402
from yclients.formatters_cabinet import _client_name  # noqa: E402
from utils.dates import format_date_short  # noqa: E402

from auth_service import AuthError  # noqa: E402


def _serialize_abonements(raw_items: list[dict]) -> list[dict]:
    return [serialize_abonement(item) for item in raw_items]


def _serialize_visit(visit: dict) -> dict:
    return {
        "date": format_date_short(visit.get("date", "")),
        "service": service_titles(visit),
        "staff": staff_name(visit),
    }


def load_cabinet(
    vk_user_id: int,
    config: MiniAppConfig,
    *,
    force_refresh: bool = False,
) -> dict:
    if not force_refresh:
        cached = get_cached_cabinet(vk_user_id)
        if cached is not None:
            return cached

    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    if force_refresh:
        clear_client_data_caches(
            vk_user_id,
            phone=phone,
            company_id=config.yclients_company_id,
        )

    yclients = create_yclients_client(config)
    try:
        data = fetch_cabinet_data(yclients, phone, use_cache=not force_refresh)
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

    usage_visits = [
        serialize_usage_visit(visit)
        for visit in fetch_abonement_usage_visits(
            yclients,
            phone,
            limit=5,
            use_cache=not force_refresh,
        )
    ]

    payload = {
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
        "abonements": _serialize_abonements(data.abonements),
        "abonementUsageVisits": usage_visits,
        "upcomingRecords": [serialize_record(record) for record in data.upcoming_records],
        "recentVisits": [_serialize_visit(visit) for visit in data.recent_visits],
    }
    set_cached_cabinet(vk_user_id, payload)
    return payload
