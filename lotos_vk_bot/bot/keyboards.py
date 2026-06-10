from vk_api.keyboard import VkKeyboard

from bot.button_colors import (
    COLOR_ABONEMENT,
    COLOR_BOOK,
    COLOR_DANGER,
    COLOR_MUTED,
    COLOR_SCHEDULE,
)
from utils import storage
from utils import user_prefs

BTN_LOGIN = "Войти"
BTN_LOGOUT = "Выйти"
BTN_CONTACT_ADMIN = "Написать администратору"
BTN_BOT_MENU = "Меню бота"
BTN_BOOK = "Записаться"
BTN_BOOK_AGAIN = "Записаться снова"
BTN_SCHEDULE_MY_TRAINER = "Мой тренер"
BTN_FAVORITE_TRAINER = "Избранный тренер"
BTN_PICK_TRAINER = "Выбрать тренера"
BTN_CANCEL_RECORD = "Отменить запись"
BTN_CABINET = "Личный кабинет"
BTN_SCHEDULE = "Расписание"
BTN_ABONEMENT = "Мой абонемент"
BTN_NEXT_RECORD = "Ближайшая запись"
BTN_INFO = "Справка"
BTN_CONTACTS = "Контакты"
BTN_FAQ = "Вопросы и ответы"
BTN_BOOK_ONLINE = "Записаться онлайн"
BTN_HOW_TO_USE = "Как пользоваться"

BTN_SCHEDULE_TODAY = "Сегодня"
BTN_SCHEDULE_TOMORROW = "Завтра"
BTN_SCHEDULE_5 = "5 дней"
BTN_SCHEDULE_10 = "10 дней"
BTN_SCHEDULE_15 = "15 дней"
BTN_CHANGE_PHONE = "Изменить номер"
BTN_HELP = "Помощь"
BTN_MENU = "В главное меню"

BTN_CABINET_REFRESH = "Обновить"
BTN_CABINET_RECORDS = "Мои записи"
BTN_CABINET_HISTORY = "История"
BTN_CABINET_ABONEMENT = "Абонемент"

BTN_CANCEL = "Отмена"


def main_menu(user_id: int) -> str:
    if not storage.get_phone(user_id):
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button(BTN_LOGIN, color=COLOR_BOOK)
        keyboard.add_button(BTN_BOOK_ONLINE, color=COLOR_BOOK)
        keyboard.add_line()
        keyboard.add_button(BTN_INFO, color=COLOR_MUTED)
        keyboard.add_button(BTN_CONTACT_ADMIN, color=COLOR_MUTED)
        return keyboard.get_keyboard()

    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_BOOK, color=COLOR_BOOK)
    keyboard.add_button(BTN_BOOK_AGAIN, color=COLOR_BOOK)
    keyboard.add_line()
    keyboard.add_button(BTN_NEXT_RECORD, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_CANCEL_RECORD, color=COLOR_DANGER)
    keyboard.add_line()
    keyboard.add_button(BTN_CABINET, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_SCHEDULE, color=COLOR_SCHEDULE)
    keyboard.add_button(BTN_ABONEMENT, color=COLOR_ABONEMENT)
    keyboard.add_line()
    keyboard.add_button(BTN_INFO, color=COLOR_MUTED)
    keyboard.add_button(BTN_CONTACT_ADMIN, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_LOGOUT, color=COLOR_DANGER)
    return keyboard.get_keyboard()


def info_menu(user_id: int) -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_CONTACTS, color=COLOR_MUTED)
    keyboard.add_button(BTN_FAQ, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_BOOK_ONLINE, color=COLOR_BOOK)
    keyboard.add_line()
    keyboard.add_button(BTN_HOW_TO_USE, color=COLOR_MUTED)
    if storage.get_phone(user_id):
        keyboard.add_button(BTN_CHANGE_PHONE, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_MENU, color=COLOR_MUTED)
    return keyboard.get_keyboard()


def admin_chat_menu() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_BOT_MENU, color=COLOR_MUTED)
    return keyboard.get_keyboard()


def schedule_period_menu(user_id: int) -> str:
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(BTN_SCHEDULE_TODAY, color=COLOR_MUTED)
    keyboard.add_button(BTN_SCHEDULE_TOMORROW, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_SCHEDULE_5, color=COLOR_MUTED)
    keyboard.add_button(BTN_SCHEDULE_10, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_SCHEDULE_15, color=COLOR_MUTED)
    if user_prefs.get_favorite_staff(user_id):
        keyboard.add_line()
        keyboard.add_button(BTN_SCHEDULE_MY_TRAINER, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_MENU, color=COLOR_MUTED)
    return keyboard.get_keyboard()


def cabinet_menu() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_CABINET_REFRESH, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_CABINET_RECORDS, color=COLOR_MUTED)
    keyboard.add_button(BTN_CABINET_HISTORY, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_CABINET_ABONEMENT, color=COLOR_ABONEMENT)
    keyboard.add_line()
    keyboard.add_button(BTN_FAVORITE_TRAINER, color=COLOR_MUTED)
    keyboard.add_button(BTN_PICK_TRAINER, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_MENU, color=COLOR_MUTED)
    return keyboard.get_keyboard()


def phone_input_menu() -> str:
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(BTN_CANCEL, color=COLOR_DANGER)
    keyboard.add_line()
    keyboard.add_button(BTN_MENU, color=COLOR_MUTED)
    return keyboard.get_keyboard()
