# Lotos Studio App

Монорепозиторий студии **Lotos**:

| Папка | Назначение |
|-------|------------|
| `personal_acc_lotos/` | VK Mini App — личный кабинет клиента (React + FastAPI) |
| `lotos_vk_bot/` | VK-бот (Python, пример / общая библиотека YClients) |

API мини-приложения использует код из `lotos_vk_bot` (`yclients`, `utils`, `services`).

## Требования

- **Node.js** 20+ и npm
- **Python** 3.12+
- Токены **YClients** (partner + user) — те же, что для бота

## Быстрый старт (новый ПК)

### 1. Клонировать репозиторий

```bash
git clone https://github.com/ZorinYan/lotos-studio-app.git
cd lotos-studio-app
```

### 2. Настроить переменные окружения

```powershell
cd personal_acc_lotos
copy .env.example .env
```

Откройте `personal_acc_lotos/.env` и заполните:

- `YCLIENTS_PARTNER_TOKEN`
- `YCLIENTS_USER_TOKEN`
- при необходимости `YCLIENTS_COMPANY_ID`, `STUDIO_NAME`

Токены можно взять из рабочего `lotos_vk_bot/.env` или получить заново:

```powershell
cd ..\lotos_vk_bot
copy .env.example .env
# заполните YCLIENTS_PARTNER_TOKEN, YCLIENTS_LOGIN, YCLIENTS_PASSWORD
python scripts/get_user_token.py
```

Проверка токенов:

```powershell
python scripts/check_permissions.py
```

> Файл `personal_acc_lotos/server/.env` **не обязателен** — API читает `personal_acc_lotos/.env`.  
> Если создаёте `server/.env`, не перепутайте partner и user token.

### 3. Установить зависимости

**Автоматически (Windows):**

```powershell
cd personal_acc_lotos
.\scripts\setup-dev.ps1
```

**Вручную:**

```powershell
cd personal_acc_lotos
npm install
pip install -r server/requirements.txt
```

### 4. Запустить разработку

Нужны **два терминала** из папки `personal_acc_lotos`:

```powershell
# Терминал 1 — API (порт 8080)
npm run dev:api

# Терминал 2 — фронтенд (порт 5173)
npm run dev
```

Откройте http://localhost:5173

Проверка API: http://127.0.0.1:8080/health → `{"status":"ok"}`

### Локальная разработка без VK

В `.env` уже задано:

```
VITE_SKIP_VK_BRIDGE=true
VITE_DEV_VK_USER_ID=1
```

Приложение работает с тестовым `vk_user_id=1`.

## Сборка продакшена

```powershell
cd personal_acc_lotos
npm run build
```

Артефакты: `personal_acc_lotos/dist/`

Деплой:

- **Фронт** — Vercel (`vercel.json`)
- **API** — Render (`render.yaml`, `rootDir: server`)

## Структура мини-приложения

```
personal_acc_lotos/
├── src/              # React + VK Bridge + VKUI
├── server/           # FastAPI
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example  # опционально, для Render
├── package.json
└── .env.example      # основной файл для локальной разработки
```

## Частые проблемы

| Симптом | Решение |
|---------|---------|
| `ECONNREFUSED 127.0.0.1:8080` | Запустите `npm run dev:api` **до** `npm run dev` |
| `No module named uvicorn` | `pip install -r server/requirements.txt` |
| `No module named '_lib_path'` | Обновите репозиторий — файл `server/_lib_path.py` |
| Ошибка токенов YClients | Проверьте `.env`, не перепутаны partner/user; `check_permissions.py` |
| Нет чипов дней в расписании | Перезапустите API и фронт после обновления кода |

## VK-бот (опционально)

```powershell
cd lotos_vk_bot
copy .env.example .env
pip install -r requirements.txt
python main.py
```

Подробнее: `lotos_vk_bot/README.md`
