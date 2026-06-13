"""Verify trial booking flag variants (dev only)."""
from __future__ import annotations

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
    if isinstance(meta, list) and meta:
        first = meta[0]
        if isinstance(first, dict):
            return str(first.get("message") or first)
    return ""


def _record_info(yc, record_id: int) -> dict:
    comp = yc.config.yclients_company_id
    rec = yc._request("GET", f"/record/{comp}/{record_id}").get("data") or {}
    svc = (rec.get("services") or [{}])[0]
    return {
        "cost": svc.get("cost"),
        "manual_cost": svc.get("manual_cost"),
        "first_cost": svc.get("first_cost"),
        "is_trial": svc.get("is_trial"),
        "record_labels": rec.get("record_labels"),
    }


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
    dt = str(activity.get("date") or "")
    if "T" in dt:
        dt = dt.replace("T", " ")[:19]
    print("activity_id", aid, "datetime", dt)
    print("trial_settings", trial)

    base = {
        "phone": "79000000998",
        "fullname": "Тест",
        "surname": "Пробный",
        "comment": "probe trial flag — delete me",
    }

    appt_base = {
        "id": 0,
        "activityId": aid,
        "activityType": 2,
        "staff_id": staff.get("id"),
        "services": [service.get("id")],
        "clients_count": 1,
        "datetime": dt,
        "events": [],
        "chargeStatus": "",
    }

    variants = [
        ("appt_is_trial_service", {**appt_base, "is_trial_service": True}),
        ("appt_is_trial", {**appt_base, "is_trial": True}),
        (
            "appt_both",
            {**appt_base, "is_trial_service": True, "is_trial": True},
        ),
        (
            "appt_trial_id",
            {**appt_base, "trial_id": trial.get("id"), "is_trial_service": True},
        ),
        (
            "top+appt_is_trial_service",
            {
                "bookform_id": 1996926,
                "appointments": [{**appt_base, "is_trial_service": True}],
            },
        ),
        (
            "top+appt_is_trial",
            {
                "bookform_id": 1996926,
                "appointments": [{**appt_base, "is_trial": True}],
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
        if "appointments" in extra:
            payload = {**base, **extra}
        else:
            payload = {**base, "appointments": [extra]}

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
        info = _record_info(yc, record_id) if record_id else {}
        print(name, info)
        if record_id and record_hash:
            _delete_record(yc, record_id, record_hash)


if __name__ == "__main__":
    main()
