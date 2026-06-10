from bot import messages, records_context
from bot.keyboards import main_menu
from bot.records_keyboards import (
    BTN_CONFIRM_CANCEL,
    BTN_KEEP_RECORD,
    BTN_PAGE_NEXT,
    BTN_PAGE_PREV,
    RECORD_PAGE_SIZE,
    build_cancel_confirm_keyboard,
    build_records_keyboard,
)
from bot.booking_keyboards import page_caption
from bot.messenger import Messenger
from utils import reminders_storage
from yclients import YClientsClient, YClientsError, YClientsPermissionError
from yclients.formatters_records import (
    format_cancel_success,
    format_record_card,
    format_upcoming_for_cancel,
    record_button_label,
)


class RecordsHandler:
    def __init__(
        self,
        yclients: YClientsClient,
        messenger: Messenger,
        phone_flow,
        config,
    ) -> None:
        self.yclients = yclients
        self.messenger = messenger
        self.phone_flow = phone_flow
        self.config = config

    def cancel(self, user_id: int) -> None:
        records_context.clear(user_id)

    def open_cancel(self, user_id: int) -> None:
        from bot import states

        phone = self.phone_flow.require_phone(user_id, purpose=states.PURPOSE_CANCEL_RECORD)
        if not phone:
            return
        self._load_records(user_id, phone)

    def handle_message(self, user_id: int, text: str) -> bool:
        ctx = records_context.get(user_id)
        if not ctx:
            return False

        if text == BTN_KEEP_RECORD:
            self.cancel(user_id)
            self.messenger.send_message(user_id, messages.record_kept(), main_menu(user_id))
            return True

        if text in {BTN_PAGE_NEXT, BTN_PAGE_PREV} and ctx.step == "pick":
            delta = 1 if text == BTN_PAGE_NEXT else -1
            ctx.record_page = self._clamp_page(
                ctx.record_page + delta, len(ctx.record_labels), RECORD_PAGE_SIZE
            )
            self._show_pick_keyboard(user_id, ctx)
            return True

        if ctx.step == "pick":
            return self._handle_pick(user_id, text)
        if ctx.step == "confirm":
            return self._handle_confirm(user_id, text)

        return False

    def _load_records(self, user_id: int, phone: str) -> None:
        try:
            with self.messenger.loading(user_id, messages.loading_records(), main_menu(user_id)):
                profile = self.yclients.find_client_by_phone(phone)
                if not profile:
                    self.messenger.send_message(
                        user_id, messages.client_not_found(self.config), main_menu(user_id)
                    )
                    return
                records = self.yclients.get_upcoming_records(profile["id"], limit=10)
        except YClientsPermissionError:
            self.messenger.send_message(user_id, messages.service_unavailable(), main_menu(user_id))
            return
        except YClientsError as error:
            self.messenger.send_message(user_id, messages.fetch_error(str(error)), main_menu(user_id))
            return

        if not records:
            self.messenger.send_message(
                user_id,
                format_upcoming_for_cancel([]),
                main_menu(user_id),
            )
            return

        ctx = records_context.start(user_id)
        ctx.records = records
        ctx.record_map, ctx.record_labels = self._build_record_map(records)
        ctx.record_page = 0
        ctx.step = "pick"
        self._show_pick_keyboard(user_id, ctx)

    def _show_pick_keyboard(self, user_id: int, ctx: records_context.RecordsContext) -> None:
        caption = page_caption(ctx.record_page, len(ctx.record_labels), RECORD_PAGE_SIZE)
        self.messenger.send_message(
            user_id,
            format_upcoming_for_cancel(ctx.records) + caption,
            build_records_keyboard(ctx.record_labels, ctx.record_page),
        )

    def _handle_pick(self, user_id: int, text: str) -> bool:
        ctx = records_context.get(user_id)
        if not ctx:
            return False

        record_id = ctx.record_map.get(text)
        if not record_id:
            return False

        record = next((item for item in ctx.records if item.get("id") == record_id), None)
        if not record:
            return False

        ctx.selected_record = record
        ctx.step = "confirm"
        self.messenger.send_message(
            user_id,
            messages.record_cancel_confirm(format_record_card(record)),
            build_cancel_confirm_keyboard(),
        )
        return True

    def _handle_confirm(self, user_id: int, text: str) -> bool:
        if text != BTN_CONFIRM_CANCEL:
            return False

        ctx = records_context.get(user_id)
        if not ctx or not ctx.selected_record:
            return False

        record = ctx.selected_record
        record_id = record.get("id")
        if not record_id:
            records_context.clear(user_id)
            self.messenger.send_message(user_id, messages.record_cancel_failed("Нет ID записи"), main_menu(user_id))
            return True

        try:
            with self.messenger.loading(user_id, messages.loading_record_cancel(), main_menu(user_id)):
                self.yclients.delete_record(record_id)
        except YClientsError as error:
            records_context.clear(user_id)
            self.messenger.send_message(user_id, messages.record_cancel_failed(str(error)), main_menu(user_id))
            return True

        reminders_storage.clear_record(record_id)
        records_context.clear(user_id)
        self.messenger.send_message(
            user_id,
            format_cancel_success(record),
            main_menu(user_id),
        )
        return True

    @staticmethod
    def _build_record_map(records: list[dict]) -> tuple[dict[str, int], list[str]]:
        record_map: dict[str, int] = {}
        labels: list[str] = []
        used: set[str] = set()
        for record in records:
            record_id = record.get("id")
            if not record_id:
                continue
            label = record_button_label(record)
            if label in used:
                label = f"{label[:36]} ({record_id})"[:40]
            used.add(label)
            record_map[label] = record_id
            labels.append(label)
        return record_map, labels

    @staticmethod
    def _clamp_page(page: int, total: int, page_size: int) -> int:
        if total <= 0:
            return 0
        max_page = (total + page_size - 1) // page_size - 1
        return max(0, min(page, max_page))
