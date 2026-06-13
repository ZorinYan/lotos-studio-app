from datetime import date

MONTH_GENITIVE = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]


def _expiry_message(days_left: int, expiry: date) -> str:
    label = f"{expiry.day} {MONTH_GENITIVE[expiry.month - 1]}"
    if days_left == 0:
        return f"Абонемент истекает сегодня · до {label}"
    if days_left == 1:
        return f"Абонемент до {label} · истекает завтра"
    if days_left <= 7:
        return f"Абонемент до {label}"
    return f"Абонемент до {label}"


def _is_expired_status(status: str) -> bool:
    text = status.lower()
    return any(
        word in text
        for word in ("просроч", "законч", "архив", "истёк", "истек", "неактив")
    )


def _parse_profile_date(raw: str | None) -> date | None:
    if not raw:
        return None
    text = str(raw)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _hint(
    hint_type: str,
    message: str,
    *,
    action: str,
    action_label: str,
    detail: str | None = None,
    days_left: int | None = None,
) -> dict:
    payload = {
        "type": hint_type,
        "message": message,
        "action": action,
        "actionLabel": action_label,
    }
    if detail:
        payload["detail"] = detail
    if days_left is not None:
        payload["daysLeft"] = days_left
    return payload


def build_home_alerts(
    abonement: dict | None,
    *,
    profile: dict | None = None,
    inactive_detail: str | None = None,
) -> list[dict]:
    hints: list[dict] = []

    if abonement and not _is_expired_status(abonement.get("status", "")):
        remaining = abonement.get("balanceRemaining")
        if remaining == 1:
            hints.append(
                _hint(
                    "low_balance",
                    "Осталась 1 тренировка на абонементе",
                    action="schedule",
                    action_label="Записаться",
                )
            )

        expiry_raw = abonement.get("expiryDate")
        if expiry_raw:
            try:
                expiry = date.fromisoformat(str(expiry_raw))
            except ValueError:
                expiry = None
            if expiry:
                days_left = (expiry - date.today()).days
                if 0 <= days_left <= 14:
                    hints.append(
                        _hint(
                            "expiring",
                            _expiry_message(days_left, expiry),
                            action="contact_renew",
                            action_label="Продлить",
                            days_left=days_left,
                        )
                    )

    if profile:
        last_visit = _parse_profile_date(profile.get("last_visit_date"))
        visits_count = 0
        for key in ("success_visits_count", "visits_count"):
            try:
                visits_count = max(visits_count, int(profile.get(key) or 0))
            except (TypeError, ValueError):
                pass

        if last_visit and visits_count > 0:
            days_since = (date.today() - last_visit).days
            if days_since >= 14:
                weeks = days_since // 7
                weeks_label = (
                    "2 недели"
                    if weeks == 2
                    else f"{weeks} недель"
                    if weeks >= 5
                    else f"{weeks} недели"
                )
                hints.append(
                    _hint(
                        "inactive",
                        f"Вы не были {weeks_label}",
                        detail=inactive_detail,
                        action="rebook",
                        action_label="Записаться",
                    )
                )

    return hints
