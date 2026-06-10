import logging
import os
import signal
import threading
import time
from pathlib import Path

import vk_api
from vk_api.longpoll import VkEventType, VkLongPoll

from bot import messages, states
from bot import booking_context, records_context
from bot.booking_handler import BookingHandler
from bot.cabinet_handler import CabinetHandler
from bot.info_handler import InfoHandler
from bot.keyboards import (
    BTN_ABONEMENT,
    BTN_BOOK,
    BTN_BOOK_AGAIN,
    BTN_BOOK_ONLINE,
    BTN_BOT_MENU,
    BTN_CANCEL_RECORD,
    BTN_CABINET,
    BTN_CABINET_ABONEMENT,
    BTN_CABINET_HISTORY,
    BTN_CABINET_RECORDS,
    BTN_CABINET_REFRESH,
    BTN_CANCEL,
    BTN_CHANGE_PHONE,
    BTN_CONTACT_ADMIN,
    BTN_CONTACTS,
    BTN_FAQ,
    BTN_FAVORITE_TRAINER,
    BTN_PICK_TRAINER,
    BTN_HELP,
    BTN_HOW_TO_USE,
    BTN_INFO,
    BTN_LOGIN,
    BTN_LOGOUT,
    BTN_MENU,
    BTN_NEXT_RECORD,
    BTN_SCHEDULE,
    BTN_SCHEDULE_10,
    BTN_SCHEDULE_15,
    BTN_SCHEDULE_5,
    BTN_SCHEDULE_MY_TRAINER,
    BTN_SCHEDULE_TODAY,
    BTN_SCHEDULE_TOMORROW,
    admin_chat_menu,
    main_menu,
)
from bot.routing import is_bot_command
from bot.phone_flow import PhoneFlow
from bot.records_handler import RecordsHandler
from bot.schedule_handler import ScheduleHandler
from bot.trainer_handler import TrainerHandler
from bot.messenger import Messenger
from bot.vk_patch import apply as apply_vk_patch
from config import load_config
from health_server import start_from_env
from services.keepalive import start_from_env as start_keepalive
from services.reminders import ReminderService
from utils import storage
from yclients import YClientsClient, YClientsError, YClientsPermissionError
from yclients.formatters import format_abonements

apply_vk_patch()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

Path("data").mkdir(parents=True, exist_ok=True)

config = load_config()

vk_session = vk_api.VkApi(token=config.vk_token)
vk = vk_session.get_api()
messenger = Messenger(vk)
yclients = YClientsClient(config)

try:
    if not yclients.has_loyalty_access():
        print(
            "ВНИМАНИЕ: у YCLIENTS_USER_TOKEN нет права «Лояльность». "
            "Абонементы не будут работать. Запустите: python scripts/check_permissions.py"
        )
except Exception as error:
    print(f"Не удалось проверить права YClients: {error}")

START_TRIGGERS = {"начать", "start", "привет", "меню"}
CANCEL_TRIGGERS = {"отмена", "назад", BTN_CANCEL.lower()}


def get_first_name(user_id: int) -> str | None:
    try:
        users = vk.users.get(user_ids=user_id)
        if users:
            return users[0].get("first_name")
    except Exception:
        pass
    return None


phone_flow = PhoneFlow(yclients, messenger, config)
cabinet = CabinetHandler(yclients, messenger, config, phone_flow)
schedule = ScheduleHandler(yclients, messenger)
booking = BookingHandler(yclients, messenger, config, get_first_name)
records = RecordsHandler(yclients, messenger, phone_flow, config)
info = InfoHandler(yclients, messenger, config)
trainer = TrainerHandler(yclients, messenger)


def fetch_and_show_abonement(user_id: int, phone: str) -> None:
    from utils.phone import format_phone_display

    display = format_phone_display(phone)
    try:
        with messenger.loading(user_id, messages.loading_abonement(display), main_menu(user_id)):
            if not yclients.find_client_by_phone(phone):
                messenger.send_message(
                    user_id, messages.client_not_found(config), main_menu(user_id)
                )
                return
            abonements = yclients.get_abonements_by_phone(phone)
            usage_visits = yclients.get_abonement_usage_visits(phone, limit=3)
    except YClientsPermissionError:
        messenger.send_message(user_id, messages.service_unavailable(), main_menu(user_id))
        print("Ошибка прав YClients — см. scripts/check_permissions.py")
        return
    except YClientsError as error:
        messenger.send_message(user_id, messages.fetch_error(str(error)), main_menu(user_id))
        return

    messenger.send_message(
        user_id,
        format_abonements(abonements, usage_visits=usage_visits),
        main_menu(user_id),
    )


phone_flow.bind_handlers(
    on_cabinet=cabinet._show_overview,
    on_booking=booking.open,
    on_cancel_record=records._load_records,
    on_abonement=fetch_and_show_abonement,
    on_next_record=info.show_next_record,
)

reminders = ReminderService(yclients, messenger, config)
reminders.start()


def show_menu(user_id: int, text: str | None = None) -> None:
    states.set_state(user_id, None)
    states.clear_pending(user_id)
    booking_context.clear(user_id)
    records_context.clear(user_id)
    trainer.cancel_pick(user_id)
    if text is None:
        first_name = get_first_name(user_id)
        if storage.get_phone(user_id):
            text = messages.welcome(config, first_name)
        else:
            text = messages.welcome_guest(config, first_name)
    messenger.send_message(user_id, text, main_menu(user_id))


def open_booking(user_id: int) -> None:
    phone = phone_flow.require_phone(user_id, purpose=states.PURPOSE_BOOKING)
    if phone:
        booking.open(user_id, phone)


def open_abonement(user_id: int) -> None:
    phone = phone_flow.require_phone(user_id, purpose=states.PURPOSE_ABONEMENT)
    if phone:
        fetch_and_show_abonement(user_id, phone)


def handle_message_event(user_id: int, text: str, text_lower: str) -> None:
    is_main_menu = text == BTN_MENU or text_lower == "меню"
    if text_lower in CANCEL_TRIGGERS or is_main_menu:
        if booking_context.is_active(user_id) or records_context.is_active(user_id):
            show_menu(user_id, messages.action_cancelled())
            return
        if states.get_state(user_id) in {
            states.AWAITING_PHONE,
            states.AWAITING_CLIENT_NAME,
        }:
            show_menu(user_id, messages.action_cancelled())
            return
        if is_main_menu:
            show_menu(user_id)
            return

    if booking_context.is_active(user_id):
        if booking.handle_message(user_id, text, storage.get_phone(user_id)):
            return
        booking.cancel(user_id)

    if records_context.is_active(user_id):
        if records.handle_message(user_id, text):
            return
        records.cancel(user_id)

    if trainer.is_picking(user_id):
        if trainer.handle_pick(user_id, text):
            return

    if states.get_state(user_id) == states.AWAITING_PHONE:
        phone_flow.handle_phone_input(user_id, text)
        return

    if states.get_state(user_id) == states.AWAITING_CLIENT_NAME:
        phone_flow.handle_name_input(user_id, text)
        return

    if states.get_state(user_id) == states.ADMIN_CHAT:
        if text in {BTN_BOT_MENU, BTN_MENU} or text_lower in {"меню бота", "к боту"}:
            show_menu(user_id)
            return
        if not is_bot_command(text, text_lower):
            return
        states.set_state(user_id, None)

    if text == BTN_CONTACT_ADMIN or text_lower in {"администратор", "админ", "оператор"}:
        states.set_state(user_id, states.ADMIN_CHAT)
        messenger.send_message(
            user_id,
            messages.admin_chat_started(config),
            admin_chat_menu(),
        )
        return

    if text == BTN_INFO or text_lower in {"справка", "о студии"}:
        info.show_info_menu(user_id)
        return

    if text == BTN_CONTACTS or text_lower == "контакты":
        info.show_contacts(user_id)
        return

    if text == BTN_FAQ or text_lower in {"вопросы", "faq", "вопросы и ответы"}:
        info.show_faq(user_id)
        return

    if text == BTN_BOOK_ONLINE or text_lower in {"записаться онлайн", "онлайн запись"}:
        info.show_book_online(user_id)
        return

    if text in {BTN_HOW_TO_USE, BTN_HELP} or text_lower in {"помощь", "как пользоваться"}:
        info.show_help(user_id)
        return

    if text == BTN_LOGOUT or text_lower in {"выйти", "выход", "выйти из аккаунта"}:
        if storage.get_phone(user_id):
            storage.clear_phone(user_id)
            show_menu(user_id, messages.logged_out())
        else:
            show_menu(user_id)
        return

    if not storage.get_phone(user_id):
        if text == BTN_LOGIN or text_lower in {"войти", "вход"}:
            phone_flow.ask_phone(user_id, purpose=states.PURPOSE_LOGIN)
            return
        if text_lower in START_TRIGGERS:
            show_menu(user_id)
            return
        if is_bot_command(text, text_lower):
            show_menu(user_id, messages.please_login())
            return
        return

    if text == BTN_NEXT_RECORD or text_lower in {"ближайшая запись", "моя запись"}:
        phone = phone_flow.require_phone(user_id, purpose=states.PURPOSE_NEXT_RECORD)
        if phone:
            info.show_next_record(user_id, phone)
        return

    if text == BTN_BOOK_AGAIN or text_lower in {"записаться снова", "повторить запись"}:
        phone = storage.get_phone(user_id)
        booking.open_book_again(user_id, phone)
        return

    if text == BTN_BOOK or text_lower in {"записаться", "запись"}:
        open_booking(user_id)
        return

    if text == BTN_CANCEL_RECORD or text_lower in {"отменить запись", "отмена записи"}:
        records.open_cancel(user_id)
        return

    if text == BTN_SCHEDULE_MY_TRAINER or text_lower in {"мой тренер", "тренер"}:
        trainer.show_schedule_for_favorite(user_id, days=7)
        return

    if text == BTN_SCHEDULE or text_lower == "расписание":
        schedule.ask_period(user_id)
        return

    if text == BTN_SCHEDULE_TODAY:
        schedule.show_today(user_id)
        return

    if text == BTN_SCHEDULE_TOMORROW:
        schedule.show_tomorrow(user_id)
        return

    if text in {BTN_SCHEDULE_5, BTN_SCHEDULE_10, BTN_SCHEDULE_15}:
        days = schedule.parse_days(text)
        if days:
            schedule.show_schedule(user_id, days)
        return

    if text == BTN_CABINET or text_lower in {"кабинет", "личный кабинет"}:
        cabinet.open_overview(user_id)
        return

    if text == BTN_FAVORITE_TRAINER or text_lower in {"избранный тренер", "любимый тренер"}:
        trainer.show_favorite(user_id)
        return

    if text == BTN_PICK_TRAINER or text_lower in {"выбрать тренера", "сменить тренера"}:
        trainer.start_pick(user_id)
        return

    if text == BTN_CABINET_REFRESH:
        cabinet.refresh(user_id)
        return

    if text == BTN_CABINET_RECORDS:
        cabinet.show_upcoming(user_id)
        return

    if text == BTN_CABINET_HISTORY:
        cabinet.show_history(user_id)
        return

    if text == BTN_CABINET_ABONEMENT:
        cabinet.show_abonement(user_id)
        return

    if text == BTN_ABONEMENT or text_lower in {"абонемент", "мой абонемент"}:
        open_abonement(user_id)
        return

    if text == BTN_CHANGE_PHONE or text_lower in {"изменить номер", "сменить номер"}:
        phone_flow.ask_phone(user_id, purpose=states.PURPOSE_LINK, is_change=True)
        return

    if text_lower in START_TRIGGERS:
        show_menu(user_id)
        return


_shutdown = False
_health_server = None
_keepalive = None


def _handle_shutdown(signum, frame) -> None:
    global _shutdown
    logger.info("Получен сигнал %s, завершаю работу...", signum)
    _shutdown = True
    reminders.stop()
    if _keepalive is not None:
        _keepalive.stop()
    if _health_server is not None:
        _health_server.stop()


def _process_event(event) -> None:
    if event.type != VkEventType.MESSAGE_NEW or not event.to_me:
        return

    user_id = event.user_id
    text = (getattr(event, "text", None) or "").strip()

    if not text:
        return

    text_lower = text.lower()

    try:
        handle_message_event(user_id, text, text_lower)
    except YClientsError as error:
        logging.exception("YClients error for user %s", user_id)
        messenger.send_message(user_id, messages.fetch_error(str(error)), main_menu(user_id))
    except Exception:
        logging.exception("Unhandled error for user %s", user_id)
        messenger.send_message(
            user_id,
            messages.fetch_error("Внутренняя ошибка бота. Попробуйте ещё раз."),
            main_menu(user_id),
        )


def _run_longpoll() -> None:
    logger.info("Long Poll запущен")
    while not _shutdown:
        try:
            longpoll = VkLongPoll(vk_session)
            for event in longpoll.listen():
                if _shutdown:
                    break
                _process_event(event)
        except Exception:
            if _shutdown:
                break
            logger.exception("Ошибка Long Poll, переподключение через 5 сек...")
            time.sleep(5)


def run() -> None:
    global _shutdown, _health_server, _keepalive

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    print("Бот запущен")

    _health_server = start_from_env()
    if _health_server is not None:
        logger.info("Режим Web Service (Render): health-check на PORT=%s", os.getenv("PORT"))
        _keepalive = start_keepalive()
        bot_thread = threading.Thread(target=_run_longpoll, name="vk-longpoll", daemon=True)
        bot_thread.start()
        try:
            while not _shutdown and bot_thread.is_alive():
                bot_thread.join(timeout=1)
        except KeyboardInterrupt:
            _handle_shutdown(signal.SIGINT, None)
        bot_thread.join(timeout=10)
    else:
        _run_longpoll()

    logger.info("Бот остановлен")


if __name__ == "__main__":
    run()
