import re


def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw.strip())
    if not digits:
        return None

    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits

    if len(digits) != 11 or not digits.startswith("7"):
        return None

    return digits


def format_phone_display(phone: str) -> str:
    if len(phone) == 11 and phone.startswith("7"):
        return f"+7 ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
    return phone
