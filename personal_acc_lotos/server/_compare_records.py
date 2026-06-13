import json
import sys
from pathlib import Path

SERVER = Path(__file__).resolve().parent
sys.path[:0] = [str(SERVER), str(SERVER / "lib")]

from miniapp_config import load_config  # noqa: E402
from yclients_adapter import create_yclients_client  # noqa: E402


def dump_record(record_id: int) -> None:
    yc = create_yclients_client(load_config())
    comp = yc.config.yclients_company_id
    rec = yc._request("GET", f"/record/{comp}/{record_id}").get("data") or {}
    interesting = {
        k: rec[k]
        for k in rec
        if k
        not in (
            "staff",
            "company",
            "documents",
            "goods_transactions",
            "consumables",
        )
    }
    print("===", record_id)
    print(json.dumps(interesting, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    dump_record(1769336094)  # trial 300
    dump_record(1775889111)  # regular 900
