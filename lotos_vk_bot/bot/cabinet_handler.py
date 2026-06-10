from bot import messages
from bot.keyboards import cabinet_menu, main_menu
from bot.messenger import Messenger
from services.cabinet import CabinetService
from yclients import YClientsClient, YClientsError, YClientsPermissionError
from yclients.formatters import format_abonements
from yclients.formatters_cabinet import (
    format_cabinet_overview,
    format_upcoming_records,
    format_visit_history,
)


class CabinetHandler:
    def __init__(
        self,
        yclients: YClientsClient,
        messenger: Messenger,
        config,
        phone_flow,
    ) -> None:
        self.yclients = yclients
        self.messenger = messenger
        self.config = config
        self.service = CabinetService(yclients)
        self.phone_flow = phone_flow

    def open_overview(self, user_id: int) -> None:
        from bot import states

        phone = self.phone_flow.require_phone(user_id, purpose=states.PURPOSE_CABINET)
        if not phone:
            return
        self._show_overview(user_id, phone)

    def _show_overview(
        self,
        user_id: int,
        phone: str,
        *,
        loading_text: str | None = None,
    ) -> None:
        loading_text = loading_text or messages.loading_cabinet()
        try:
            with self.messenger.loading(user_id, loading_text, cabinet_menu()):
                data = self.service.load(phone)
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
        except ValueError:
            self.messenger.send_message(
                user_id, messages.client_not_found(self.config), main_menu(user_id)
            )
            return

        self.messenger.send_message(
            user_id,
            format_cabinet_overview(data, phone),
            cabinet_menu(),
        )

    def show_upcoming(self, user_id: int) -> None:
        from bot import states

        phone = self.phone_flow.require_phone(user_id, purpose=states.PURPOSE_CABINET)
        if not phone:
            return
        try:
            with self.messenger.loading(
                user_id, messages.loading_records(), cabinet_menu()
            ):
                profile = self.yclients.find_client_by_phone(phone)
                if not profile:
                    self.messenger.send_message(
                        user_id, messages.client_not_found(self.config), cabinet_menu()
                    )
                    return
                records = self.yclients.get_upcoming_records(profile["id"], limit=5)
        except (YClientsError, YClientsPermissionError) as error:
            self.messenger.send_message(
                user_id,
                messages.fetch_error(str(error)),
                cabinet_menu(),
            )
            return
        self.messenger.send_message(
            user_id, format_upcoming_records(records), cabinet_menu()
        )

    def show_history(self, user_id: int) -> None:
        from bot import states

        phone = self.phone_flow.require_phone(user_id, purpose=states.PURPOSE_CABINET)
        if not phone:
            return
        try:
            with self.messenger.loading(
                user_id, messages.loading_history(), cabinet_menu()
            ):
                visits = self.yclients.get_recent_visits(phone, limit=8)
        except (YClientsError, YClientsPermissionError) as error:
            self.messenger.send_message(
                user_id,
                messages.fetch_error(str(error)),
                cabinet_menu(),
            )
            return
        self.messenger.send_message(
            user_id, format_visit_history(visits), cabinet_menu()
        )

    def show_abonement(self, user_id: int) -> None:
        from bot import states

        phone = self.phone_flow.require_phone(user_id, purpose=states.PURPOSE_CABINET)
        if not phone:
            return
        try:
            with self.messenger.loading(user_id, messages.loading(), cabinet_menu()):
                if not self.yclients.find_client_by_phone(phone):
                    self.messenger.send_message(
                        user_id, messages.client_not_found(self.config), cabinet_menu()
                    )
                    return
                abonements = self.yclients.get_abonements_by_phone(phone)
                usage_visits = self.yclients.get_abonement_usage_visits(phone, limit=3)
        except YClientsPermissionError:
            self.messenger.send_message(
                user_id, messages.service_unavailable(), cabinet_menu()
            )
            return
        except YClientsError as error:
            self.messenger.send_message(
                user_id, messages.fetch_error(str(error)), cabinet_menu()
            )
            return
        self.messenger.send_message(
            user_id,
            format_abonements(abonements, usage_visits=usage_visits),
            cabinet_menu(),
        )

    def refresh(self, user_id: int) -> None:
        from utils import storage
        from utils.phone import format_phone_display

        phone = storage.get_phone(user_id)
        if not phone:
            self.open_overview(user_id)
            return
        display = format_phone_display(phone)
        self._show_overview(
            user_id,
            phone,
            loading_text=f"🔄 Обновляю кабинет ({display})...",
        )
