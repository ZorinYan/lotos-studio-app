"""Посты, истории и адрес сообщества VK для главной страницы."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import quote

from geocode import geocode_address
from miniapp_config import MiniAppConfig
from vk_api import VkApiError, vk_call

_WEEKDAY_LABELS = {
    "mon": "Пн",
    "tue": "Вт",
    "wed": "Ср",
    "thu": "Чт",
    "fri": "Пт",
    "sat": "Сб",
    "sun": "Вс",
}

_feed_cache: tuple[tuple[Any, ...], float, dict[str, Any]] | None = None
_FEED_CACHE_TTL_SEC = 900


def clear_feed_cache() -> None:
    global _feed_cache
    _feed_cache = None


def _minutes_to_hhmm(value: Any) -> str | None:
    if value is None:
        return None
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return str(value) if value else None
    hours, mins = divmod(minutes, 60)
    return f"{hours:02d}:{mins:02d}"


def _feed_cache_key(config: MiniAppConfig) -> tuple[Any, ...]:
    return (
        config.vk_group_id,
        bool(config.vk_service_token),
        len(config.vk_service_token),
    )


def _clean_post_text(text: str, *, max_len: int = 220) -> str:
    cleaned = re.sub(r"\[(id|club|public)\d+\|([^\]]+)\]", r"\2", text or "")
    cleaned = re.sub(r"\[([^\]|]+)\|([^\]]+)\]", r"\2", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def _pick_photo_url(photo: dict[str, Any]) -> str | None:
    sizes = photo.get("sizes") or []
    if sizes:
        best = max(sizes, key=lambda item: item.get("width", 0))
        url = best.get("url")
        if url:
            return str(url)
    for key in ("photo_807", "photo_604", "photo_476", "photo_323", "photo_130"):
        value = photo.get(key)
        if value:
            return str(value)
    return None


def _extract_post_image(attachments: list[dict[str, Any]] | None) -> str | None:
    for attachment in attachments or []:
        attachment_type = attachment.get("type")
        if attachment_type == "photo":
            url = _pick_photo_url(attachment.get("photo") or {})
            if url:
                return url
        if attachment_type == "video":
            video = attachment.get("video") or {}
            for key in ("image", "first_frame"):
                items = video.get(key) or []
                if items:
                    best = max(items, key=lambda item: item.get("width", 0))
                    url = best.get("url")
                    if url:
                        return str(url)
    return None


def _format_timetable(timetable: dict[str, Any] | None) -> str | None:
    if not timetable:
        return None

    lines: list[str] = []
    ranges: list[str] = []
    for key, label in _WEEKDAY_LABELS.items():
        day = timetable.get(key)
        if not isinstance(day, dict):
            continue
        if day.get("breaks"):
            continue
        start_raw = day.get("from") or day.get("open_time")
        end_raw = day.get("to") or day.get("close_time")
        start = _minutes_to_hhmm(start_raw) if isinstance(start_raw, int) else start_raw
        end = _minutes_to_hhmm(end_raw) if isinstance(end_raw, int) else end_raw
        if start and end:
            time_range = f"{start}–{end}"
            ranges.append(time_range)
            lines.append(f"{label}: {time_range}")

    if not lines:
        return None
    if len(set(ranges)) == 1:
        return f"Ежедневно: {ranges[0]}"
    return ", ".join(lines)


def _parse_group_place(group: dict[str, Any], config: MiniAppConfig) -> dict[str, Any] | None:
    owner_id = -config.vk_group_id if config.vk_group_id else 0
    group_url = f"https://vk.com/club{config.vk_group_id}" if config.vk_group_id else None

    title = group.get("name") or config.studio_name
    address = config.studio_address or None
    phone = config.studio_phone or group.get("phone") or None
    hours = config.studio_hours or None
    latitude = config.studio_latitude
    longitude = config.studio_longitude

    addresses_block = group.get("addresses") or {}
    main_address = None
    if isinstance(addresses_block, dict):
        main_address = addresses_block.get("main_address")
        if not main_address:
            items = addresses_block.get("items") or []
            main_address = items[0] if items else None

    if isinstance(main_address, dict):
        city_title = (main_address.get("city") or {}).get("title")
        raw_address = (main_address.get("address") or "").strip()
        address_title = (main_address.get("title") or "").strip()
        if address_title:
            address = address_title
        elif raw_address and city_title:
            address = f"{raw_address}, {city_title}"
        else:
            address = raw_address or address
        phone = main_address.get("phone") or phone
        hours = _format_timetable(main_address.get("timetable")) or hours
        latitude = main_address.get("latitude", latitude)
        longitude = main_address.get("longitude", longitude)

    place = group.get("place") or {}
    if isinstance(place, dict) and place:
        address = place.get("address") or address
        latitude = place.get("latitude", latitude)
        longitude = place.get("longitude", longitude)
        title = place.get("title") or title

    contacts = group.get("contacts") or []
    if not phone and contacts:
        for contact in contacts:
            if contact.get("phone"):
                phone = contact["phone"]
                break

    map_url = None
    if latitude is not None and longitude is not None:
        map_url = f"https://yandex.ru/maps/?pt={longitude},{latitude}&z=17&l=map"
    elif address:
        map_url = f"https://yandex.ru/maps/?text={quote(address)}"

    if (latitude is None or longitude is None) and address:
        geocoded = geocode_address(address)
        if geocoded is not None:
            latitude, longitude = geocoded
            if not map_url:
                map_url = f"https://yandex.ru/maps/?pt={longitude},{latitude}&z=17&l=map"

    if not any([address, phone, hours, latitude, longitude, group_url]):
        return None

    return {
        "title": title,
        "address": address,
        "phone": phone,
        "hours": hours,
        "latitude": latitude,
        "longitude": longitude,
        "mapUrl": map_url,
        "groupUrl": group_url,
        "ownerId": owner_id,
    }


def _load_wall_posts(config: MiniAppConfig) -> list[dict[str, Any]]:
    if not config.vk_group_id or not config.vk_service_token:
        return []

    token = config.vk_service_token

    owner_id = -config.vk_group_id
    response = vk_call(
        "wall.get",
        token,
        owner_id=owner_id,
        count=5,
        filter="owner",
    )
    items = (response or {}).get("items") or []
    posts: list[dict[str, Any]] = []

    for item in items[:5]:
        post_id = item.get("id")
        if post_id is None:
            continue
        text = _clean_post_text(item.get("text", ""))
        image_url = _extract_post_image(item.get("attachments"))
        if not text and not image_url:
            continue
        posts.append(
            {
                "id": int(post_id),
                "ownerId": owner_id,
                "date": int(item.get("date") or 0),
                "text": text,
                "imageUrl": image_url,
                "postUrl": f"https://vk.com/wall{owner_id}_{post_id}",
            }
        )

    return posts


def _load_stories(config: MiniAppConfig) -> tuple[list[dict[str, Any]], bool]:
    if not config.vk_group_id:
        return [], False

    owner_id = -config.vk_group_id
    try:
        response = vk_call(
            "stories.get",
            config.vk_group_token,
            owner_id=owner_id,
            extended=0,
        )
    except VkApiError:
        return [], True

    stories: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    for block in (response or {}).get("items") or []:
        nested = block.get("stories") if isinstance(block, dict) else None
        story_items = nested if isinstance(nested, list) else [block]
        for item in story_items:
            if not isinstance(item, dict):
                continue
            story_id = item.get("id")
            if story_id is None or item.get("is_expired"):
                continue
            story_id = int(story_id)
            if story_id in seen_ids:
                continue
            seen_ids.add(story_id)

            preview = None
            photo = item.get("photo") or {}
            preview = _pick_photo_url(photo)
            if not preview:
                video = item.get("video") or {}
                frames = video.get("first_frame") or video.get("image") or []
                if frames:
                    preview = max(
                        frames,
                        key=lambda frame: frame.get("width", 0),
                    ).get("url")
            if not preview:
                continue

            access_key = item.get("access_key")
            link = f"https://vk.com/story{owner_id}_{story_id}"
            if access_key:
                link = f"{link}?access_key={access_key}"

            stories.append(
                {
                    "id": story_id,
                    "ownerId": owner_id,
                    "previewUrl": str(preview),
                    "linkUrl": link,
                }
            )
            if len(stories) >= 8:
                break
        if len(stories) >= 8:
            break

    return stories, True


def _load_group_info(config: MiniAppConfig) -> dict[str, Any] | None:
    if not config.vk_group_id:
        return _parse_group_place({}, config)

    group: dict[str, Any] = {}

    if config.vk_group_token:
        fields = ",".join(["name", "phone", "contacts", "addresses", "place"])
        try:
            response = vk_call(
                "groups.getById",
                config.vk_group_token,
                group_id=config.vk_group_id,
                fields=fields,
            )
            if isinstance(response, dict):
                groups = response.get("groups") or []
            elif isinstance(response, list):
                groups = response
            else:
                groups = []
            if groups:
                group = groups[0]
        except VkApiError:
            pass

    if config.vk_service_token:
        try:
            addresses = vk_call(
                "groups.getAddresses",
                config.vk_service_token,
                group_id=config.vk_group_id,
            )
            items = (addresses or {}).get("items") or []
            if items:
                group["addresses"] = {
                    "main_address": items[0],
                    "items": items,
                }
        except VkApiError:
            pass

    return _parse_group_place(group, config)


def load_studio_feed(config: MiniAppConfig, *, force_refresh: bool = False) -> dict[str, Any]:
    global _feed_cache

    cache_key = _feed_cache_key(config)
    now = time.monotonic()
    if not force_refresh and _feed_cache is not None:
        cached_key, expires_at, payload = _feed_cache
        if cached_key == cache_key and now < expires_at:
            return payload

    posts: list[dict[str, Any]] = []
    stories: list[dict[str, Any]] = []
    stories_available = bool(config.vk_group_id)
    place = _load_group_info(config)

    if config.vk_group_id:
        if config.vk_service_token:
            try:
                posts = _load_wall_posts(config)
            except VkApiError:
                posts = []

        if config.vk_group_token:
            stories, stories_available = _load_stories(config)

    payload = {
        "posts": posts,
        "stories": stories,
        "storiesAvailable": stories_available,
        "place": place,
    }

    should_cache = bool(posts) or not config.vk_service_token
    if should_cache:
        _feed_cache = (cache_key, now + _FEED_CACHE_TTL_SEC, payload)
    return payload
