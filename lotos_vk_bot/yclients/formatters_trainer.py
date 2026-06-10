from utils.text_style import page_header


def format_favorite_staff(favorite: dict | None) -> str:
    if not favorite:
        return (
            f"{page_header('⭐', 'Избранный тренер')}\n\n"
            "Пока не выбран.\n\n"
            "Нажмите «Выбрать тренера» — расписание и запись\n"
            "можно будет фильтровать по нему."
        )

    return (
        f"{page_header('⭐', 'Избранный тренер')}\n\n"
        f"👤  {favorite['name']}\n\n"
        "В расписании доступна кнопка «Мой тренер».\n"
        "«Записаться снова» повторит последнее занятие с этим тренером."
    )
