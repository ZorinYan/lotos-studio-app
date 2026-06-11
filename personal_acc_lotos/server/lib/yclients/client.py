import threading
import time
from datetime import date, datetime, timedelta

import requests

from config import Config

_RETRYABLE = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)
_MAX_RETRIES = 3

CLIENTS_PERMISSION_HINT = (
    "У аккаунта YClients нет доступа к клиентской базе.\n\n"
    "YClients → Настройки → Сотрудники → Права доступа → "
    "включите «Клиентская база» и «Телефоны клиентов»."
)

LOYALTY_PERMISSION_HINT = (
    "У аккаунта YClients, чей токен указан в YCLIENTS_USER_TOKEN, "
    "нет права «Лояльность».\n\n"
    "Что сделать:\n"
    "1. YClients → Настройки → Сотрудники\n"
    "2. Выберите владельца или отдельного сотрудника для бота\n"
    "3. Права доступа → включите «Лояльность»\n"
    "4. Заново получите токен: python scripts/get_user_token.py\n\n"
    "Проверить права: python scripts/check_permissions.py"
)


class YClientsError(Exception):
    pass


class YClientsAuthError(YClientsError):
    pass


class YClientsPermissionError(YClientsError):
    pass


class YClientsNetworkError(YClientsError):
    pass


class YClientsClient:
    BASE_URL = "https://api.yclients.com/api/v1"

    def __init__(self, config: Config) -> None:
        self.config = config
        self._lock = threading.Lock()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": (
                    f"Bearer {config.yclients_partner_token}, "
                    f"User {config.yclients_user_token}"
                ),
                "Accept": "application/vnd.yclients.v2+json",
                "Content-Type": "application/json",
            }
        )

    def _send_request(self, method: str, url: str, **kwargs) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                with self._lock:
                    return self.session.request(method, url, timeout=15, **kwargs)
            except _RETRYABLE as error:
                last_error = error
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(1 + attempt)
        raise YClientsNetworkError(
            "Не удалось связаться с YClients. Проверьте интернет и попробуйте снова."
        ) from last_error

    def _request(self, method: str, path: str, **kwargs) -> dict:
        response = self._send_request(method, f"{self.BASE_URL}{path}", **kwargs)

        if response.status_code == 401:
            raise YClientsAuthError(
                "Ошибка авторизации YClients. Проверьте YCLIENTS_PARTNER_TOKEN "
                "и YCLIENTS_USER_TOKEN в .env"
            )

        if response.status_code == 403:
            message = ""
            try:
                message = response.json().get("meta", {}).get("message", "")
            except ValueError:
                pass
            if "прав" in message.lower():
                raise YClientsPermissionError(
                    self._permission_hint_for_path(path)
                )
            raise YClientsPermissionError(
                f"Доступ запрещён (403): {message or response.text[:200]}"
            )

        if response.status_code >= 400:
            raise YClientsError(
                f"YClients вернул ошибку {response.status_code}: {response.text[:200]}"
            )

        return response.json()

    def get_permissions(self) -> dict:
        payload = self._request(
            "GET",
            f"/user/permissions/{self.config.yclients_company_id}",
        )
        return payload.get("data", {})

    def _permission_hint_for_path(self, path: str) -> str:
        if "loyalty" in path or "abonement" in path:
            return LOYALTY_PERMISSION_HINT
        if "client" in path or "record" in path or "visit" in path:
            return CLIENTS_PERMISSION_HINT
        return LOYALTY_PERMISSION_HINT

    def has_loyalty_access(self) -> bool:
        permissions = self.get_permissions()
        loyalty = permissions.get("loyalty", {})
        return bool(
            loyalty.get("loyalty_access") or loyalty.get("has_loyalty_access")
        )

    def get_abonements_by_phone(self, phone: str) -> list[dict]:
        payload = self._request(
            "GET",
            "/loyalty/abonements/",
            params={
                "company_id": self.config.yclients_company_id,
                "phone": phone,
            },
        )

        if not payload.get("success"):
            message = payload.get("meta", {}).get("message", "неизвестная ошибка")
            if "прав" in message.lower():
                raise YClientsPermissionError(LOYALTY_PERMISSION_HINT)
            raise YClientsError(message)

        return payload.get("data", [])

    def find_client_by_phone(self, phone: str) -> dict | None:
        payload = self._request(
            "POST",
            f"/company/{self.config.yclients_company_id}/clients/search",
            json={
                "page": 1,
                "page_size": 5,
                "fields": [
                    "id",
                    "name",
                    "surname",
                    "phone",
                    "visits",
                    "spent",
                    "discount",
                    "first_visit_date",
                    "last_visit_date",
                ],
                "filters": [
                    {
                        "type": "quick_search",
                        "state": {"value": phone},
                    }
                ],
            },
        )
        if not payload.get("success"):
            message = payload.get("meta", {}).get("message", "")
            if "прав" in message.lower():
                raise YClientsPermissionError(CLIENTS_PERMISSION_HINT)
            raise YClientsError(message or "Ошибка поиска клиента")

        clients = payload.get("data", [])
        matched = None
        for client in clients:
            client_phone = str(client.get("phone", "")).strip()
            if client_phone.endswith(phone[-10:]):
                matched = client
                break
        if not matched and clients:
            matched = clients[0]
        if not matched:
            return None

        profile = self.get_client(matched["id"])
        for field in ("first_visit_date", "last_visit_date"):
            if matched.get(field):
                profile[field] = matched[field]
        return profile

    def get_client(self, client_id: int) -> dict:
        payload = self._request(
            "GET",
            f"/client/{self.config.yclients_company_id}/{client_id}",
        )
        if not payload.get("success"):
            raise YClientsError("Не удалось загрузить профиль клиента")
        return payload.get("data", {})

    def get_upcoming_records(self, client_id: int, limit: int = 3) -> list[dict]:
        today = date.today().isoformat()
        payload = self._request(
            "GET",
            f"/records/{self.config.yclients_company_id}",
            params={
                "client_id": client_id,
                "start_date": today,
                # API отдаёт ограниченную страницу — запрашиваем больше,
                # чтобы не потерять ближайшую запись при limit=3 в обзоре.
                "count": 50,
                "page": 1,
            },
        )
        if not payload.get("success"):
            return []

        records = payload.get("data", [])
        upcoming = []
        now = datetime.now()
        for record in records:
            if record.get("deleted"):
                continue
            if record.get("attendance") == -1:
                continue
            dt = self._parse_record_datetime(record)
            if dt and dt >= now:
                upcoming.append((dt, record))

        upcoming.sort(key=lambda item: item[0])
        return [record for _, record in upcoming[:limit]]

    def get_client_records(
        self,
        client_id: int,
        *,
        days_back: int = 180,
        count: int = 100,
    ) -> list[dict]:
        start = (date.today() - timedelta(days=days_back)).isoformat()
        payload = self._request(
            "GET",
            f"/records/{self.config.yclients_company_id}",
            params={
                "client_id": client_id,
                "start_date": start,
                "count": count,
                "page": 1,
            },
        )
        if not payload.get("success"):
            return []

        records: list[tuple[datetime, dict]] = []
        for record in payload.get("data", []):
            if record.get("deleted"):
                continue
            dt = self._parse_record_datetime(record)
            records.append((dt or datetime.min, record))

        records.sort(key=lambda item: item[0])
        return [record for _, record in records]

    def delete_record(self, record_id: int) -> None:
        response = self._send_request(
            "DELETE",
            f"{self.BASE_URL}/record/{self.config.yclients_company_id}/{record_id}",
        )

        if response.status_code == 401:
            raise YClientsAuthError(
                "Ошибка авторизации YClients. Проверьте токены в .env"
            )

        if response.status_code == 403:
            message = ""
            try:
                message = response.json().get("meta", {}).get("message", "")
            except ValueError:
                pass
            raise YClientsPermissionError(
                message or "Нет прав на удаление записи. "
                "Включите «Удаление записей» в правах сотрудника YClients."
            )

        if response.status_code in {200, 204}:
            return

        message = ""
        try:
            message = response.json().get("meta", {}).get("message", "")
        except ValueError:
            message = response.text[:200]
        raise YClientsError(message or f"Не удалось отменить запись ({response.status_code})")

    @staticmethod
    def _parse_record_datetime(record: dict) -> datetime | None:
        dt_raw = record.get("datetime") or record.get("date", "")
        if not dt_raw:
            return None
        try:
            dt = datetime.fromisoformat(dt_raw.replace("Z", "+00:00"))
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            return dt
        except ValueError:
            return None

    def get_abonement_usage_visits(self, phone: str, limit: int = 3) -> list[dict]:
        from yclients.abonement_utils import visit_used_abonement

        visits = self.get_recent_visits(phone, limit=30)
        matched: list[dict] = []
        for visit in visits:
            if visit_used_abonement(visit):
                matched.append(visit)
            if len(matched) >= limit:
                break
        if matched:
            return matched
        return visits[:limit]

    @staticmethod
    def activity_staff_id(activity: dict) -> int | None:
        staff_id = activity.get("staff", {}).get("id")
        return int(staff_id) if staff_id else None

    @staticmethod
    def activity_service_title(activity: dict) -> str:
        service = activity.get("service", {})
        return str(service.get("title") or "Занятие").strip()

    @staticmethod
    def activity_service_id(activity: dict) -> int | None:
        service = activity.get("service", {})
        service_id = service.get("id")
        return int(service_id) if service_id else None

    @staticmethod
    def filter_activities_by_staff(activities: list[dict], staff_id: int) -> list[dict]:
        return [
            item
            for item in activities
            if YClientsClient.activity_staff_id(item) == staff_id
        ]

    @staticmethod
    def filter_activities_like_booking(
        activities: list[dict],
        *,
        staff_id: int,
        service_title: str,
        service_id: int | None = None,
    ) -> list[dict]:
        title_lower = service_title.lower()
        matched: list[dict] = []
        for item in activities:
            if YClientsClient.activity_staff_id(item) != staff_id:
                continue
            item_service_id = YClientsClient.activity_service_id(item)
            item_title = YClientsClient.activity_service_title(item).lower()
            if service_id and item_service_id == service_id:
                matched.append(item)
            elif item_title == title_lower:
                matched.append(item)
        return matched

    def collect_staff_from_activities(
        self, days: int = 14
    ) -> list[dict]:
        staff: dict[int, str] = {}
        for activity in self.get_schedule_activities(days):
            staff_id = self.activity_staff_id(activity)
            if not staff_id:
                continue
            block = activity.get("staff", {})
            name = (block.get("name") or block.get("specialization") or "Тренер").strip()
            staff[staff_id] = name
        return [{"id": staff_id, "name": name} for staff_id, name in sorted(staff.items(), key=lambda item: item[1])]

    def get_recent_visits(self, phone: str, limit: int = 5) -> list[dict]:
        payload = self._request(
            "POST",
            f"/company/{self.config.yclients_company_id}/clients/visits/search",
            json={
                "client_id": None,
                "client_phone": phone,
                "from": None,
                "to": None,
                "payment_statuses": [],
                "attendance": 1,
            },
        )
        if not payload.get("success"):
            return []

        records = payload.get("data", {}).get("records", [])
        visits = []
        for record in records:
            if record.get("attendance") != 1:
                continue
            visits.append(record)
            if len(visits) >= limit:
                break
        return visits

    def search_activities(
        self,
        from_date: date,
        till_date: date,
        *,
        page_size: int = 50,
    ) -> list[dict]:
        company_id = self.config.yclients_company_id
        activities: list[dict] = []
        page = 1

        while True:
            payload = self._request(
                "GET",
                f"/activity/{company_id}/search/",
                params={
                    "from": from_date.isoformat(),
                    "till": till_date.isoformat(),
                    "page": page,
                    "count": page_size,
                },
            )
            if not payload.get("success"):
                message = payload.get("meta", {}).get("message", "")
                raise YClientsError(message or "Ошибка загрузки расписания")

            batch = payload.get("data", [])
            activities.extend(batch)

            total = payload.get("meta", {}).get("count", len(batch))
            if len(activities) >= total or not batch:
                break
            page += 1

        return activities

    def get_schedule_activities(self, days: int) -> list[dict]:
        start = date.today()
        end = start + timedelta(days=days - 1)
        activities = self.search_activities(start, end)

        now = datetime.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        filtered = []
        for activity in activities:
            dt = self._parse_activity_datetime(activity)
            if dt and dt >= day_start:
                filtered.append(activity)

        filtered.sort(key=lambda item: self._parse_activity_datetime(item) or now)
        return filtered

    def get_activities_for_date(self, target: date) -> list[dict]:
        activities = self.search_activities(target, target)
        now = datetime.now()
        filtered = []
        for activity in activities:
            dt = self._parse_activity_datetime(activity)
            if not dt or dt.date() != target:
                continue
            if target == date.today() and dt < now:
                continue
            filtered.append(activity)

        filtered.sort(key=lambda item: self._parse_activity_datetime(item) or now)
        return filtered

    @staticmethod
    def activity_has_free_spots(activity: dict) -> bool:
        capacity = activity.get("capacity") or 0
        if capacity <= 0:
            return True
        booked = activity.get("records_count") or 0
        return booked < capacity

    def get_bookable_activities(self, days: int = 14) -> list[dict]:
        activities = self.get_schedule_activities(days)
        return [item for item in activities if self.activity_has_free_spots(item)]

    def book_activity(
        self,
        activity_id: int,
        phone: str,
        fullname: str,
        surname: str = "",
        *,
        comment: str = "Запись через VK бот",
        salon_service_id: int | None = None,
    ) -> dict:
        payload: dict[str, object] = {
            "phone": phone,
            "fullname": fullname,
            "surname": surname,
            "comment": comment,
        }
        if salon_service_id:
            payload["salon_service_id"] = salon_service_id

        response = self._send_request(
            "POST",
            f"{self.BASE_URL}/activity/{self.config.yclients_company_id}/{activity_id}/book",
            headers={
                "Authorization": f"Bearer {self.config.yclients_partner_token}",
                "Accept": "application/vnd.yclients.v2+json",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        if response.status_code >= 400:
            message = ""
            try:
                message = response.json().get("meta", {}).get("message", "")
            except ValueError:
                pass
            raise YClientsError(message or response.text[:200])

        payload = response.json()
        if not payload.get("success"):
            message = payload.get("meta", {}).get("message", "Не удалось создать запись")
            raise YClientsError(message)
        return payload.get("data", {})

    @staticmethod
    def _parse_activity_datetime(activity: dict) -> datetime | None:
        raw = activity.get("date")
        if raw is None:
            return None
        try:
            if isinstance(raw, (int, float)):
                return datetime.fromtimestamp(raw)
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        except (ValueError, OSError, OverflowError):
            return None
