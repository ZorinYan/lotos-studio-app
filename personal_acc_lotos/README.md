# Lotos VK Mini App

Личный кабинет клиента студии Lotos для ВКонтакте.

**Полная инструкция по клонированию и запуску на новом ПК:** [README в корне репозитория](../README.md)

## Быстрый старт

```powershell
copy .env.example .env
# заполните YCLIENTS_PARTNER_TOKEN и YCLIENTS_USER_TOKEN

.\scripts\setup-dev.ps1

# терминал 1
npm run dev:api

# терминал 2
npm run dev
```

## Скрипты

| Команда | Описание |
|---------|----------|
| `npm run dev` | Фронтенд http://localhost:5173 |
| `npm run dev:api` | API http://127.0.0.1:8080 |
| `npm run dev:mobile` | Фронт с `--host` для телефона в Wi‑Fi |
| `npm run build` | Сборка в `dist/` |

## Деплой

- Фронт: Vercel (`vercel.json`)
- API: Render (`render.yaml`)
