from datetime import date, timedelta

from vk_api.keyboard import VkKeyboard

from bot.button_colors import COLOR_BOOK, COLOR_DANGER, COLOR_MUTED
from bot.keyboards import BTN_CANCEL

BTN_ANY_STAFF = "Любой тренер"
BTN_CONFIRM_YES = "Подтвердить запись"
BTN_CONFIRM_NO = "Отмена записи"
BTN_PAGE_NEXT = "Далее ▶"
BTN_PAGE_PREV = "◀ Назад"

STAFF_PAGE_SIZE = 5
CLASS_PAGE_SIZE = 7
DAY_PAGE_SIZE = 7


def paginate(items: list, page: int, page_size: int) -> tuple[list, int, bool, bool]:
    if not items:
        return [], 0, False, False
    total_pages = (len(items) + page_size - 1) // page_size
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    return items[start : start + page_size], page, page > 0, page < total_pages - 1


def _add_nav_row(keyboard: VkKeyboard, has_prev: bool, has_next: bool) -> None:
    if not has_prev and not has_next:
        return
    keyboard.add_line()
    if has_prev and has_next:
        keyboard.add_button(BTN_PAGE_PREV, color=COLOR_MUTED)
        keyboard.add_button(BTN_PAGE_NEXT, color=COLOR_MUTED)
    elif has_prev:
        keyboard.add_button(BTN_PAGE_PREV, color=COLOR_MUTED)
    else:
        keyboard.add_button(BTN_PAGE_NEXT, color=COLOR_MUTED)


def _day_label(day: date, today: date) -> str:
    if day == today:
        return "Сегодня"
    if day == today + timedelta(days=1):
        return "Завтра"
    weekdays = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
    return f"{weekdays[day.weekday()]} {day.day:02d}.{day.month:02d}"


def make_day_map(dates: list[date]) -> dict[str, date]:
    today = date.today()
    result: dict[str, date] = {}
    used: set[str] = set()
    for day in sorted(dates):
        label = _day_label(day, today)
        if label in used:
            label = f"{label} ({day.isoformat()[5:]})"
        used.add(label)
        result[label] = day
    return result


def build_day_keyboard(day_labels: list[str], page: int = 0) -> str:
    chunk, _, has_prev, has_next = paginate(day_labels, page, DAY_PAGE_SIZE)
    keyboard = VkKeyboard(one_time=True)
    for index, label in enumerate(chunk):
        if index > 0:
            keyboard.add_line()
        keyboard.add_button(label, color=COLOR_MUTED)
    _add_nav_row(keyboard, has_prev, has_next)
    keyboard.add_line()
    keyboard.add_button(BTN_CANCEL, color=COLOR_DANGER)
    return keyboard.get_keyboard()


def build_staff_keyboard(staff_names: list[str], page: int = 0) -> str:
    chunk, _, has_prev, has_next = paginate(staff_names, page, STAFF_PAGE_SIZE)
    keyboard = VkKeyboard(one_time=True)
    for index, name in enumerate(chunk):
        if index > 0:
            keyboard.add_line()
        keyboard.add_button(name, color=COLOR_MUTED)
    if chunk:
        keyboard.add_line()
    keyboard.add_button(BTN_ANY_STAFF, color=COLOR_MUTED)
    _add_nav_row(keyboard, has_prev, has_next)
    keyboard.add_line()
    keyboard.add_button(BTN_CANCEL, color=COLOR_DANGER)
    return keyboard.get_keyboard()


def build_class_keyboard(class_labels: list[str], page: int = 0) -> str:
    chunk, _, has_prev, has_next = paginate(class_labels, page, CLASS_PAGE_SIZE)
    keyboard = VkKeyboard(one_time=True)
    for index, label in enumerate(chunk):
        if index > 0:
            keyboard.add_line()
        keyboard.add_button(label, color=COLOR_MUTED)
    _add_nav_row(keyboard, has_prev, has_next)
    keyboard.add_line()
    keyboard.add_button(BTN_CANCEL, color=COLOR_DANGER)
    return keyboard.get_keyboard()


def build_confirm_keyboard() -> str:
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(BTN_CONFIRM_YES, color=COLOR_BOOK)
    keyboard.add_line()
    keyboard.add_button(BTN_CONFIRM_NO, color=COLOR_DANGER)
    return keyboard.get_keyboard()


def page_caption(page: int, total_items: int, page_size: int) -> str:
    if total_items <= page_size:
        return ""
    total_pages = (total_items + page_size - 1) // page_size
    return f"\n\nСтраница {page + 1} из {total_pages}"
