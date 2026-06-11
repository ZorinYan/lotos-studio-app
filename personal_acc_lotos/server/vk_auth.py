"""Проверка подписи VK на запросах к API."""

from __future__ import annotations

import base64
import json

from fastapi import Header, HTTPException

from miniapp_config import MiniAppConfig
from vk_sign import launch_user_id, verify_launch_sign


def decode_launch_header(header: str | None) -> dict[str, str]:
    if not header:
        return {}
    try:
        raw = base64.b64decode(header).decode("utf-8")
        parsed = json.loads(raw)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): "" if value is None else str(value) for key, value in parsed.items()}


def guard_vk_user(vk_user_id: int, launch: dict[str, str], config: MiniAppConfig) -> None:
    if config.skip_vk_sign:
        return

    if not config.vk_app_secret:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "vk_sign_not_configured",
                "message": "На сервере не настроен VK_APP_SECRET.",
            },
        )

    if not launch or not launch.get("sign"):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "missing_vk_sign",
                "message": "Откройте приложение через ВКонтакте и обновите страницу.",
            },
        )

    if not verify_launch_sign(launch, config.vk_app_secret):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "invalid_vk_sign",
                "message": "Недействительная подпись VK. Обновите мини-приложение.",
            },
        )

    launch_uid = launch_user_id(launch)
    if launch_uid is None or launch_uid != vk_user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "vk_user_mismatch",
                "message": "Идентификатор пользователя VK не совпадает с подписью.",
            },
        )


def vk_launch_from_header(
    x_vk_launch_params: str | None = Header(default=None, alias="X-VK-Launch-Params"),
) -> dict[str, str]:
    return decode_launch_header(x_vk_launch_params)
