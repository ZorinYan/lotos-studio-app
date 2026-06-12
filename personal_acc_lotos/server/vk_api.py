"""Низкоуровневые вызовы VK API для мини-приложения."""

from __future__ import annotations

from typing import Any

import requests

VK_API_VERSION = "5.199"
VK_API_URL = "https://api.vk.com/method"


class VkApiError(Exception):
    def __init__(self, code: int | None, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def vk_call(method: str, token: str, **params: Any) -> Any:
    if not token:
        raise VkApiError(None, "VK_GROUP_TOKEN не задан")

    try:
        response = requests.get(
            f"{VK_API_URL}/{method}",
            params={
                "access_token": token,
                "v": VK_API_VERSION,
                **params,
            },
            timeout=15,
        )
        payload = response.json()
    except requests.RequestException as error:
        raise VkApiError(None, str(error)) from error

    if "error" in payload:
        err = payload["error"]
        raise VkApiError(err.get("error_code"), err.get("error_msg", "Ошибка VK API"))

    return payload.get("response")
