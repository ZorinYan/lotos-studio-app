import sys
from datetime import date, timedelta
from pathlib import Path

SERVER = Path(__file__).resolve().parent
sys.path[:0] = [str(SERVER), str(SERVER / "lib")]

from miniapp_config import load_config  # noqa: E402
from yclients_adapter import create_yclients_client  # noqa: E402

yc = create_yclients_client(load_config())
comp = yc.config.yclients_company_id
start = (date.today() - timedelta(days=365)).isoformat()
end = (date.today() + timedelta(days=30)).isoformat()

for page in range(1, 20):
    recs = (
        yc._request(
            "GET",
            f"/records/{comp}",
            params={"start_date": start, "end_date": end, "count": 200, "page": page},
        ).get("data")
        or []
    )
    if not recs:
        break
    for rec in recs:
        if not rec.get("activity_id"):
            continue
        cost = (rec.get("services") or [{}])[0].get("cost")
        if cost != 300:
            continue
        if rec.get("online"):
            print(
                "ONLINE trial",
                rec.get("id"),
                "labels",
                rec.get("record_labels"),
                "from",
                rec.get("record_from"),
                "bookform",
                rec.get("bookform_id"),
                "comment",
                (rec.get("comment") or "")[:40],
            )
