"""Геокодирование адреса, если VK не отдаёт координаты."""

from __future__ import annotations

import requests

_GEOCODE_CACHE: dict[str, tuple[float, float]] = {}


def geocode_address(address: str) -> tuple[float, float] | None:
    key = address.strip().lower()
    if not key:
        return None
    if key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[key]

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "LotosStudioMiniApp/1.0"},
            timeout=12,
        )
        payload = response.json()
    except requests.RequestException:
        return None

    if not payload:
        return None

    try:
        coords = (float(payload[0]["lat"]), float(payload[0]["lon"]))
    except (KeyError, TypeError, ValueError):
        return None

    _GEOCODE_CACHE[key] = coords
    return coords
