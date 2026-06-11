from services.cabinet import CabinetData
from utils.dates import format_date_short, format_datetime_short
from utils.phone import format_phone_display
from utils.text_style import join_blocks, marker, page_header, section
from yclients.abonement_utils import format_abonement_expiry, format_abonement_freeze
from yclients.formatters import status_icon

ATTENDANCE_LABELS = {
    0: "⏳  Ожидаем",
    1: "✅  Пришёл",
    2: "📌  Подтвердил",
    -1: "❌  Не пришёл",
}


def _client_name(profile: dict) -> str:
    parts = [
        profile.get("name", ""),
        profile.get("surname", ""),
        profile.get("patronymic", ""),
    ]
    name = " ".join(part for part in parts if part).strip()
    return name or "Клиент"


def _service_titles(record: dict) -> str:
    services = record.get("services", [])
    if not services:
        return "Занятие"
    return ", ".join(item.get("title", "Услуга") for item in services)


def _staff_name(record: dict) -> str:
    staff = record.get("staff", {})
    return staff.get("name") or staff.get("specialization") or "—"


def _abonement_summary(abonements: list[dict]) -> str:
    if not abonements:
        return f"{section('🎫', 'Абонемент')}\n\n    нет активных"

    lines = [section("🎫", "Абонемент"), ""]
    for item in abonements[:2]:
        title = item.get("type", {}).get("title", "Абонемент")
        balance = item.get("balance_string", "—")
        status = item.get("status", {})
        status_title = status.get("extended_title") or status.get("title", "—")
        icon = status_icon(status_title)
        lines.append(f"    •  {title}")
        lines.append(f"      {balance}  {icon}")
        expiry = format_abonement_expiry(item)
        if expiry:
            lines.append(f"      {expiry.replace('📅  ', '')}")
        for freeze_line in format_abonement_freeze(item):
            lines.append(f"      {freeze_line}")
    if len(abonements) > 2:
        lines.append(f"    •  и ещё {len(abonements) - 2}...")
    return "\n".join(lines)


def _upcoming_preview(records: list[dict]) -> str:
    lines = [section("📅", "Ближайшие записи"), ""]
    if not records:
        lines.append("    пока нет предстоящих занятий")
        return "\n".join(lines)

    for record in records[:2]:
        when = format_datetime_short(record.get("datetime") or record.get("date", ""))
        service = _service_titles(record)
        staff = _staff_name(record)
        lines.append(f"    •  {when}")
        lines.append(f"      {service}")
        lines.append(f"      👤  {staff}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _visits_preview(visits: list[dict]) -> str:
    lines = [section("🕐", "Недавние посещения"), ""]
    if not visits:
        lines.append("    история пока пуста")
        return "\n".join(lines)

    for visit in visits[:3]:
        when = format_date_short(visit.get("date", ""))
        service = _service_titles(visit)
        lines.append(f"    •  {when}  ·  {service}  ✅")
    return "\n".join(lines)


def format_cabinet_overview(data: CabinetData, phone: str) -> str:
    profile = data.profile
    name = _client_name(profile)
    visits = profile.get("visits") or 0
    spent = profile.get("spent") or 0
    discount = profile.get("discount") or 0
    first_visit = profile.get("first_visit_date") or ""
    last_visit = profile.get("last_visit_date") or ""

    lines = [
        page_header("👤", "Личный кабинет"),
        "",
        f"🪷  {name}",
        f"📱  {format_phone_display(phone)}",
        section("📊", "Статистика"),
        "",
        f"    •  Визитов в студии:  {visits}",
    ]

    if spent:
        lines.append(f"    •  Оплачено всего:  {spent:,.0f} ₽".replace(",", " "))
    if discount:
        lines.append(f"    •  Персональная скидка:  {discount}%")
    if first_visit:
        lines.append(f"    •  Первый визит:  {format_date_short(first_visit)}")
    if last_visit:
        lines.append(f"    •  Последний визит:  {format_date_short(last_visit)}")

    lines.extend(["", _abonement_summary(data.abonements), "", _upcoming_preview(data.upcoming_records), "", _visits_preview(data.recent_visits)])
    return "\n".join(lines)


def format_upcoming_records(records: list[dict]) -> str:
    if not records:
        return (
            f"{page_header('📅', 'Ближайшие записи')}\n\n"
            "У вас нет предстоящих занятий.\n"
            "Запишитесь через бот или напишите администратору."
        )

    blocks = []
    for index, record in enumerate(records, 1):
        when = format_datetime_short(record.get("datetime") or record.get("date", ""))
        service = _service_titles(record)
        staff = _staff_name(record)
        attendance = ATTENDANCE_LABELS.get(record.get("attendance", 0), "▫️")
        blocks.append(
            "\n".join([
                f"{marker(index)}  {when}",
                f"    {service}",
                f"    👤  {staff}",
                f"    {attendance}",
            ])
        )

    return (
        f"{page_header('📅', 'Ближайшие записи')}\n\n"
        + join_blocks(blocks)
        + "\n\nОтменить запись — кнопка «Отменить запись» в меню."
    )


def format_visit_history(visits: list[dict]) -> str:
    if not visits:
        return (
            f"{page_header('🕐', 'История посещений')}\n\n"
            "Пока нет завершённых визитов в студии."
        )

    blocks = []
    for index, visit in enumerate(visits, 1):
        when = format_date_short(visit.get("date", ""))
        service = _service_titles(visit)
        staff = _staff_name(visit)
        blocks.append(
            "\n".join([
                f"{marker(index)}  {when}",
                f"    {service}",
                f"    👤  {staff}  ✅",
            ])
        )

    return f"{page_header('🕐', 'История посещений')}\n\n" + join_blocks(blocks)
