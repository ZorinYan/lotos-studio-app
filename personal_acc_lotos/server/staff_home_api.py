"""Домашний экран сотрудника (заглушка под будущий функционал)."""

from __future__ import annotations

from staff_auth_service import StaffAuthError, get_staff_auth_status


def load_staff_home(vk_user_id: int) -> dict:
    status = get_staff_auth_status(vk_user_id)
    if not status.authenticated:
        raise StaffAuthError("not_authenticated", "Войдите как сотрудник.")

    return {
        "staffName": status.staff_name,
        "staffId": status.staff_id,
        "specialization": status.specialization,
        "positionTitle": status.position_title,
        "phoneDisplay": status.phone_display,
        "sections": [
            {
                "id": "schedule",
                "title": "Расписание на сегодня",
                "description": "Скоро: ваши занятия и свободные слоты.",
                "status": "coming_soon",
            },
            {
                "id": "records",
                "title": "Записи клиентов",
                "description": "Скоро: список записей на ваши тренировки.",
                "status": "coming_soon",
            },
            {
                "id": "attendance",
                "title": "Отметки посещения",
                "description": "Скоро: быстрая отметка присутствия на занятии.",
                "status": "coming_soon",
            },
        ],
    }
