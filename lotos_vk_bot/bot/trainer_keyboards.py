from vk_api.keyboard import VkKeyboard

from bot.booking_keyboards import BTN_PAGE_NEXT, BTN_PAGE_PREV, paginate
from bot.button_colors import COLOR_DANGER, COLOR_MUTED
from bot.keyboards import BTN_MENU

BTN_CLEAR_FAVORITE = "Убрать избранного"

TRAINER_PAGE_SIZE = 6


def build_trainer_pick_keyboard(labels: list[str], page: int = 0) -> str:
    chunk, _, has_prev, has_next = paginate(labels, page, TRAINER_PAGE_SIZE)
    keyboard = VkKeyboard(one_time=True)
    for index, label in enumerate(chunk):
        if index > 0:
            keyboard.add_line()
        keyboard.add_button(label, color=COLOR_MUTED)
    if has_prev or has_next:
        keyboard.add_line()
        if has_prev and has_next:
            keyboard.add_button(BTN_PAGE_PREV, color=COLOR_MUTED)
            keyboard.add_button(BTN_PAGE_NEXT, color=COLOR_MUTED)
        elif has_prev:
            keyboard.add_button(BTN_PAGE_PREV, color=COLOR_MUTED)
        else:
            keyboard.add_button(BTN_PAGE_NEXT, color=COLOR_MUTED)
    keyboard.add_line()
    keyboard.add_button(BTN_CLEAR_FAVORITE, color=COLOR_DANGER)
    keyboard.add_line()
    keyboard.add_button(BTN_MENU, color=COLOR_MUTED)
    return keyboard.get_keyboard()
