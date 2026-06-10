# VK-бот студии «Лотос» + YClients

Бот для группы ВКонтакте: запись, расписание, кабинет, абонемент, напоминания, диалог с администратором.

## Стек

- Python 3.12
- VK API (Long Poll)
- YClients API

## Локальный запуск

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # заполните токены
python main.py
```

## Деплой

| Платформа | Инструкция |
|-----------|------------|
| **Render** (Web Service) | [DEPLOY_RENDER.md](DEPLOY_RENDER.md) |
| Oracle Cloud Free | [DEPLOY_ORACLE.md](DEPLOY_ORACLE.md) |

## Структура

```
main.py              — точка входа
bot/                 — обработчики, клавиатуры, сообщения
yclients/            — клиент и форматтеры YClients
services/            — напоминания
data/studio_info.json — контакты и FAQ (можно править)
data/users.json      — привязка VK → телефон (не в git)
.env                 — секреты (не в git)
```

## Важно

- Одновременно должен работать **только один** экземпляр бота (один Long Poll).
- Файлы `.env`, `data/users.json`, `data/reminders.json` **не коммитить** в GitHub.
