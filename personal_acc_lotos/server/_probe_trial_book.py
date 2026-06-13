"""Probe YClients activity book payload for trial flag (dev only)."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

SERVER = Path(__file__).resolve().parent
sys.path[:0] = [str(SERVER), str(SERVER / "lib")]

from miniapp_config import load_config  # noqa: E402
from yclients_adapter import create_yclients_client  # noqa: E402


def main() -> None:
    yc = create_yclients_client(load_config())
    comp = yc.config.yclients_company_id

    activity = None
    for offset in range(14):
        target = date.today() + timedelta(days=offset)
        for item in yc.get_activities_for_date(target):
            trial = (item.get("service") or {}).get("trial_settings")
            if trial and yc.activity_has_free_spots(item):
                activity = item
                break
        if activity:
            break

    if not activity:
        print("No bookable trial activity found")
        return

    aid = activity["id"]
    trial = activity["service"]["trial_settings"]
    print("activity_id", aid)
    print("trial_settings", trial)

    base = {
        "phone": "79000000001",
        "fullname": "Тест",
        "surname": "Пробный",
        "comment": "probe — do not keep",
    }

    variants = [
        ("base", {}),
        ("salon_service_id", {"salon_service_id": trial["salon_service_id"]}),
        ("trial_id", {"trial_id": trial["id"]}),
        ("service_trial_id", {"service_trial_id": trial["id"]}),
        ("is_trial_visit", {"is_trial_visit": True}),
        ("is_trial", {"is_trial": True}),
        ("trial_visit", {"trial_visit": True}),
        ("trial_settings_id", {"trial_settings_id": trial["id"]}),
        (
            "salon+trial_id",
            {
                "salon_service_id": trial["salon_service_id"],
                "trial_id": trial["id"],
            },
        ),
        (
            "appointments_trial",
            {
                "appointments": [
                    {
                        "id": 1,
                        "services": [activity["service"]["id"]],
                        "is_trial_visit": True,
                    }
                ],
            },
        ),
    ]

    url = f"{yc.BASE_URL}/activity/{comp}/{aid}/book"
    headers = {
        "Authorization": f"Bearer {yc.config.yclients_partner_token}",
        "Accept": "application/vnd.yclients.v2+json",
        "Content-Type": "application/json",
    }

    for name, extra in variants:
        payload = {**base, **extra}
        response = yc._send_request("POST", url, headers=headers, json=payload)
        body = {}
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text[:300]}
        print(
            name,
            response.status_code,
            body.get("meta", {}).get("message") or body.get("success"),
        )


if __name__ == "__main__":
    main()
