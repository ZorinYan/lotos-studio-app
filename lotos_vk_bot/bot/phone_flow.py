from collections.abc import Callable

from bot import messages, states
from bot.keyboards import main_menu, phone_input_menu
from bot.messenger import Messenger
from config import Config
from utils import storage
from utils.client_name import client_has_surname, client_names_match
from utils.phone import format_phone_display, normalize_phone
from yclients import YClientsClient, YClientsError, YClientsPermissionError


class PhoneFlow:
    def __init__(
        self,
        yclients: YClientsClient,
        messenger: Messenger,
        config: Config,
    ) -> None:
        self.yclients = yclients
        self.messenger = messenger
        self.config = config
        self.on_cabinet: Callable[[int, str], None] | None = None
        self.on_booking: Callable[[int, str], None] | None = None
        self.on_cancel_record: Callable[[int, str], None] | None = None
        self.on_abonement: Callable[[int, str], None] | None = None
        self.on_next_record: Callable[[int, str], None] | None = None

    def bind_handlers(
        self,
        *,
        on_cabinet: Callable[[int, str], None],
        on_booking: Callable[[int, str], None],
        on_cancel_record: Callable[[int, str], None],
        on_abonement: Callable[[int, str], None],
        on_next_record: Callable[[int, str], None] | None = None,
    ) -> None:
        self.on_cabinet = on_cabinet
        self.on_booking = on_booking
        self.on_cancel_record = on_cancel_record
        self.on_abonement = on_abonement
        self.on_next_record = on_next_record

    def require_phone(self, user_id: int, *, purpose: str, is_change: bool = False) -> str | None:
        phone = storage.get_phone(user_id)
        if phone:
            return phone

        self.ask_phone(user_id, purpose=purpose, is_change=is_change)
        return None

    def ask_phone(self, user_id: int, *, purpose: str, is_change: bool = False) -> None:
        states.set_pending_action(user_id, purpose)
        states.set_state(user_id, states.AWAITING_PHONE)
        if purpose == states.PURPOSE_CABINET:
            text = messages.ask_phone_for_cabinet()
        elif purpose == states.PURPOSE_BOOKING:
            text = messages.ask_phone_for_booking()
        elif purpose == states.PURPOSE_CANCEL_RECORD:
            text = messages.ask_phone_for_cancel()
        elif purpose == states.PURPOSE_LOGIN:
            text = messages.ask_phone_for_login()
        elif is_change:
            text = messages.ask_phone_change()
        else:
            text = messages.ask_phone()
        self.messenger.send_message(user_id, text, phone_input_menu())

    def handle_phone_input(self, user_id: int, raw_phone: str) -> None:
        phone = normalize_phone(raw_phone)
        if not phone:
            self.messenger.send_message(user_id, messages.invalid_phone(), phone_input_menu())
            return

        if not states.get_pending_action(user_id):
            states.set_pending_action(user_id, states.PURPOSE_ABONEMENT)

        try:
            with self.messenger.loading(
                user_id, messages.loading_phone_check(), phone_input_menu()
            ):
                profile = self.yclients.find_client_by_phone(phone)
        except YClientsPermissionError:
            self._abort_verification(user_id)
            self.messenger.send_message(
                user_id, messages.service_unavailable(), main_menu(user_id)
            )
            return
        except YClientsError as error:
            self._abort_verification(user_id)
            self.messenger.send_message(
                user_id, messages.fetch_error(str(error)), main_menu(user_id)
            )
            return

        if not profile:
            self._abort_verification(user_id)
            self.messenger.send_message(
                user_id, messages.client_not_found(self.config), main_menu(user_id)
            )
            return

        states.set_pending_phone(user_id, phone)
        states.set_state(user_id, states.AWAITING_CLIENT_NAME)
        self.messenger.send_message(
            user_id,
            messages.ask_client_name(with_surname=client_has_surname(profile)),
            phone_input_menu(),
        )

    def handle_name_input(self, user_id: int, raw_name: str) -> None:
        name = raw_name.strip()
        if not name:
            self.messenger.send_message(
                user_id, messages.invalid_client_name(), phone_input_menu()
            )
            return

        phone = states.get_pending_phone(user_id)
        purpose = states.get_pending_action(user_id)
        if not phone or not purpose:
            states.set_state(user_id, None)
            return

        try:
            with self.messenger.loading(
                user_id, messages.loading_name_check(), phone_input_menu()
            ):
                profile = self.yclients.find_client_by_phone(phone)
        except YClientsPermissionError:
            self._abort_verification(user_id)
            self.messenger.send_message(
                user_id, messages.service_unavailable(), main_menu(user_id)
            )
            return
        except YClientsError as error:
            self._abort_verification(user_id)
            self.messenger.send_message(
                user_id, messages.fetch_error(str(error)), main_menu(user_id)
            )
            return

        if not profile or not client_names_match(profile, name):
            self._abort_verification(user_id)
            self.messenger.send_message(
                user_id, messages.name_verification_failed(self.config), main_menu(user_id)
            )
            return

        states.pop_pending_action(user_id)
        states.pop_pending_phone(user_id)
        states.set_state(user_id, None)
        storage.set_phone(user_id, phone)
        self._continue_purpose(user_id, phone, purpose)

    def _abort_verification(self, user_id: int) -> None:
        states.clear_pending(user_id)
        states.set_state(user_id, None)

    def _continue_purpose(self, user_id: int, phone: str, purpose: str) -> None:
        if purpose == states.PURPOSE_CABINET:
            if self.on_cabinet:
                self.on_cabinet(user_id, phone)
            return

        if purpose == states.PURPOSE_BOOKING:
            if self.on_booking:
                self.on_booking(user_id, phone)
            return

        if purpose == states.PURPOSE_CANCEL_RECORD:
            if self.on_cancel_record:
                self.on_cancel_record(user_id, phone)
            return

        if purpose == states.PURPOSE_LOGIN:
            display = format_phone_display(phone)
            self.messenger.send_message(
                user_id,
                messages.login_success(display),
                main_menu(user_id),
            )
            return

        if purpose == states.PURPOSE_NEXT_RECORD:
            if self.on_next_record:
                self.on_next_record(user_id, phone)
            return

        if purpose == states.PURPOSE_LINK:
            display = format_phone_display(phone)
            self.messenger.send_message(
                user_id,
                f"✅  Номер обновлён: {display}\n\n{messages.phone_saved()}",
                main_menu(user_id),
            )
            return

        if self.on_abonement:
            self.on_abonement(user_id, phone)
