import re

from datetime import date



from utils.dates import format_date_short, format_datetime_short, parse_datetime



_INACTIVE_STATUS_SLUGS = frozenset(

    {

        "expired",

        "depleted",

        "used",

        "closed",

        "archived",

        "inactive",

        "finished",

    }

)



_INACTIVE_STATUS_MARKERS = (

    "просрочен",

    "исчерпан",

    "закончился",

    "завершён",

    "завершен",

    "архив",

    "закрыт",

    "использован",

    "неактив",

)





def abonement_expiry_raw(item: dict) -> str | None:

    for key in (

        "expiration_date",

        "expired_at",

        "end_date",

        "valid_till",

        "valid_until",

        "date_finish",

    ):

        raw = item.get(key)

        if raw:

            return str(raw)

    return None





def format_abonement_expiry(item: dict) -> str | None:

    raw = abonement_expiry_raw(item)

    if not raw:

        return None

    formatted = format_date_short(raw)

    if formatted and formatted != "—":

        return f"📅  Действует до:  {formatted}"

    return f"📅  Действует до:  {raw[:10]}"





def format_abonement_freeze(item: dict) -> list[str]:

    lines: list[str] = []

    if item.get("is_frozen"):

        lines.append("❄️  Сейчас заморожен")



    freeze = item.get("freeze_period") or item.get("freeze") or {}

    if isinstance(freeze, dict):

        start = freeze.get("start_date") or freeze.get("from")

        end = freeze.get("end_date") or freeze.get("to")

        if start or end:

            start_fmt = format_date_short(str(start)) if start else "—"

            end_fmt = format_date_short(str(end)) if end else "—"

            lines.append(f"❄️  Заморозка:  {start_fmt} — {end_fmt}")



    frozen_until = item.get("frozen_until") or item.get("freeze_until")

    if frozen_until and not item.get("is_frozen"):

        lines.append(f"❄️  Заморозка до:  {format_date_short(str(frozen_until))}")



    return lines





def visit_used_abonement(visit: dict) -> bool:

    if visit.get("abonement_id") or visit.get("loyalty_abonement_id"):

        return True



    for key in ("abonement", "loyalty_abonement"):

        block = visit.get(key)

        if isinstance(block, dict) and block.get("id"):

            return True



    for collection_key in ("goods_transactions", "transactions", "payments"):

        for tx in visit.get(collection_key) or []:

            if not isinstance(tx, dict):

                continue

            if tx.get("abonement_id") or tx.get("type") in {"abonement", "loyalty_abonement"}:

                return True

            if "абонемент" in str(tx.get("title", "")).lower():

                return True



    comment = str(visit.get("comment", "")).lower()

    if "абонемент" in comment:

        return True



    return False





def _parse_balance_string_value(raw) -> int | None:

    if raw is None:

        return None

    text = str(raw).strip()

    if not text or text == "—":

        return None



    # «Серфинг (x10)», «Услуги (х6)»

    match = re.search(r"[\(\s][xх×]\s*(\d+)", text, re.IGNORECASE)

    if match:

        return int(match.group(1))



    # «6 из 10»

    match = re.search(r"(\d+)\s*из\s*\d+", text, re.IGNORECASE)

    if match:

        return int(match.group(1))



    if text.isdigit():

        return int(text)



    match = re.search(r"(\d+)", text)

    if match:

        return int(match.group(1))

    return None





def abonement_links_remaining(item: dict) -> int | None:

    links = (item.get("balance_container") or {}).get("links") or []

    if not links:

        return None



    total = 0

    found = False

    for link in links:

        if not isinstance(link, dict):

            continue

        count = link.get("count")

        if count is None:

            continue

        try:

            total += int(count)

            found = True

        except (TypeError, ValueError):

            continue

    return total if found else None





def abonement_balance_count(item: dict) -> int | None:

    """Остаток занятий: links — приоритет, но balance_string важен, если links = 0."""

    links_remaining = abonement_links_remaining(item)

    parsed = _parse_balance_string_value(item.get("balance_string"))



    if links_remaining is not None and links_remaining > 0:

        return links_remaining

    if parsed is not None and parsed > 0:

        return parsed

    if links_remaining is not None:

        return links_remaining

    if parsed is not None:

        return parsed



    balance = item.get("balance")

    if balance is not None:

        try:

            return int(balance)

        except (TypeError, ValueError):

            pass



    return None





def abonement_expiry_date(item: dict) -> date | None:

    raw = abonement_expiry_raw(item)

    if not raw:

        return None

    dt = parse_datetime(raw)

    return dt.date() if dt else None





def _status_title(item: dict) -> str:

    status = item.get("status") or {}

    if not isinstance(status, dict):

        return ""

    return str(status.get("extended_title") or status.get("title") or "").lower()





def is_issued_abonement(item: dict) -> bool:
    title = _status_title(item)
    if any(marker in title for marker in ("выпущ", "issued", "created", "создан")):
        return True
    status = item.get("status") or {}
    if isinstance(status, dict):
        slug = str(status.get("slug") or "").lower()
        return slug in ("created", "issued", "new", "released")
    return False


def is_active_abonement(item: dict) -> bool:

    """Активный по статусу YClients (не по нулевому остатку)."""

    status = item.get("status") or {}

    if not isinstance(status, dict):

        return True



    slug = str(status.get("slug") or "").lower()

    if slug in _INACTIVE_STATUS_SLUGS:

        return False



    title = _status_title(item)

    if any(marker in title for marker in _INACTIVE_STATUS_MARKERS):

        return False



    return True





def format_abonement_visit_line(visit: dict) -> str:

    when = format_datetime_short(visit.get("datetime") or visit.get("date", ""))

    services = visit.get("services", [])

    if services:

        title = ", ".join(item.get("title", "Занятие") for item in services)

    else:

        title = "Занятие"

    staff = visit.get("staff", {})

    trainer = staff.get("name") or staff.get("specialization") or ""

    if trainer:

        return f"    •  {when}  ·  {title}  ·  {trainer}"

    return f"    •  {when}  ·  {title}"


