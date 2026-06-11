import requests

from miniapp_config import MiniAppConfig
from schedule_cache import extract_schedule_filters, fetch_schedule_activities
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

from auth_service import AuthError  # noqa: E402


def load_schedule_filters(config: MiniAppConfig) -> dict:
    yclients = create_yclients_client(config)

    try:
        activities = fetch_schedule_activities(yclients)
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

    return extract_schedule_filters(activities)
