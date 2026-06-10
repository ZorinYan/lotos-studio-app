from datetime import date, timedelta

import requests

from miniapp_config import MiniAppConfig
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

from auth_service import AuthError  # noqa: E402


def load_schedule_filters(config: MiniAppConfig) -> dict:
    yclients = create_yclients_client(config)
    trainers: dict[int, str] = {}
    services: dict[int, str] = {}
    service_titles: dict[str, str] = {}

    try:
        for offset in range(14):
            target = date.today() + timedelta(days=offset)
            activities = yclients.get_activities_for_date(target)
            for activity in activities:
                staff = activity.get("staff") or {}
                staff_id = staff.get("id")
                if staff_id:
                    name = (staff.get("name") or staff.get("specialization") or "Тренер").strip()
                    trainers[int(staff_id)] = name

                service = activity.get("service") or {}
                service_id = service.get("id")
                title = str(service.get("title") or "Занятие").strip()
                if service_id:
                    services[int(service_id)] = title
                elif title:
                    service_titles[title.lower()] = title
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

    trainer_list = [
        {"id": staff_id, "name": name}
        for staff_id, name in sorted(trainers.items(), key=lambda item: item[1].lower())
    ]
    service_list = [
        {"id": service_id, "title": title}
        for service_id, title in sorted(services.items(), key=lambda item: item[1].lower())
    ]
    for title in sorted(service_titles.values(), key=str.lower):
        if title not in {item["title"] for item in service_list}:
            service_list.append({"id": None, "title": title})

    return {
        "trainers": trainer_list,
        "services": service_list,
    }
