"""Отправка сообщений VK от имени сообщества (код входа в мини-приложение)."""

from __future__ import annotations

import random
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class VkSendResult:
    ok: bool
    error_code: int | None = None
    error_message: str | None = None


def send_user_message(group_token: str, user_id: int, text: str) -> VkSendResult:
    if not group_token:
        return VkSendResult(ok=False, error_message="VK_GROUP_TOKEN не задан")

    try:
        response = requests.post(
            "https://api.vk.com/method/messages.send",
            params={
                "access_token": group_token,
                "v": "5.199",
                "user_id": user_id,
                "message": text,
                "random_id": random.randint(1, 2**31 - 1),
            },
            timeout=15,
        )
        payload = response.json()
    except requests.RequestException as error:
        return VkSendResult(ok=False, error_message=str(error))

    if "error" in payload:
        err = payload["error"]
        return VkSendResult(
            ok=False,
            error_code=err.get("error_code"),
            error_message=err.get("error_msg", "Ошибка VK API"),
        )

    if payload.get("response") is None:
        return VkSendResult(ok=False, error_message="Пустой ответ VK API")

    return VkSendResult(ok=True)
