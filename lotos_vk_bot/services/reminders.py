import logging
import threading
from datetime import date, datetime

from bot.keyboards import main_menu
from bot.messenger import Messenger
from config import Config
from utils import reminders_storage, storage
from yclients.abonement_utils import (
    abonement_balance_count,
    abonement_expiry_date,
    is_active_abonement,
)
from yclients.client import YClientsClient
from yclients.formatters_abonement_reminders import (
    format_abonement_expires_tomorrow,
    format_abonement_one_left,
)
from yclients.formatters_records import format_reminder

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(
        self,
        yclients: YClientsClient,
        messenger: Messenger,
        config: Config,
    ) -> None:
        self.yclients = yclients
        self.messenger = messenger
        self.config = config
        self._stop = threading.Event()

    def start(self) -> None:
        thread = threading.Thread(target=self._loop, name="reminders", daemon=True)
        thread.start()
        offsets = ", ".join(f"{minutes} мин" for minutes in self.config.reminder_offsets_minutes)
        logger.info(
            "Напоминания запущены: тренировки (%s), абонемент, проверка каждые %s сек",
            offsets,
            self.config.reminder_check_interval_sec,
        )

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        self._stop.wait(30)
        while not self._stop.is_set():
            try:
                self.check_all()
            except Exception:
                logger.exception("Ошибка в цикле напоминаний")
            self._stop.wait(self.config.reminder_check_interval_sec)

    def check_all(self) -> None:
        users = storage.get_all_users()
        if not users:
            return

        for vk_user_id, phone in users.items():
            try:
                self._check_user(vk_user_id, phone)
            except Exception:
                logger.exception("Напоминание: ошибка для VK user %s", vk_user_id)

    def _check_user(self, vk_user_id: int, phone: str) -> None:
        profile = self.yclients.find_client_by_phone(phone)
        if not profile:
            return

        self._check_training_reminders(vk_user_id, profile["id"])
        self._check_abonement_reminders(vk_user_id, phone)

    def _check_training_reminders(self, vk_user_id: int, client_id: int) -> None:
        records = self.yclients.get_upcoming_records(client_id, limit=20)
        half_window = max(self.config.reminder_check_interval_sec / 60 / 2, 3)
        now = datetime.now()

        for record in records:
            record_id = record.get("id")
            if not record_id:
                continue

            dt = YClientsClient._parse_record_datetime(record)
            if not dt:
                continue

            minutes_until = (dt - now).total_seconds() / 60
            if minutes_until <= 0:
                continue

            for offset in self.config.reminder_offsets_minutes:
                reminder_type = f"training_{offset}"
                if reminders_storage.was_sent_record(record_id, reminder_type):
                    continue
                if abs(minutes_until - offset) > half_window:
                    continue

                text = format_reminder(record, self.config.studio_name, offset)
                self._send(vk_user_id, text, f"тренировка record={record_id} {reminder_type}")
                reminders_storage.mark_sent_record(record_id, reminder_type)

    def _check_abonement_reminders(self, vk_user_id: int, phone: str) -> None:
        try:
            abonements = self.yclients.get_abonements_by_phone(phone)
        except Exception:
            logger.exception("Не удалось загрузить абонементы для user %s", vk_user_id)
            return

        today = date.today()
        for item in abonements:
            if not is_active_abonement(item):
                continue

            abonement_id = item.get("id")
            if not abonement_id:
                continue

            balance = abonement_balance_count(item)
            if balance == 1 and not reminders_storage.was_sent_abonement(
                abonement_id, "one_left"
            ):
                text = format_abonement_one_left(item, self.config.studio_name)
                self._send(vk_user_id, text, f"абонемент {abonement_id} one_left")
                reminders_storage.mark_sent_abonement(abonement_id, "one_left")

            expiry = abonement_expiry_date(item)
            if (
                expiry
                and (expiry - today).days == 1
                and not reminders_storage.was_sent_abonement(abonement_id, "expires_1d")
            ):
                text = format_abonement_expires_tomorrow(item, self.config.studio_name)
                self._send(vk_user_id, text, f"абонемент {abonement_id} expires_1d")
                reminders_storage.mark_sent_abonement(abonement_id, "expires_1d")

    def _send(self, vk_user_id: int, text: str, label: str) -> None:
        try:
            self.messenger.send_message(vk_user_id, text, main_menu(vk_user_id))
            logger.info("Напоминание отправлено: user=%s %s", vk_user_id, label)
        except Exception:
            logger.exception("Не удалось отправить напоминание user=%s %s", vk_user_id, label)
