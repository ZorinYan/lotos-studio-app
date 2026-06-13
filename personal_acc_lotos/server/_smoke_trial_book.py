"""Smoke-test updated book_activity trial flag (dev only)."""
from __future__ import annotations

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
    result = yc.book_activity(
        aid,
        "79000000997",
        "Тест",
        "Пробный",
        comment="smoke trial — delete me",
        is_trial=True,
        activity=activity,
    )
    record_id = result.get("id")
    record_hash = result.get("hash")
    rec = yc._request("GET", f"/record/{comp}/{record_id}").get("data") or {}
    svc = (rec.get("services") or [{}])[0]
    print("record_id", record_id, "cost", svc.get("cost"), "manual_cost", svc.get("manual_cost"))

    if record_id and record_hash:
        yc._send_request(
            "DELETE",
            f"{yc.BASE_URL}/record/{comp}/{record_id}",
            headers={
                "Authorization": f"Bearer {yc.config.yclients_partner_token}",
                "Accept": "application/vnd.yclients.v2+json",
                "Content-Type": "application/json",
            },
            json={"record_hash": record_hash},
        )
        print("deleted")


if __name__ == "__main__":
    main()
