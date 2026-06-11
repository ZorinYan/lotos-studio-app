from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from auth_service import (
    AuthError,
    check_phone,
    get_auth_status,
    logout,
    verify_name,
)
from booking_api import book_schedule_class, check_booking_eligibility, check_guest_booking
from cabinet_api import load_cabinet
from home_api import load_home
from records_api import cancel_record, load_records
from rebook_api import load_rebook_slots
from schedule_api import load_schedule
from schedule_filters_api import load_schedule_filters
from miniapp_config import MiniAppConfig, load_config
from _lib_path import ensure_lib_path
from keepalive import KeepAliveService, start_from_env

ensure_lib_path()
from utils.dates import studio_today  # noqa: E402

config: MiniAppConfig = load_config()

_keepalive: KeepAliveService | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _keepalive
    _keepalive = start_from_env()
    yield
    if _keepalive is not None:
        _keepalive.stop()
        _keepalive = None


app = FastAPI(title="Lotos Mini App API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VkUserRequest(BaseModel):
    vk_user_id: int = Field(gt=0)


class PhoneRequest(VkUserRequest):
    phone: str = Field(min_length=5, max_length=30)


class VerifyRequest(VkUserRequest):
    phone: str = Field(min_length=11, max_length=11)
    name: str = Field(min_length=1, max_length=120)


class BookScheduleRequest(VkUserRequest):
    activity_id: int = Field(gt=0)
    activity_date: str | None = None
    phone: str | None = None
    name: str | None = None


class GuestCheckRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=30)


class CancelRecordRequest(VkUserRequest):
    record_id: int = Field(gt=0)


def _cfg() -> MiniAppConfig:
    return config


def _handle_auth_error(error: AuthError) -> HTTPException:
    status = 400
    if error.code in {"service_unavailable", "fetch_error"}:
        status = 503
    return HTTPException(
        status_code=status,
        detail={"code": error.code, "message": str(error)},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config/public")
def public_config() -> dict[str, str]:
    cfg = _cfg()
    return {
        "studioName": cfg.studio_name,
        "bookingUrl": cfg.yclients_booking_url,
    }


@app.get("/api/auth/status")
def auth_status(vk_user_id: int):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    status = get_auth_status(vk_user_id, _cfg())
    return {
        "authenticated": status.authenticated,
        "phone": status.phone,
        "phoneDisplay": status.phone_display,
        "clientName": status.client_name,
    }


@app.post("/api/auth/phone")
def auth_phone(body: PhoneRequest):
    try:
        result = check_phone(body.vk_user_id, body.phone, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error) from error

    return {
        "step": result.step,
        "phone": result.phone,
        "requiresSurname": result.requires_surname,
    }


@app.post("/api/auth/verify")
def auth_verify(body: VerifyRequest):
    try:
        result = verify_name(body.vk_user_id, body.phone, body.name, _cfg())
    except AuthError as error:
        raise _handle_auth_error(error) from error

    return {
        "success": True,
        "phone": result.phone,
        "phoneDisplay": result.phone_display,
    }


@app.post("/api/auth/logout")
def auth_logout(body: VkUserRequest):
    logout(body.vk_user_id)
    return {"success": True}


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
def schedule_rebook(vk_user_id: int):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    try:
        return load_rebook_slots(vk_user_id, _cfg())
    except AuthError as error:
        status = 400
        if error.code == "not_authenticated":
            status = 401
        elif error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error


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
def records(vk_user_id: int, filter: str = "all", refresh: bool = False):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    try:
        return load_records(vk_user_id, filter, _cfg(), force_refresh=refresh)
    except AuthError as error:
        status = 401 if error.code == "not_authenticated" else 400
        if error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error


@app.post("/api/records/cancel")
def records_cancel(body: CancelRecordRequest):
    try:
        return cancel_record(body.vk_user_id, body.record_id, _cfg())
    except AuthError as error:
        status = 400
        if error.code == "not_authenticated":
            status = 401
        elif error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error


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
def schedule_book_eligibility(vk_user_id: int, activity_id: int, activity_date: str | None = None):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    if activity_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный activity_id")
    try:
        return check_booking_eligibility(vk_user_id, activity_id, activity_date, _cfg())
    except AuthError as error:
        status = 400
        if error.code == "not_authenticated":
            status = 401
        elif error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error


@app.post("/api/schedule/book")
def schedule_book(body: BookScheduleRequest):
    try:
        return book_schedule_class(
            body.vk_user_id,
            body.activity_id,
            body.activity_date,
            _cfg(),
            guest_phone=body.phone,
            guest_name=body.name,
        )
    except AuthError as error:
        status = 400
        if error.code == "not_authenticated":
            status = 401
        elif error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error


@app.get("/api/home")
def home(vk_user_id: int, refresh: bool = False):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    try:
        return load_home(vk_user_id, _cfg(), force_refresh=refresh)
    except AuthError as error:
        status = 401 if error.code == "not_authenticated" else 400
        if error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error


@app.get("/api/cabinet")
def cabinet(vk_user_id: int, refresh: bool = False):
    if vk_user_id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный vk_user_id")
    try:
        return load_cabinet(vk_user_id, _cfg(), force_refresh=refresh)
    except AuthError as error:
        status = 401 if error.code == "not_authenticated" else 400
        if error.code in {"service_unavailable", "fetch_error"}:
            status = 503
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error)},
        ) from error
