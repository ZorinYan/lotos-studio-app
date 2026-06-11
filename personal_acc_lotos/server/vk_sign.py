"""Проверка подписи launch params VK мини-приложения."""

from __future__ import annotations

import base64
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import parse_qsl, urlencode, urlparse


def compute_launch_sign(query: dict[str, str], secret: str) -> str:
    vk_subset = OrderedDict(
        sorted(
            (key, "" if value is None else str(value))
            for key, value in query.items()
            if key.startswith("vk_")
        )
    )
    sign_string = urlencode(vk_subset, doseq=True)
    digest = HMAC(secret.encode(), sign_string.encode(), sha256).digest()
    encoded = base64.b64encode(digest).decode("utf-8")
    return encoded.rstrip("=").replace("+", "-").replace("/", "_")


def verify_launch_sign(query: dict[str, str], secret: str) -> bool:
    received = query.get("sign")
    if not received or not secret:
        return False
    return received == compute_launch_sign(query, secret)


def launch_user_id(query: dict[str, str]) -> int | None:
    raw = query.get("vk_user_id")
    if raw is None or raw == "":
        return None
    try:
        user_id = int(raw)
    except (TypeError, ValueError):
        return None
    return user_id if user_id > 0 else None


def parse_launch_query(url_or_query: str) -> dict[str, str]:
    query = url_or_query
    if "?" in query:
        query = urlparse(query).query
    return dict(parse_qsl(query, keep_blank_values=True))
