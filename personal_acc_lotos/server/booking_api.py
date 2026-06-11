from datetime import date, timedelta

import requests

from _lib_path import ensure_lib_path
from miniapp_config import MiniAppConfig
from schedule_api import _serialize_activity
from yclients_adapter import (
    YClientsError,
    YClientsPermissionError,
    create_yclients_client,
)

ensure_lib_path()

from utils import storage  # noqa: E402
from utils.phone import format_phone_display, normalize_phone  # noqa: E402
from yclients.client import YClientsClient  # noqa: E402

from booking_rules import (
    assert_abonement_booking_allowed,
    has_usable_abonement_for_activity,
    requires_abonement,
)
from rebook_api import remember_booking_from_activity
from client_cache import invalidate_client_cache
from schedule_cache import invalidate_schedule_cache

from auth_service import AuthError  # noqa: E402


def is_first_time_client(profile: dict | None) -> bool:
    if not profile:
        return True
    if profile.get("first_visit_date"):
        return False
    for key in ("success_visits_count", "visits_count"):
        try:
            if int(profile.get(key) or 0) > 0:
                return False
        except (TypeError, ValueError):
            pass
    try:
        if float(profile.get("spent") or 0) > 0:
            return False
    except (TypeError, ValueError):
        pass
    return True


def _trial_salon_service_id(activity: dict) -> int | None:
    service = activity.get("service") or {}
    trial = service.get("trial_settings") or {}
    if not isinstance(trial, dict):
        return None
    raw = trial.get("salon_service_id")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _split_name(raw_name: str) -> tuple[str, str]:
    parts = raw_name.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _resolve_fullname(vk_user_id: int, phone: str, yclients) -> tuple[str, str]:
    try:
        client = yclients.find_client_by_phone(phone)
        if client:
            name = str(client.get("name", "")).strip()
            surname = str(client.get("surname", "")).strip()
            if name:
                return name, surname
    except (YClientsError, YClientsPermissionError, requests.RequestException):
        pass

    stored = storage.get_user_entry(vk_user_id).get("client_name", "")
    parts = str(stored).strip().split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    if parts:
        return parts[0], ""
    return "Клиент", ""


def _resolve_guest_identity(
    phone: str,
    raw_name: str,
    yclients,
) -> tuple[str, str, bool, dict | None]:
    normalized = normalize_phone(phone)
    if not normalized:
        raise AuthError("invalid_phone", "Не удалось распознать номер телефона.")

    name = raw_name.strip()
    if not name:
        raise AuthError("invalid_name", "Укажите имя для записи.")

    try:
        profile = yclients.find_client_by_phone(normalized)
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

    is_trial = is_first_time_client(profile)
    if profile and not is_trial:
        raise AuthError(
            "existing_client_login_required",
            "Вы уже были в студии. Войдите по номеру телефона — запись доступна только после авторизации.",
        )

    fullname, surname = _split_name(name)
    if not fullname:
        raise AuthError("invalid_name", "Укажите имя для записи.")
    return fullname, surname, True, profile


def _find_activity(yclients, activity_id: int, activity_date: str | None) -> dict | None:
    if activity_date:
        try:
            target = date.fromisoformat(activity_date)
        except ValueError:
            target = None
        if target:
            for activity in yclients.get_activities_for_date(target):
                if activity.get("id") == activity_id:
                    return activity

    for offset in range(14):
        target = date.today() + timedelta(days=offset)
        for activity in yclients.get_activities_for_date(target):
            if activity.get("id") == activity_id:
                return activity
    return None


def book_schedule_class(
    vk_user_id: int,
    activity_id: int,
    activity_date: str | None,
    config: MiniAppConfig,
    *,
    guest_phone: str | None = None,
    guest_name: str | None = None,
) -> dict:
    yclients = create_yclients_client(config)
    is_trial = False
    salon_service_id: int | None = None

    if guest_phone is not None:
        normalized_phone = normalize_phone(guest_phone)
        if not normalized_phone:
            raise AuthError("invalid_phone", "Не удалось распознать номер телефона.")
        fullname, surname, is_trial, profile = _resolve_guest_identity(
            guest_phone,
            guest_name or "",
            yclients,
        )
        phone = normalized_phone
        display_name = guest_name.strip() if guest_name else fullname
        storage.update_user_entry(
            vk_user_id,
            phone=phone,
            client_name=display_name,
        )
    else:
        phone = storage.get_phone(vk_user_id)
        if not phone:
            raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")
        fullname, surname = _resolve_fullname(vk_user_id, phone, yclients)
        try:
            profile = yclients.find_client_by_phone(phone)
        except (YClientsError, YClientsPermissionError, requests.RequestException):
            profile = None
        is_trial = is_first_time_client(profile)

    try:
        activity = _find_activity(yclients, activity_id, activity_date)
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

    if not activity:
        raise AuthError("activity_not_found", "Занятие не найдено или уже прошло.")

    if not YClientsClient.activity_has_free_spots(activity):
        raise AuthError("activity_full", "На это занятие больше нет свободных мест.")

    if is_trial:
        salon_service_id = _trial_salon_service_id(activity)
        if requires_abonement(activity) and salon_service_id is None:
            raise AuthError(
                "trial_unavailable",
                "Пробная запись на это занятие недоступна. Обратитесь к администратору студии.",
            )
        comment = "Пробное занятие · мини-приложение Lotos"
    else:
        assert_abonement_booking_allowed(yclients, phone, activity)
        comment = "Запись через мини-приложение Lotos"

    try:
        yclients.book_activity(
            activity_id,
            phone,
            fullname,
            surname,
            comment=comment,
            salon_service_id=salon_service_id,
        )
    except YClientsError as error:
        raise AuthError("booking_failed", str(error)) from error
    except requests.RequestException:
        raise AuthError(
            "service_unavailable",
            "Не удалось связаться с YClients. Проверьте интернет и попробуйте снова.",
        ) from None

    remember_booking_from_activity(vk_user_id, activity)
    invalidate_schedule_cache(config.yclients_company_id)
    invalidate_client_cache(
        vk_user_id=vk_user_id,
        phone=phone,
        company_id=config.yclients_company_id,
    )
    serialized = _serialize_activity(activity)
    message = (
        "Вы записаны на пробное занятие."
        if is_trial
        else "Вы успешно записаны на занятие."
    )
    return {
        "success": True,
        "isTrial": is_trial,
        "phoneDisplay": format_phone_display(phone),
        "class": serialized,
        "message": message,
    }


def check_guest_booking(phone: str, config: MiniAppConfig) -> dict:
    normalized = normalize_phone(phone)
    if not normalized:
        raise AuthError("invalid_phone", "Не удалось распознать номер телефона.")

    yclients = create_yclients_client(config)
    try:
        profile = yclients.find_client_by_phone(normalized)
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

    is_trial = is_first_time_client(profile)
    if profile and not is_trial:
        return {
            "allowed": False,
            "reason": "login_required",
            "isFirstVisit": False,
            "message": (
                "Вы уже были в студии. Войдите по номеру телефона — "
                "запись доступна только после авторизации."
            ),
        }

    return {
        "allowed": True,
        "reason": None,
        "isFirstVisit": is_trial,
        "message": None,
    }


def check_booking_eligibility(
    vk_user_id: int,
    activity_id: int,
    activity_date: str | None,
    config: MiniAppConfig,
) -> dict:
    phone = storage.get_phone(vk_user_id)
    if not phone:
        raise AuthError("not_authenticated", "Сначала войдите по номеру телефона.")

    yclients = create_yclients_client(config)
    try:
        profile = yclients.find_client_by_phone(phone)
    except (YClientsError, YClientsPermissionError, requests.RequestException):
        profile = None

    is_trial = is_first_time_client(profile)

    try:
        activity = _find_activity(yclients, activity_id, activity_date)
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

    if not activity:
        raise AuthError("activity_not_found", "Занятие не найдено или уже прошло.")

    needs_abonement = requires_abonement(activity)
    has_abonement = (
        has_usable_abonement_for_activity(yclients, phone, activity)
        if needs_abonement
        else True
    )
    trial_available = _trial_salon_service_id(activity) is not None

    can_book = True
    reason = None
    message = None

    if is_trial:
        if needs_abonement and not trial_available:
            can_book = False
            reason = "trial_unavailable"
            message = "Пробная запись на это занятие недоступна. Обратитесь к администратору студии."
    elif needs_abonement and not has_abonement:
        can_book = False
        reason = "abonement_required"
        message = (
            "Запись на это занятие только по абонементу. "
            "Оформите или продлите абонемент в студии."
        )

    return {
        "canBook": can_book,
        "isTrial": is_trial,
        "requiresAbonement": needs_abonement,
        "hasAbonement": has_abonement,
        "reason": reason,
        "message": message,
    }
