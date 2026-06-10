import json
from dataclasses import dataclass
from pathlib import Path

INFO_PATH = Path(__file__).resolve().parent.parent / "data" / "studio_info.json"


@dataclass(frozen=True)
class FaqItem:
    question: str
    answer: str


@dataclass(frozen=True)
class StudioInfo:
    address: str
    work_hours: str
    phone: str
    map_url: str
    parking: str
    extra: str
    faq: list[FaqItem]


def load_studio_info() -> StudioInfo:
    if not INFO_PATH.exists():
        return StudioInfo(
            address="",
            work_hours="",
            phone="",
            map_url="",
            parking="",
            extra="",
            faq=[],
        )

    with open(INFO_PATH, encoding="utf-8") as file:
        raw = json.load(file)

    faq = [
        FaqItem(question=item.get("q", ""), answer=item.get("a", ""))
        for item in raw.get("faq", [])
        if item.get("q") and item.get("a")
    ]

    return StudioInfo(
        address=str(raw.get("address", "")).strip(),
        work_hours=str(raw.get("work_hours", "")).strip(),
        phone=str(raw.get("phone", "")).strip(),
        map_url=str(raw.get("map_url", "")).strip(),
        parking=str(raw.get("parking", "")).strip(),
        extra=str(raw.get("extra", "")).strip(),
        faq=faq,
    )
