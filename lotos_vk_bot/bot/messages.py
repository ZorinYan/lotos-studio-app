from datetime import date

from config import Config
from utils.studio_info import StudioInfo
from utils.text_style import LIGHT, join_blocks, page_header

DIVIDER = "━━━━━━━━━━━━━━━"  # re-export for backward compatibility


def welcome(config: Config, first_name: str | None = None) -> str:
    greeting = f"{first_name}, добро пожаловать!" if first_name else "Добро пожаловать!"
    return (
        f"🪷  {greeting}\n\n"
        f"Студия растяжки «{config.studio_name}»\n"
        f"{LIGHT}\n\n"
        "Запись · напоминания · отмена · расписание · кабинет\n\n"
        "Выберите действие в меню 👇"
    )


def welcome_guest(config: Config, first_name: str | None = None) -> str:
    greeting = f"{first_name}, добро пожаловать!" if first_name else "Добро пожаловать!"
    return (
        f"🪷  {greeting}\n\n"
        f"Студия растяжки «{config.studio_name}»\n"
        f"{LIGHT}\n\n"
        "Войдите по номеру из студии или запишитесь онлайн.\n"
        "Контакты и ответы на вопросы — в «Справке».\n\n"
        "Выберите действие 👇"
    )


def please_login() -> str:
    return "Сначала войдите по номеру телефона из студии 👇"


def logged_out() -> str:
    return "Вы вышли из аккаунта.\n\nЧтобы снова войти, нажмите «Войти» 👇"


def login_success(phone_display: str) -> str:
    return (
        f"✅  Вы вошли ({phone_display})\n\n"
        "Теперь доступны запись, кабинет, расписание и абонемент."
    )


def ask_phone_for_login() -> str:
    return (
        f"{page_header('🔑', 'Вход')}\n\n"
        "Введите номер телефона, указанный при записи в студию.\n\n"
        "Например:  89991234567"
    )


def help_text() -> str:
    return (
        f"{page_header('ℹ️', 'Как пользоваться ботом')}\n\n"
        "1️⃣  «Записаться»\n"
        "    день → тренер → занятие\n\n"
        "2️⃣  «Отменить запись»\n"
        "    выбор и подтверждение отмены\n\n"
        "3️⃣  «Расписание»\n"
        "    сегодня, завтра или на несколько дней\n\n"
        "4️⃣  «Личный кабинет»\n"
        "    профиль, записи, история\n\n"
        "5️⃣  «Мой абонемент»\n"
        "    остаток занятий\n\n"
        "📅  «Ближайшая запись» — одним нажатием\n"
        "🔁  «Записаться снова» — повтор прошлого занятия\n\n"
        "⭐  «Избранный тренер» — в личном кабинете\n"
        "    в расписании появится «Мой тренер»\n\n"
        "ℹ️  «Справка» — контакты, FAQ, онлайн-запись\n\n"
        "🔐  При первом входе и смене номера бот попросит\n"
        "    имя из студии — так чужой не воспользуется вашим номером.\n\n"
        f"{LIGHT}\n\n"
        "📱  Сменили номер — «Изменить номер»\n"
        "💬  Вопрос администратору — «Написать администратору»\n"
        "    бот не будет отвечать, пока вы переписываетесь со студией\n\n"
        "🚪  Выйти из аккаунта — «Выйти»\n"
        "🏠  В главное меню — соответствующая кнопка"
    )


def admin_chat_started(config: Config) -> str:
    return (
        f"{page_header('💬', 'Диалог со студией')}\n\n"
        "Напишите сообщение — его увидит администратор и ответит лично.\n"
        "Бот сейчас не мешает переписке.\n\n"
        f"Студия «{config.studio_name}» обычно отвечает в рабочее время.\n\n"
        "Чтобы снова пользоваться ботом, нажмите «Меню бота» 👇"
    )


def info_menu_intro(config: Config) -> str:
    return (
        f"{page_header('ℹ️', 'Справка')}\n\n"
        f"Студия растяжки «{config.studio_name}»\n\n"
        "Контакты, ответы на частые вопросы и онлайн-запись 👇"
    )


def format_contacts(config: Config, info: StudioInfo) -> str:
    lines = [page_header("📍", "Контакты"), ""]
    if info.address:
        lines.append(f"🏠  {info.address}")
    if info.work_hours:
        lines.append(f"🕐  {info.work_hours}")
    if info.phone:
        lines.append(f"📞  {info.phone}")
    if info.parking:
        lines.append(f"🅿️  {info.parking}")
    if info.extra:
        lines.append(f"💡  {info.extra}")
    if info.map_url:
        lines.append(f"\n🗺  Карта:\n    {info.map_url}")
    if len(lines) <= 2:
        lines.append("Данные пока не заполнены. Напишите администратору.")
    return "\n".join(lines)


def format_faq(info: StudioInfo) -> str:
    if not info.faq:
        return (
            f"{page_header('❓', 'Вопросы и ответы')}\n\n"
            "Раздел пока не заполнен. Напишите администратору."
        )

    blocks = []
    for index, item in enumerate(info.faq, 1):
        blocks.append(f"❓  {item.question}\n\n    {item.answer}")

    body = join_blocks(blocks)
    return f"{page_header('❓', 'Вопросы и ответы')}\n\n{body}"


def book_online(config: Config) -> str:
    return (
        f"{page_header('🌐', 'Онлайн-запись')}\n\n"
        "Первая запись или удобнее через сайт — откройте ссылку:\n"
        f"    {config.yclients_booking_url}\n\n"
        "Там откроется окно записи YClients.\n"
        "После записи можно войти в бота по номеру телефона."
    )


def loading_next_record() -> str:
    return "⏳  Ищу вашу ближайшую запись..."


def no_upcoming_record(config: Config) -> str:
    return (
        f"{page_header('📅', 'Ближайшая запись')}\n\n"
        "Предстоящих занятий нет.\n\n"
        "Запишитесь через «Записаться» в меню или онлайн:\n"
        f"    {config.yclients_booking_url}"
    )


def loading_trainers() -> str:
    return "⏳  Загружаю список тренеров..."


def loading_schedule_trainer(name: str, days: int) -> str:
    return f"⏳  Расписание · {name} · {days} дн...."


def choose_favorite_trainer() -> str:
    return (
        f"{page_header('⭐', 'Избранный тренер')}\n\n"
        "Выберите тренера из расписания ближайших двух недель:"
    )


def favorite_trainer_saved(name: str) -> str:
    return f"⭐  Избранный тренер: {name}\n\nВ расписании появится кнопка «Мой тренер»."


def favorite_trainer_cleared() -> str:
    return "Избранный тренер убран."


def favorite_trainer_not_set() -> str:
    return (
        f"{page_header('⭐', 'Мой тренер')}\n\n"
        "Сначала выберите избранного тренера:\n"
        "Личный кабинет → «Избранный тренер» → «Выбрать тренера»."
    )


def no_trainers_for_pick() -> str:
    return "Не удалось загрузить тренеров из расписания. Попробуйте позже."


def book_again_unavailable() -> str:
    return (
        f"{page_header('🔁', 'Записаться снова')}\n\n"
        "Пока нет данных о прошлой записи.\n\n"
        "Сначала запишитесь через «Записаться» — "
        "в следующий раз бот предложит повтор."
    )


def book_again_no_slots(staff_name: str, service_title: str) -> str:
    return (
        f"{page_header('🔁', 'Записаться снова')}\n\n"
        f"Сейчас нет свободных занятий:\n"
        f"    👤  {staff_name}\n"
        f"    📌  {service_title}\n\n"
        "Попробуйте «Записаться» и выберите другой день."
    )


def book_again_choose() -> str:
    return (
        f"{page_header('🔁', 'Записаться снова')}\n\n"
        "Выберите удобное время:"
    )


def ask_phone() -> str:
    return (
        f"{page_header('📱', 'Введите номер телефона')}\n\n"
        "Укажите тот же номер, что при записи в студию.\n\n"
        "Например:\n"
        "    •  89991234567\n"
        "    •  +7 999 123-45-67"
    )


def ask_phone_change() -> str:
    return (
        f"{page_header('📱', 'Новый номер телефона')}\n\n"
        "Введите актуальный номер, привязанный к абонементу в студии."
    )


def phone_saved() -> str:
    return "✅  Номер сохранён — в следующий раз всё откроется сразу."


def loading_phone_check() -> str:
    return "⏳  Проверяю номер в студии..."


def loading_name_check() -> str:
    return "⏳  Сверяю имя..."


def ask_client_name(*, with_surname: bool) -> str:
    if with_surname:
        return (
            f"{page_header('👤', 'Подтверждение')}\n\n"
            "Введите имя и фамилию так, как указано в студии.\n\n"
            "Например:  Иван Иванов"
        )
    return (
        f"{page_header('👤', 'Подтверждение')}\n\n"
        "Введите имя так, как указано в студии.\n\n"
        "Например:  Иван"
    )


def invalid_client_name() -> str:
    return (
        f"{page_header('❌', 'Введите имя')}\n\n"
        "Напишите имя (и фамилию, если она есть в студии)."
    )


def name_verification_failed(config: Config) -> str:
    return (
        f"{page_header('🔒', 'Не удалось подтвердить')}\n\n"
        "Имя не совпадает с данными в студии.\n\n"
        "Проверьте номер и попробуйте снова или запишитесь онлайн:\n"
        f"    {config.yclients_booking_url}\n\n"
        "Там откроется окно записи YClients."
    )


def ask_phone_for_cabinet() -> str:
    return (
        f"{page_header('👤', 'Личный кабинет')}\n\n"
        "Для входа нужен номер телефона из студии.\n"
        "Он сохранится — в следующий раз откроется сразу.\n\n"
        "Введите номер, например:  89991234567"
    )


def loading() -> str:
    return "⏳  Ищу ваш абонемент..."


def loading_cabinet() -> str:
    return "⏳  Загружаю личный кабинет..."


def loading_records() -> str:
    return "⏳  Загружаю ваши записи..."


def loading_history() -> str:
    return "⏳  Загружаю историю посещений..."


def loading_abonement(phone_display: str) -> str:
    return f"⏳  Проверяю абонемент ({phone_display})..."


def schedule_choose_period() -> str:
    return f"{page_header('📅', 'Расписание занятий')}\n\nВыберите период:"


def loading_schedule(days: int) -> str:
    return f"⏳  Загружаю расписание на {days} дн...."


def loading_schedule_day(label: str) -> str:
    return f"⏳  Загружаю расписание · {label}..."


def ask_phone_for_booking() -> str:
    return (
        f"{page_header('📅', 'Запись на занятие')}\n\n"
        "Для записи нужен номер телефона из студии.\n"
        "Он сохранится — в следующий раз откроется сразу.\n\n"
        "Введите номер, например:  89991234567"
    )


def loading_booking() -> str:
    return "⏳  Ищу свободные занятия..."


def loading_booking_submit() -> str:
    return "⏳  Создаю запись..."


def booking_choose_day() -> str:
    return f"{page_header('📅', 'Запись на занятие')}\n\nВыберите день:"


def booking_choose_staff(day: date) -> str:
    weekdays = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
    day_label = f"{weekdays[day.weekday()]}, {day.day:02d}.{day.month:02d}"
    return f"{page_header('👤', f'Тренер · {day_label}')}\n\nК кому записаться?"


def booking_choose_class() -> str:
    return f"{page_header('🧘', 'Занятие')}\n\nВыберите время и занятие:"


def booking_confirm(activity_card: str) -> str:
    return (
        f"{page_header('✅', 'Подтвердите запись')}\n\n"
        f"{activity_card}\n\n"
        "Всё верно?"
    )


def booking_no_slots() -> str:
    return (
        f"{page_header('😔', 'Нет свободных мест')}\n\n"
        "Попробуйте позже или напишите администратору студии."
    )


def booking_day_empty() -> str:
    return (
        "На этот день свободных мест уже нет.\n\n"
        "Выберите другой день 👇"
    )


def booking_no_classes_for_staff() -> str:
    return (
        "У выбранного тренера нет свободных занятий.\n\n"
        "Выберите другого тренера 👇"
    )


def booking_cancelled() -> str:
    return "Запись отменена. Вы в главном меню 🪷"


def ask_phone_for_cancel() -> str:
    return (
        f"{page_header('🗑', 'Отмена записи')}\n\n"
        "Для отмены нужен номер телефона из студии.\n"
        "Он сохранится — в следующий раз откроется сразу.\n\n"
        "Введите номер, например:  89991234567"
    )


def record_cancel_confirm(record_card: str) -> str:
    return (
        f"{page_header('⚠️', 'Подтвердите отмену')}\n\n"
        f"{record_card}\n\n"
        "Точно отменить эту запись?"
    )


def record_cancel_failed(detail: str) -> str:
    return (
        f"{page_header('😔', 'Не удалось отменить')}\n\n"
        f"{detail}\n\n"
        "Возможно, до занятия осталось слишком мало времени.\n"
        "Напишите администратору студии."
    )


def record_kept() -> str:
    return "Запись сохранена. Вы в главном меню 🪷"


def loading_record_cancel() -> str:
    return "⏳  Отменяю запись..."


def booking_failed(detail: str) -> str:
    return (
        f"{page_header('😔', 'Не удалось записаться')}\n\n"
        f"{detail}\n\n"
        "Попробуйте другое занятие или обратитесь в студию."
    )


def client_not_found(config: Config) -> str:
    return (
        f"{page_header('🔍', 'Клиент не найден')}\n\n"
        "По этому номеру нет карточки в студии.\n\n"
        "Если вы ещё не записывались — оформите первую запись онлайн:\n"
        f"    {config.yclients_booking_url}\n\n"
        "Там откроется окно записи YClients."
    )


def action_cancelled() -> str:
    return "Действие отменено. Вы в главном меню 🪷"


def unknown_command() -> str:
    return "Не совсем понял 🤔\n\nВыберите действие в меню ниже 👇"


def invalid_phone() -> str:
    return (
        f"{page_header('❌', 'Не удалось распознать номер')}\n\n"
        "Попробуйте ещё раз, например:\n"
        "    89991234567"
    )


def service_unavailable() -> str:
    return (
        f"{page_header('😔', 'Сервис временно недоступен')}\n\n"
        "Пожалуйста, напишите администратору студии — "
        "мы поможем проверить абонемент вручную."
    )


def fetch_error(detail: str) -> str:
    return (
        f"{page_header('😔', 'Не удалось загрузить данные')}\n\n"
        f"Попробуйте чуть позже или обратитесь в студию.\n\n"
        f"    ({detail})"
    )
