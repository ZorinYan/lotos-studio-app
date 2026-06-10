from bot import messages
from bot.keyboards import info_menu, main_menu
from bot.messenger import Messenger
from config import Config
from utils.studio_info import load_studio_info
from yclients import YClientsClient, YClientsError, YClientsPermissionError
from yclients.formatters_records import format_next_record


class InfoHandler:
    def __init__(
        self,
        yclients: YClientsClient,
        messenger: Messenger,
        config: Config,
    ) -> None:
        self.yclients = yclients
        self.messenger = messenger
        self.config = config

    def show_info_menu(self, user_id: int) -> None:
        self.messenger.send_message(
            user_id,
            messages.info_menu_intro(self.config),
            info_menu(user_id),
        )

    def show_contacts(self, user_id: int) -> None:
        info = load_studio_info()
        self.messenger.send_message(
            user_id,
            messages.format_contacts(self.config, info),
            info_menu(user_id),
        )

    def show_faq(self, user_id: int) -> None:
        info = load_studio_info()
        self.messenger.send_message(
            user_id,
            messages.format_faq(info),
            info_menu(user_id),
        )

    def show_book_online(self, user_id: int) -> None:
        self.messenger.send_message(
            user_id,
            messages.book_online(self.config),
            info_menu(user_id),
        )

    def show_help(self, user_id: int) -> None:
        self.messenger.send_message(
            user_id,
            messages.help_text(),
            info_menu(user_id),
        )

    def show_next_record(self, user_id: int, phone: str) -> None:
        try:
            with self.messenger.loading(
                user_id, messages.loading_next_record(), main_menu(user_id)
            ):
                profile = self.yclients.find_client_by_phone(phone)
                if not profile:
                    self.messenger.send_message(
                        user_id,
                        messages.client_not_found(self.config),
                        main_menu(user_id),
                    )
                    return
                records = self.yclients.get_upcoming_records(profile["id"], limit=1)
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

        if not records:
            self.messenger.send_message(
                user_id,
                messages.no_upcoming_record(self.config),
                main_menu(user_id),
            )
            return

        self.messenger.send_message(
            user_id,
            format_next_record(records[0]),
            main_menu(user_id),
        )
