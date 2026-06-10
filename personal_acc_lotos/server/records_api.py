from datetime import datetime

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

from utils import storage  # noqa: E402
from auth_service import AuthError  # noqa: E402

VALID_FILTERS = {"all", "upcoming", "past"}


def _load_profile(vk_user_id: int, config: MiniAppConfig) -> tuple[str, dict]:
    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    try:
        profile = yclients.find_client_by_phone(phone)
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

    if not profile:
        raise AuthError(
            "client_not_found",
            "По этому номеру нет карточки в студии.",
        )

    return phone, profile


def load_records(vk_user_id: int, record_filter: str, config: MiniAppConfig) -> dict:
    if record_filter not in VALID_FILTERS:
        raise AuthError("invalid_filter", "Некорректный фильтр записей.")

    _, profile = _load_profile(vk_user_id, config)
    yclients = create_yclients_client(config)
    now = datetime.now()

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

    serialized = [
        serialize_record(record, now=now)
        for record in raw_records
        if record.get("id")
    ]
    upcoming = [item for item in serialized if item["isUpcoming"]]
    past = [item for item in serialized if not item["isUpcoming"]]

    upcoming.sort(key=lambda item: f"{item.get('date') or ''} {item.get('time') or ''}")
    past.sort(key=lambda item: f"{item.get('date') or ''} {item.get('time') or ''}", reverse=True)
    all_records = upcoming + past

    if record_filter == "upcoming":
        records = upcoming
    elif record_filter == "past":
        records = past
    else:
        records = all_records

    return {
        "filter": record_filter,
        "records": records,
        "counts": {
            "all": len(all_records),
            "upcoming": len(upcoming),
            "past": len(past),
        },
    }


def cancel_record(vk_user_id: int, record_id: int, config: MiniAppConfig) -> dict:
    _, profile = _load_profile(vk_user_id, config)
    yclients = create_yclients_client(config)
    now = datetime.now()

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

    return {
        "success": True,
        "message": "Запись отменена.",
        "record": serialized,
    }
