from contextlib import asynccontextmanager
from datetime import date
import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

import psycopg

from auth_service import (
    AuthError,
    check_phone,
    get_boot_state,
    get_auth_status,
    logout,
    set_password,
    verify_name,
    verify_password,
)
from staff_auth_service import (
    StaffAuthError,
    set_staff_password,
    verify_staff_password,
)
from staff_home_api import load_staff_home
from staff_settings_api import load_staff_settings, update_staff_settings
from staff_schedule_api import load_staff_activity_clients
from vk_auth import guard_vk_user, vk_launch_from_header
from booking_api import book_schedule_class, check_booking_eligibility, check_guest_booking
from cabinet_api import load_cabinet
from home_api import load_home
from abonement_api import load_abonements
from records_api import cancel_record, load_records
from reschedule_api import load_reschedule_slots, reschedule_record
from rebook_api import load_rebook_slots
from schedule_api import load_schedule
from schedule_filters_api import load_schedule_filters
from settings_api import load_settings, update_settings
from vk_group_content import load_studio_feed
from miniapp_config import MiniAppConfig, load_config
from _lib_path import ensure_lib_path
from keepalive import KeepAliveService, start_from_env
from runtime_reset import reset_runtime_state

ensure_lib_path()
from utils.dates import studio_today  # noqa: E402

config: MiniAppConfig = load_config()

_keepalive: KeepAliveService | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _keepalive
    from _lib_path import ensure_lib_path

    ensure_lib_path()
    from utils.postgres import close_pool, database_configured  # noqa: E402

    reset_runtime_state()

    if not database_configured():
        raise RuntimeError("DATABASE_URL не задан")

    logger.info("API worker started (runtime state clean)")
    _keepalive = start_from_env()
    yield
    if _keepalive is not None:
        _keepalive.stop()
        _keepalive = None
    close_pool()
    reset_runtime_state()


app = FastAPI(title="Lotos Mini App API", lifespan=lifespan)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _db_unavailable_response() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": {
                "code": "db_unavailable",
                "message": "База данных временно недоступна. Подождите и попробуйте снова.",
            },
        },
    )


@app.exception_handler(psycopg.Error)
async def db_error(_request: Request, _exc: psycopg.Error):
    return _db_unavailable_response()


class VkUserRequest(BaseModel):
    vk_user_id: int = Field(gt=0)


class PhoneRequest(VkUserRequest):
    phone: str = Field(min_length=5, max_length=30)


class VerifyRequest(VkUserRequest):
    phone: str = Field(min_length=11, max_length=11)
    name: str = Field(min_length=1, max_length=120)


class PasswordVerifyRequest(VkUserRequest):
    phone: str = Field(min_length=11, max_length=11)
    password: str = Field(min_length=6, max_length=72)


class PasswordSetRequest(VkUserRequest):
    phone: str = Field(min_length=11, max_length=11)
    password: str = Field(min_length=6, max_length=72)
    password_confirm: str = Field(min_length=6, max_length=72)


class BookScheduleRequest(VkUserRequest):
    activity_id: int = Field(gt=0)
    activity_date: str | None = None
    phone: str | None = None
    name: str | None = None
    surname: str | None = None


class GuestCheckRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=30)


class CancelRecordRequest(VkUserRequest):
    record_id: int = Field(gt=0)


class RescheduleRecordRequest(VkUserRequest):
    record_id: int = Field(gt=0)
    activity_id: int = Field(gt=0)
    activity_date: str | None = None


class SettingsUpdateRequest(VkUserRequest):
    model_config = ConfigDict(populate_by_name=True)

    favorite_staff_id: int | None = None
    favorite_staff_name: str | None = Field(default=None, max_length=120)
    clear_favorite: bool = False
    notifications_enabled: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("notifications_enabled", "notificationsEnabled"),
    )
    color_scheme: str | None = Field(
        default=None,
        pattern="^(light|dark)$",
        validation_alias=AliasChoices("color_scheme", "colorScheme"),
    )
    welcome_banner_seen: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("welcome_banner_seen", "welcomeBannerSeen"),
    )


class SettingsResponse(BaseModel):
    favoriteTrainer: dict | None = None
    notificationsEnabled: bool = False
    colorScheme: str = "light"
    welcomeBannerSeen: bool = False


class StaffSettingsResponse(BaseModel):
    staffName: str | None = None
    phoneDisplay: str | None = None
    colorScheme: str = "light"


class StaffSettingsUpdateRequest(VkUserRequest):
    model_config = ConfigDict(populate_by_name=True)

    color_scheme: str | None = Field(
        default=None,
        pattern="^(light|dark)$",
        validation_alias=AliasChoices("color_scheme", "colorScheme"),
    )


class StaffActivityClientsRequest(VkUserRequest):
    model_config = ConfigDict(populate_by_name=True)

    activity_id: int = Field(gt=0)
    activity_date: str = Field(min_length=10, max_length=10)


def _cfg() -> MiniAppConfig:
    return config


def _handle_staff_auth_error(error: StaffAuthError, *, protected: bool = False) -> HTTPException:
    status = 400
    if protected and error.code in {"not_authenticated"}:
        status = 401
    return HTTPException(
        status_code=status,
        detail={"code": error.code, "message": str(error)},
    )


def _handle_auth_error(error: AuthError, *, protected: bool = False) -> HTTPException:
    status = 400
    if protected and error.code in {"not_authenticated", "client_not_found"}:
        status = 401
    elif error.code in {"service_unavailable", "fetch_error", "yclients_timeout"}:
        status = 503
    return HTTPException(
        status_code=status,
        detail={"code": error.code, "message": str(error)},
    )


def _guard(vk_user_id: int, launch: dict[str, str]) -> None:
    guard_vk_user(vk_user_id, launch, _cfg())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/boot")
def boot(vk_user_id: int, launch: dict[str, str] = Depends(vk_launch_from_header)):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    cfg = _cfg()
    config_payload: dict[str, str | int] = {
        "studioName": cfg.studio_name,
        "bookingUrl": cfg.yclients_booking_url,
        "studioPhone": cfg.studio_phone,
    }
    if cfg.vk_group_id:
        config_payload["vkGroupId"] = cfg.vk_group_id

    status, prefs = get_boot_state(vk_user_id)

    return {
        "config": config_payload,
        "auth": {
            "authenticated": status.authenticated,
            "role": status.role,
            "phone": status.phone,
            "phoneDisplay": status.phone_display,
            "clientName": status.client_name,
            "staffName": status.staff_name,
            "staffId": status.staff_id,
            "specialization": status.specialization,
            "positionTitle": status.position_title,
        },
        "prefs": prefs,
    }


@app.get("/api/config/public")
def public_config() -> dict[str, str | int]:
    cfg = _cfg()
    payload: dict[str, str | int] = {
        "studioName": cfg.studio_name,
        "bookingUrl": cfg.yclients_booking_url,
        "studioPhone": cfg.studio_phone,
    }
    if cfg.vk_group_id:
        payload["vkGroupId"] = cfg.vk_group_id
    return payload


@app.get("/api/auth/status")
def auth_status(vk_user_id: int, launch: dict[str, str] = Depends(vk_launch_from_header)):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    status = get_auth_status(vk_user_id)
    return {
        "authenticated": status.authenticated,
        "role": status.role,
        "phone": status.phone,
        "phoneDisplay": status.phone_display,
        "clientName": status.client_name,
        "staffName": status.staff_name,
        "staffId": status.staff_id,
        "specialization": status.specialization,
        "positionTitle": status.position_title,
    }


@app.post("/api/auth/phone")
def auth_phone(body: PhoneRequest, launch: dict[str, str] = Depends(vk_launch_from_header)):
    _guard(body.vk_user_id, launch)
    try:
        result = check_phone(body.vk_user_id, body.phone, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error) from error

    return {
        "step": result.step,
        "phone": result.phone,
        "accountType": result.account_type,
        "requiresSurname": result.requires_surname,
        "phoneDisplay": result.phone_display,
        "clientName": result.client_name,
        "staffName": result.staff_name,
        "specialization": result.specialization,
        "positionTitle": result.position_title,
    }


@app.post("/api/auth/verify")
def auth_verify(body: VerifyRequest, launch: dict[str, str] = Depends(vk_launch_from_header)):
    _guard(body.vk_user_id, launch)
    try:
        result = verify_name(body.vk_user_id, body.phone, body.name, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error) from error

    return {
        "success": True,
        "phone": result.phone,
        "phoneDisplay": result.phone_display,
        "needsPassword": result.needs_password,
        "clientName": result.client_name,
    }


@app.post("/api/auth/password/verify")
def auth_password_verify(
    body: PasswordVerifyRequest,
    launch: dict[str, str] = Depends(vk_launch_from_header),
):
    _guard(body.vk_user_id, launch)
    try:
        result = verify_password(body.vk_user_id, body.phone, body.password, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error) from error

    return {
        "success": True,
        "authenticated": True,
        "phone": result.phone,
        "phoneDisplay": result.phone_display,
        "clientName": result.client_name,
        "needsPassword": result.needs_password,
    }


@app.post("/api/auth/password/set")
def auth_password_set(
    body: PasswordSetRequest,
    launch: dict[str, str] = Depends(vk_launch_from_header),
):
    _guard(body.vk_user_id, launch)
    if body.password != body.password_confirm:
        raise HTTPException(
            status_code=400,
            detail={"code": "password_mismatch", "message": "Пароли не совпадают."},
        )
    try:
        result = set_password(body.vk_user_id, body.phone, body.password, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error) from error

    return {
        "success": True,
        "authenticated": True,
        "phone": result.phone,
        "phoneDisplay": result.phone_display,
        "clientName": result.client_name,
        "needsPassword": result.needs_password,
    }


@app.post("/api/staff/auth/password/verify")
def staff_auth_password_verify(
    body: PasswordVerifyRequest,
    launch: dict[str, str] = Depends(vk_launch_from_header),
):
    _guard(body.vk_user_id, launch)
    try:
        result = verify_staff_password(body.vk_user_id, body.phone, body.password, _cfg())
    except StaffAuthError as error:
        raise _handle_staff_auth_error(error) from error

    return {
        "success": True,
        "authenticated": True,
        "role": "staff",
        "phone": result.phone,
        "phoneDisplay": result.phone_display,
        "staffName": result.staff_name,
        "staffId": result.staff_id,
        "specialization": result.specialization,
        "positionTitle": result.position_title,
    }


@app.post("/api/staff/auth/password/set")
def staff_auth_password_set(
    body: PasswordSetRequest,
    launch: dict[str, str] = Depends(vk_launch_from_header),
):
    _guard(body.vk_user_id, launch)
    if body.password != body.password_confirm:
        raise HTTPException(
            status_code=400,
            detail={"code": "password_mismatch", "message": "Пароли не совпадают."},
        )
    try:
        result = set_staff_password(body.vk_user_id, body.phone, body.password, _cfg())
    except StaffAuthError as error:
        raise _handle_staff_auth_error(error) from error

    return {
        "success": True,
        "authenticated": True,
        "role": "staff",
        "phone": result.phone,
        "phoneDisplay": result.phone_display,
        "staffName": result.staff_name,
        "staffId": result.staff_id,
        "specialization": result.specialization,
        "positionTitle": result.position_title,
    }


@app.get("/api/staff/home")
def staff_home(vk_user_id: int, launch: dict[str, str] = Depends(vk_launch_from_header)):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    try:
        return load_staff_home(vk_user_id)
    except StaffAuthError as error:
        raise _handle_staff_auth_error(error, protected=True) from error


@app.get("/api/staff/settings", response_model=StaffSettingsResponse)
def staff_settings_get(vk_user_id: int, launch: dict[str, str] = Depends(vk_launch_from_header)):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    try:
        return load_staff_settings(vk_user_id)
    except StaffAuthError as error:
        raise _handle_staff_auth_error(error, protected=True) from error


@app.put("/api/staff/settings", response_model=StaffSettingsResponse)
def staff_settings_put(
    body: StaffSettingsUpdateRequest,
    launch: dict[str, str] = Depends(vk_launch_from_header),
):
    _guard(body.vk_user_id, launch)
    try:
        return update_staff_settings(body.vk_user_id, color_scheme=body.color_scheme)
    except StaffAuthError as error:
        raise _handle_staff_auth_error(error, protected=True) from error


@app.post("/api/staff/activity/clients")
def staff_activity_clients(
    body: StaffActivityClientsRequest,
    launch: dict[str, str] = Depends(vk_launch_from_header),
):
    _guard(body.vk_user_id, launch)
    try:
        return load_staff_activity_clients(
            body.vk_user_id,
            activity_id=body.activity_id,
            activity_date=body.activity_date,
            config=_cfg(),
        )
    except StaffAuthError as error:
        raise _handle_staff_auth_error(error, protected=True) from error


@app.post("/api/auth/logout")
def auth_logout(body: VkUserRequest, launch: dict[str, str] = Depends(vk_launch_from_header)):
    _guard(body.vk_user_id, launch)
    logout(body.vk_user_id)
    return {"success": True}


@app.get("/api/settings", response_model=SettingsResponse)
def settings_get(vk_user_id: int, launch: dict[str, str] = Depends(vk_launch_from_header)):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    return load_settings(vk_user_id)


@app.put("/api/settings", response_model=SettingsResponse)
def settings_put(body: SettingsUpdateRequest, launch: dict[str, str] = Depends(vk_launch_from_header)):
    _guard(body.vk_user_id, launch)
    if body.clear_favorite and body.favorite_staff_id is not None:
        raise HTTPException(status_code=400, detail="Нельзя одновременно сбросить и задать тренера")
    try:
        return update_settings(
            body.vk_user_id,
            favorite_staff_id=body.favorite_staff_id,
            favorite_staff_name=body.favorite_staff_name,
            clear_favorite=body.clear_favorite,
            notifications_enabled=body.notifications_enabled,
            color_scheme=body.color_scheme,
            welcome_banner_seen=body.welcome_banner_seen,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/schedule/filters")
def schedule_filters(refresh: bool = False):
    try:
        return load_schedule_filters(_cfg(), force_refresh=refresh)
    except AuthError as error:
        status = 400
        if error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error


@app.get("/api/schedule/rebook")
def schedule_rebook(vk_user_id: int, launch: dict[str, str] = Depends(vk_launch_from_header)):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    try:
        return load_rebook_slots(vk_user_id, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error, protected=True) from error


@app.get("/api/schedule")
def schedule(day: str | None = None, refresh: bool = False):
    try:
        target = date.fromisoformat(day) if day else studio_today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректная дата") from None

    try:
        return load_schedule(target, _cfg(), force_refresh=refresh)
    except AuthError as error:
        status = 400
        if error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error


@app.get("/api/records")
def records(
    vk_user_id: int,
    filter: str = "all",
    refresh: bool = False,
    launch: dict[str, str] = Depends(vk_launch_from_header),
):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    try:
        return load_records(vk_user_id, filter, _cfg(), force_refresh=refresh)
    except AuthError as error:
        raise _handle_auth_error(error, protected=True) from error


@app.post("/api/records/cancel")
def records_cancel(body: CancelRecordRequest, launch: dict[str, str] = Depends(vk_launch_from_header)):
    _guard(body.vk_user_id, launch)
    try:
        return cancel_record(body.vk_user_id, body.record_id, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error, protected=True) from error


@app.get("/api/records/reschedule-slots")
def records_reschedule_slots(
    vk_user_id: int,
    record_id: int,
    launch: dict[str, str] = Depends(vk_launch_from_header),
):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    if record_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный record_id")
    _guard(vk_user_id, launch)
    try:
        return load_reschedule_slots(vk_user_id, record_id, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error, protected=True) from error


@app.post("/api/records/reschedule")
def records_reschedule(body: RescheduleRecordRequest, launch: dict[str, str] = Depends(vk_launch_from_header)):
    _guard(body.vk_user_id, launch)
    try:
        return reschedule_record(
            body.vk_user_id,
            body.record_id,
            body.activity_id,
            body.activity_date,
            _cfg(),
        )
    except AuthError as error:
        if error.code == "booking_failed":
            raise HTTPException(
                status_code=400,
                detail={"code": error.code, "message": str(error)},
            ) from error
        raise _handle_auth_error(error, protected=True) from error


@app.post("/api/schedule/guest-check")
def schedule_guest_check(body: GuestCheckRequest):
    try:
        return check_guest_booking(body.phone, _cfg())
    except AuthError as error:
        status = 400
        if error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error


@app.get("/api/schedule/book/eligibility")
def schedule_book_eligibility(
    vk_user_id: int,
    activity_id: int,
    activity_date: str | None = None,
    launch: dict[str, str] = Depends(vk_launch_from_header),
):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    if activity_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный activity_id")
    _guard(vk_user_id, launch)
    try:
        return check_booking_eligibility(vk_user_id, activity_id, activity_date, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error, protected=True) from error


@app.post("/api/schedule/book")
def schedule_book(body: BookScheduleRequest, launch: dict[str, str] = Depends(vk_launch_from_header)):
    _guard(body.vk_user_id, launch)
    try:
        return book_schedule_class(
            body.vk_user_id,
            body.activity_id,
            body.activity_date,
            _cfg(),
            guest_phone=body.phone,
            guest_name=body.name,
            guest_surname=body.surname,
        )
    except AuthError as error:
        raise _handle_auth_error(error, protected=True) from error


@app.get("/api/studio/feed")
def studio_feed(refresh: bool = False):
    return load_studio_feed(_cfg(), force_refresh=refresh)


@app.get("/api/abonement")
def abonement(vk_user_id: int, launch: dict[str, str] = Depends(vk_launch_from_header)):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    try:
        return load_abonements(vk_user_id, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error, protected=True) from error


@app.get("/api/home")
def home(vk_user_id: int, refresh: bool = False, launch: dict[str, str] = Depends(vk_launch_from_header)):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    try:
        return load_home(vk_user_id, _cfg(), force_refresh=refresh)
    except AuthError as error:
        raise _handle_auth_error(error, protected=True) from error


@app.get("/api/cabinet")
def cabinet(vk_user_id: int, refresh: bool = False, launch: dict[str, str] = Depends(vk_launch_from_header)):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    _guard(vk_user_id, launch)
    try:
        return load_cabinet(vk_user_id, _cfg(), force_refresh=refresh)
    except AuthError as error:
        raise _handle_auth_error(error, protected=True) from error
