from datetime import date, timedelta

from bot import messages
from bot.keyboards import (
    BTN_SCHEDULE_TODAY,
    BTN_SCHEDULE_TOMORROW,
    main_menu,
    schedule_period_menu,
)
from bot.messenger import Messenger
from yclients import YClientsClient, YClientsError, YClientsPermissionError
from yclients.formatters_schedule import format_schedule

SCHEDULE_DAYS = {
    "5 дней": 5,
    "10 дней": 10,
    "15 дней": 15,
}


class ScheduleHandler:
    def __init__(self, yclients: YClientsClient, messenger: Messenger) -> None:
        self.yclients = yclients
        self.messenger = messenger

    def ask_period(self, user_id: int) -> None:
        self.messenger.send_message(
            user_id,
            messages.schedule_choose_period(),
            schedule_period_menu(user_id),
        )

    def show_schedule(self, user_id: int, days: int) -> None:
        loading_text = messages.loading_schedule(days)
        try:
            with self.messenger.loading(user_id, loading_text, schedule_period_menu(user_id)):
                activities = self.yclients.get_schedule_activities(days)
        except YClientsPermissionError:
            self.messenger.send_message(
                user_id, messages.service_unavailable(), main_menu(user_id)
            )
            return
        except YClientsError as error:
            self.messenger.send_message(
                user_id, messages.fetch_error(str(error)), main_menu(user_id)
            )
            return

        self._send_parts(user_id, format_schedule(activities, days))

    def show_schedule_for_date(self, user_id: int, target: date, label: str) -> None:
        loading_text = messages.loading_schedule_day(label)
        try:
            with self.messenger.loading(user_id, loading_text, schedule_period_menu(user_id)):
                activities = self.yclients.get_activities_for_date(target)
        except YClientsPermissionError:
            self.messenger.send_message(
                user_id, messages.service_unavailable(), main_menu(user_id)
            )
            return
        except YClientsError as error:
            self.messenger.send_message(
                user_id, messages.fetch_error(str(error)), main_menu(user_id)
            )
            return

        self._send_parts(user_id, format_schedule(activities, days=1, title=label))

    def show_today(self, user_id: int) -> None:
        self.show_schedule_for_date(user_id, date.today(), "Сегодня")

    def show_tomorrow(self, user_id: int) -> None:
        self.show_schedule_for_date(user_id, date.today() + timedelta(days=1), "Завтра")

    def _send_parts(self, user_id: int, parts: list[str]) -> None:
        for index, part in enumerate(parts):
            keyboard = (
                main_menu(user_id)
                if index == len(parts) - 1
                else schedule_period_menu(user_id)
            )
            self.messenger.send_message(user_id, part, keyboard)

    @staticmethod
    def parse_days(button_text: str) -> int | None:
        return SCHEDULE_DAYS.get(button_text)
