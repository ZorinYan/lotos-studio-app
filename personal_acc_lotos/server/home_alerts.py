from datetime import date


def _expiry_message(days_left: int) -> str:
    if days_left == 1:
        return "Абонемент истекает завтра"
    if days_left in {2, 3, 4}:
        return f"Абонемент истекает через {days_left} дня"
    return f"Абонемент истекает через {days_left} дней"


def _is_expired_status(status: str) -> bool:
    text = status.lower()
    return any(
        word in text
        for word in ("просроч", "законч", "архив", "истёк", "истек", "неактив")
    )


def build_home_alerts(abonement: dict | None) -> list[dict]:
    if not abonement or _is_expired_status(abonement.get("status", "")):
        return []

    alerts: list[dict] = []
    remaining = abonement.get("balanceRemaining")
    if remaining == 1:
        alerts.append(
            {
                "type": "low_balance",
                "message": "Осталось 1 занятие на абонементе",
            }
        )

    expiry_raw = abonement.get("expiryDate")
    if expiry_raw:
        try:
            expiry = date.fromisoformat(str(expiry_raw))
        except ValueError:
            expiry = None
        if expiry:
            days_left = (expiry - date.today()).days
            if 1 <= days_left <= 3:
                alerts.append(
                    {
                        "type": "expiring",
                        "daysLeft": days_left,
                        "message": _expiry_message(days_left),
                    }
                )

    return alerts
