from dataclasses import dataclass, field

from yclients.client import YClientsClient


@dataclass
class CabinetData:
    profile: dict
    abonements: list[dict] = field(default_factory=list)
    upcoming_records: list[dict] = field(default_factory=list)
    recent_visits: list[dict] = field(default_factory=list)


class CabinetService:
    def __init__(self, client: YClientsClient) -> None:
        self.client = client

    def load(self, phone: str) -> CabinetData:
        profile = self.client.find_client_by_phone(phone)
        if not profile:
            raise ValueError("client_not_found")

        client_id = profile["id"]
        abonements = self.client.get_abonements_by_phone(phone)

        upcoming = self.client.get_upcoming_records(client_id, limit=3)
        recent: list[dict] = []
        try:
            recent = self.client.get_recent_visits(phone, limit=5)
        except Exception:
            pass

        return CabinetData(
            profile=profile,
            abonements=abonements,
            upcoming_records=upcoming,
            recent_visits=recent,
        )
