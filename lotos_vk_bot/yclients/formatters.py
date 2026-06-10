from utils.text_style import LIGHT, join_blocks, page_header
from yclients.abonement_utils import (
    format_abonement_expiry,
    format_abonement_freeze,
    format_abonement_visit_line,
)

STATUS_ICONS = {
    "активирован": "✅",
    "активен": "✅",
    "выпущен": "🟡",
    "просрочен": "⏳",
    "закончился": "⏳",
    "заморожен": "❄️",
}


def status_icon(status_title: str) -> str:
    lowered = status_title.lower()
    for key, icon in STATUS_ICONS.items():
        if key in lowered:
            return icon
    return "▫️"


def _format_usage_visits(visits: list[dict]) -> str:
    if not visits:
        return (
            "\n🕐  Последние списания\n"
            "    пока нет данных о посещениях по абонементу"
        )

    lines = ["", "🕐  Последние списания по абонементу", ""]
    for visit in visits[:3]:
        lines.append(format_abonement_visit_line(visit))
    return "\n".join(lines)


def _format_single_abonement(item: dict, index: int, total: int) -> str:
    abonement_type = item.get("type", {})
    status = item.get("status", {})
    title = abonement_type.get("title", "Абонемент")
    number = item.get("number", "—")
    balance = item.get("balance_string", "—")
    status_title = status.get("extended_title") or status.get("title", "—")
    icon = status_icon(status_title)

    if total > 1:
        header = f"📋  Абонемент {index} из {total}"
    else:
        header = page_header("🪷", "Ваш абонемент")

    lines = [
        f"📌  {title}",
        f"💫  Остаток:  {balance}",
        f"{icon}  Статус:  {status_title}",
        f"🔢  Номер:  {number}",
    ]

    expiry = format_abonement_expiry(item)
    if expiry:
        lines.append(expiry)

    lines.extend(format_abonement_freeze(item))

    body = "\n".join(lines)
    if total > 1:
        return f"{header}\n{LIGHT}\n{body}"
    return f"{header}\n\n{body}"


def format_abonements(
    abonements: list[dict],
    *,
    usage_visits: list[dict] | None = None,
) -> str:
    if not abonements:
        return (
            f"{page_header('🔍', 'Абонемент не найден')}\n\n"
            "По этому номеру ничего не нашлось.\n\n"
            "Проверьте, что телефон совпадает с тем, "
            "что указан в студии, или нажмите «Изменить номер»."
        )

    total = len(abonements)
    blocks = [_format_single_abonement(item, i, total) for i, item in enumerate(abonements, 1)]

    if total == 1:
        text = blocks[0]
    else:
        text = f"{page_header('🪷', f'Ваши абонементы · {total}')}\n\n" + join_blocks(blocks)

    if usage_visits is not None:
        text += _format_usage_visits(usage_visits)
    return text
