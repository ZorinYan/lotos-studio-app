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
| `npm run dev:api` | API http://127.0.0.1:8081 (прокси из Vite) |
| `npm run dev:api:fresh` | Остановить старый API и запустить заново |
| `npm run dev:mobile` | Фронт с `--host` для телефона в Wi‑Fi |
| `npm run build` | Сборка в `dist/` |

## Деплой

- Фронт: Vercel (`vercel.json`)
- API: Render (`render.yaml`)

На Free Render API не засыпает за счёт: встроенного keep-alive (`keepalive.py`), GitHub Actions (`.github/workflows/render-keepalive.yml`) и взаимного ping с VK-ботом (`KEEPALIVE_EXTRA_URLS` в `render.yaml`).

## Авторизация

Многоуровневый вход без SMS: телефон → (пароль, если уже задан) или имя в студии → задать пароль при первом входе. `authenticated` только при телефоне и `password_hash` в БД.

На Render задайте `VK_APP_SECRET` (защищённый ключ мини-приложения) и `VK_GROUP_TOKEN` (тот же, что у бота). Локально: `SKIP_VK_SIGN=true` в `server/.env`.
