import requests

from _lib_path import ensure_lib_path
from miniapp_config import MiniAppConfig
from record_serializer import serialize_record
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from client_cache import (  # noqa: E402
    clear_client_data_caches,
    fetch_cabinet_data,
    get_cached_records,
    invalidate_client_cache,
    set_cached_records,
)
from utils import storage  # noqa: E402
from utils.dates import studio_now  # noqa: E402
from auth_service import AuthError  # noqa: E402

VALID_FILTERS = {"all", "upcoming", "past"}


def _build_records_bundle(serialized: list[dict]) -> dict:
    upcoming = [item for item in serialized if item["isUpcoming"]]
    past = [item for item in serialized if not item["isUpcoming"]]

    upcoming.sort(key=lambda item: f"{item.get('date') or ''} {item.get('time') or ''}")
    past.sort(
        key=lambda item: f"{item.get('date') or ''} {item.get('time') or ''}",
        reverse=True,
    )
    all_records = upcoming + past

    return {
        "counts": {
            "all": len(all_records),
            "upcoming": len(upcoming),
            "past": len(past),
        },
        "filters": {
            "all": all_records,
            "upcoming": upcoming,
            "past": past,
        },
    }


def _records_response(record_filter: str, bundle: dict) -> dict:
    return {
        "filter": record_filter,
        "records": bundle["filters"][record_filter],
        "counts": bundle["counts"],
    }


def _fetch_records_bundle(
    vk_user_id: int,
    config: MiniAppConfig,
    *,
    use_cache: bool = True,
) -> dict:
    if use_cache:
        cached = get_cached_records(vk_user_id)
        if cached is not None:
            return cached

    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    try:
        cabinet = fetch_cabinet_data(yclients, phone, use_cache=use_cache)
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

    now = studio_now()
    try:
        raw_records = yclients.get_client_records(cabinet.profile["id"])
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

    serialized = [
        serialize_record(record, now=now)
        for record in raw_records
        if record.get("id")
    ]
    bundle = _build_records_bundle(serialized)
    set_cached_records(vk_user_id, bundle)
    return bundle


def load_records(
    vk_user_id: int,
    record_filter: str,
    config: MiniAppConfig,
    *,
    force_refresh: bool = False,
) -> dict:
    if record_filter not in VALID_FILTERS:
        raise AuthError("invalid_filter", "Некорректный фильтр записей.")

    if force_refresh:
        phone = storage.get_phone(vk_user_id)
        if phone:
            clear_client_data_caches(
                vk_user_id,
                phone=phone,
                company_id=config.yclients_company_id,
            )

    bundle = _fetch_records_bundle(
        vk_user_id,
        config,
        use_cache=not force_refresh,
    )
    return _records_response(record_filter, bundle)


def cancel_record(vk_user_id: int, record_id: int, config: MiniAppConfig) -> dict:
    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    try:
        cabinet = fetch_cabinet_data(yclients, phone, use_cache=False)
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

    profile = cabinet.profile
    now = studio_now()

    try:
        raw_records = yclients.get_client_records(profile["id"])
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

    raw_record = next((item for item in raw_records if item.get("id") == record_id), None)
    if not raw_record:
        raise AuthError("record_not_found", "Запись не найдена.")

    serialized = serialize_record(raw_record, now=now)
    if not serialized["canCancel"]:
        raise AuthError(
            "record_not_cancelable",
            "Эту запись нельзя отменить — занятие уже прошло или отменено.",
        )

    try:
        yclients.delete_record(record_id)
    except YClientsError as error:
        raise AuthError("cancel_failed", str(error)) from error
    except requests.RequestException:
        raise AuthError(
            "service_unavailable",
            "Не удалось связаться с YClients. Проверьте интернет и попробуйте снова.",
        ) from None

    invalidate_client_cache(
        vk_user_id=vk_user_id,
        phone=phone,
        company_id=config.yclients_company_id,
    )

    return {
        "success": True,
        "message": "Запись отменена.",
        "record": serialized,
    }
