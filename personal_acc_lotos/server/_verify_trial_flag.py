"""Verify trial booking flag for YClients activity/book (dev only)."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

SERVER = Path(__file__).resolve().parent
sys.path[:0] = [str(SERVER), str(SERVER / "lib")]

from miniapp_config import load_config  # noqa: E402
from yclients_adapter import create_yclients_client  # noqa: E402


def _meta_message(body: dict) -> str:
    meta = body.get("meta")
    if isinstance(meta, dict):
        return str(meta.get("message") or "")
    return ""


def _record_cost(yc, record_id: int) -> int | None:
    comp = yc.config.yclients_company_id
    rec = yc._request("GET", f"/record/{comp}/{record_id}").get("data") or {}
    services = rec.get("services") or []
    if not services:
        return None
    return services[0].get("cost")


def _delete_record(yc, record_id: int, record_hash: str) -> None:
    comp = yc.config.yclients_company_id
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
    service = activity.get("service") or {}
    staff = activity.get("staff") or {}
    trial = service.get("trial_settings") or {}
    print("activity_id", aid)
    print("trial_settings", trial)

    base = {
        "phone": "79000000999",
        "fullname": "Тест",
        "surname": "Пробный",
        "comment": "probe trial flag — delete me",
    }

    variants = [
        ("is_trial_service_top", {"is_trial_service": True}),
        (
            "appointments_is_trial_service",
            {"appointments": [{"id": 0, "is_trial_service": True}]},
        ),
        (
            "appointments_full",
            {
                "appointments": [
                    {
                        "id": 0,
                        "activityId": aid,
                        "activityType": 2,
                        "staff_id": staff.get("id"),
                        "services": [service.get("id")],
                        "clients_count": 1,
                        "is_trial_service": True,
                        "events": [],
                        "chargeStatus": "",
                    }
                ]
            },
        ),
        (
            "appointments_full+bookform",
            {
                "bookform_id": 1996926,
                "appointments": [
                    {
                        "id": 0,
                        "activityId": aid,
                        "activityType": 2,
                        "staff_id": staff.get("id"),
                        "services": [service.get("id")],
                        "clients_count": 1,
                        "is_trial_service": True,
                        "events": [],
                        "chargeStatus": "",
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
        try:
            body = response.json()
        except ValueError:
            print(name, response.status_code, response.text[:200])
            continue

        if response.status_code >= 400 or not body.get("success"):
            print(name, response.status_code, _meta_message(body) or body)
            continue

        data = body.get("data") or {}
        record_id = data.get("id")
        record_hash = data.get("hash")
        cost = _record_cost(yc, record_id) if record_id else None
        rec = (
            yc._request("GET", f"/record/{comp}/{record_id}").get("data") or {}
            if record_id
            else {}
        )
        svc = (rec.get("services") or [{}])[0]
        print(
            name,
            "cost",
            cost,
            "manual_cost",
            svc.get("manual_cost"),
            "first_cost",
            svc.get("first_cost"),
            "is_trial",
            svc.get("is_trial"),
        )
        if record_id and record_hash:
            _delete_record(yc, record_id, record_hash)


if __name__ == "__main__":
    main()
