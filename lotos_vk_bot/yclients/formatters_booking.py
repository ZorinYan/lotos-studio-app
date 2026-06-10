from utils.text_style import LIGHT, page_header, spots_line
from yclients.client import YClientsClient
from yclients.formatters_schedule import MONTHS, WEEKDAYS


def format_activity_card(activity: dict) -> str:
    dt = YClientsClient._parse_activity_datetime(activity)
    service = activity.get("service", {})
    staff = activity.get("staff", {})
    title = service.get("title", "Занятие")
    trainer = staff.get("name") or staff.get("specialization") or "—"

    when = "—"
    if dt:
        when = (
            f"{WEEKDAYS[dt.weekday()]}, {dt.day} {MONTHS[dt.month - 1]}"
            f"  ·  {dt.strftime('%H:%M')}"
        )

    lines = [
        f"📌  {title}",
        f"🗓  {when}",
        f"👤  {trainer}",
    ]

    spots = spots_line(
        activity.get("capacity") or 0,
        activity.get("records_count") or 0,
    )
    if spots:
        lines.append(spots)

    return f"{LIGHT}\n" + "\n".join(lines) + f"\n{LIGHT}"


def format_booking_success(activity: dict, phone_display: str) -> str:
    return (
        f"{page_header('✅', 'Вы записаны!')}\n\n"
        f"{format_activity_card(activity)}\n\n"
        f"📱  {phone_display}\n\n"
        "До встречи в студии 🪷"
    )
