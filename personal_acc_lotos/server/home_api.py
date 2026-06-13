import requests

from _lib_path import ensure_lib_path
from abonement_serializer import pick_primary_abonement, serialize_abonement
from abonement_api import merge_fresh_abonements
from booking_api import is_first_time_client
from cabinet_api import _serialize_visit, _serialize_visit_history
from home_alerts import build_home_alerts
from miniapp_config import MiniAppConfig
from record_serializer import is_upcoming, serialize_record
from rhythm_plan import build_inactive_hint_detail, build_rhythm_plan
from visit_stats import VISIT_RECORDS_DAYS_BACK, VISIT_RECORDS_LIMIT, build_visit_stats
from client_cache import (
    clear_client_data_caches,
    fetch_abonements_fresh,
    fetch_cabinet_data,
    get_cached_home,
    set_cached_home,
)
from rebook_api import rebook_preview
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from utils import storage  # noqa: E402

from auth_service import AuthError  # noqa: E402


def load_home(
    vk_user_id: int,
    config: MiniAppConfig,
    *,
    force_refresh: bool = False,
) -> dict:
    if not force_refresh:
        cached = get_cached_home(vk_user_id)
        if cached is not None:
            return merge_fresh_abonements(cached, vk_user_id, config)

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
            "По этому номеру нет карточки в студии.",
        ) from None

    abonements = [
        serialize_abonement(item)
        for item in fetch_abonements_fresh(yclients, phone)
    ]
    primary_abonement = pick_primary_abonement(abonements)
    next_record = None
    for raw in data.upcoming_records:
        if is_upcoming(raw):
            next_record = serialize_record(raw)
            break

    visit_history = []
    recent_visits = []
    try:
        raw_records = yclients.get_client_records(
            data.profile["id"],
            days_back=VISIT_RECORDS_DAYS_BACK,
            count=VISIT_RECORDS_LIMIT,
        )
        visit_stats = build_visit_stats(raw_records)
        visit_history = visit_stats["visitHistory"]
        recent_visits = [
            {
                "dateIso": item.get("dateIso"),
                "service": item.get("service"),
            }
            for item in visit_stats["recentVisits"]
        ]
    except Exception:
        visit_history = [
            entry
            for visit in (data.visit_history or [])
            for entry in [_serialize_visit_history(visit)]
            if entry
        ]
        recent_visits = [
            {
                "dateIso": item.get("dateIso"),
                "service": item.get("service"),
            }
            for visit in (data.recent_visits or [])
            for item in [_serialize_visit(visit)]
        ]

    inactive_detail = build_inactive_hint_detail(visit_history)
    rhythm_plan = None
    try:
        rhythm_plan = build_rhythm_plan(
            vk_user_id,
            phone,
            yclients,
            visit_history=visit_history,
            recent_visits=recent_visits,
            use_cache=not force_refresh,
        )
    except Exception:
        rhythm_plan = None

    payload = {
        "studioName": config.studio_name,
        "abonement": primary_abonement,
        "nextRecord": next_record,
        "alerts": build_home_alerts(
            primary_abonement,
            profile=data.profile,
            inactive_detail=inactive_detail,
        ),
        "rhythmPlan": rhythm_plan,
        "isFirstVisit": is_first_time_client(data.profile),
        "rebook": rebook_preview(vk_user_id, config, force_refresh=force_refresh),
    }
    set_cached_home(vk_user_id, payload)
    return payload
