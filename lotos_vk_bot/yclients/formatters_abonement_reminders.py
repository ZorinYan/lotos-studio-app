from utils.text_style import LIGHT, page_header
from yclients.abonement_utils import format_abonement_expiry


def _abonement_title(item: dict) -> str:
    return item.get("type", {}).get("title", "Абонемент")


def format_abonement_one_left(item: dict, studio_name: str) -> str:
    title = _abonement_title(item)
    balance = item.get("balance_string", "1")
    return (
        f"🎫  Абонемент · {studio_name}\n"
        f"{LIGHT}\n\n"
        f"На абонементе «{title}» осталось одно занятие:\n"
        f"    💫  {balance}\n\n"
        "Успейте записаться, пока действует абонемент 🪷"
    )


def format_abonement_expires_tomorrow(item: dict, studio_name: str) -> str:
    title = _abonement_title(item)
    expiry = format_abonement_expiry(item) or "📅  Срок действия скоро закончится"
    balance = item.get("balance_string", "—")
    return (
        f"⏳  Абонемент · {studio_name}\n"
        f"{LIGHT}\n\n"
        f"«{title}» заканчивается завтра.\n"
        f"    {expiry}\n"
        f"    💫  Остаток:  {balance}\n\n"
        "Запишитесь через бот или продлите абонемент у администратора."
    )
