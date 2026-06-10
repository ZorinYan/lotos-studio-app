# Деплой бота на GitHub + Render

Пошаговая инструкция: залить код на GitHub и запустить бота на [Render](https://render.com).

**Важно перед стартом**

1. **Остановите бота на своём ПК** (`Ctrl+C` в терминале) — одновременно два экземпляра работать не должны.
2. Бот использует **VK Long Poll** + **HTTP health-check** на `/health` (для Render Web Service).
3. Тип сервиса на Render: **Web Service** (не Background Worker).

---

## Часть 1. Подготовка проекта (на вашем ПК)

### Шаг 1. Проверьте, что не попадёт в GitHub

В репозиторий **не должны** уйти секреты и данные клиентов:

| Файл | Почему |
|------|--------|
| `.env` | токены VK и YClients |
| `data/users.json` | телефоны клиентов |
| `data/reminders.json` | служебные данные |

Это уже прописано в `.gitignore`.

**Можно и нужно** коммитить:

- весь код (`bot/`, `yclients/`, `main.py`, …)
- `data/studio_info.json` — контакты и FAQ
- `.env.example` — шаблон без секретов
- `render.yaml` — конфиг Render

### Шаг 2. Заполните `data/studio_info.json`

Проверьте адрес, телефон, часы работы и FAQ — этот файл уедет в GitHub.

### Шаг 3. Убедитесь, что бот работает локально

```powershell
cd C:\WEB\lotos_vk_bot
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
# .env должен быть заполнен
python main.py
```

Напишите боту в VK — должен ответить. Остановите: `Ctrl+C`.

---

## Часть 2. GitHub

### Шаг 4. Создайте репозиторий на GitHub

1. Откройте https://github.com/new
2. Имя, например: `lotos-vk-bot`
3. **Private** (рекомендуется — код студии)
4. Без README / .gitignore (они уже есть в проекте)
5. **Create repository**

### Шаг 5. Залейте код (PowerShell)

```powershell
cd C:\WEB\lotos_vk_bot

git init
git add .
git status
```

Убедитесь, что в списке **нет** `.env`, `data/users.json`, `data/reminders.json`.

```powershell
git commit -m "VK bot Lotos: initial commit"
git branch -M main
git remote add origin https://github.com/ВАШ_ЛОГИН/lotos-vk-bot.git
git push -u origin main
```

При первом `push` GitHub попросит войти (браузер или Personal Access Token).

### Шаг 6. Personal Access Token (если Git просит пароль)

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. **Generate new token** → отметьте `repo`
3. Скопируйте токен — используйте его вместо пароля при `git push`

---

## Часть 3. Render

### Шаг 7. Регистрация

1. https://render.com → **Get Started**
2. Войдите через **GitHub** — дайте доступ к репозиторию `lotos-vk-bot`

### Шаг 8. Создание Web Service (способ А — через Blueprint, проще)

1. Render Dashboard → **New** → **Blueprint**
2. Подключите репозиторий `lotos-vk-bot`
3. Render прочитает `render.yaml` из корня проекта
4. Нажмите **Apply**

Появится сервис `lotos-vk-bot` типа **Web Service**.

### Шаг 8 (альтернатива). Создание Web Service вручную (способ Б)

1. **New** → **Web Service**
2. Подключите репозиторий GitHub
3. Заполните:

| Поле | Значение |
|------|----------|
| Name | `lotos-vk-bot` |
| Region | `Frankfurt` (ближе к РФ) |
| Branch | `main` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| **Start Command** | `python main.py` |
| Plan | **Free** или Starter |
| Health Check Path | `/health` |

Render сам задаёт переменную `PORT` — бот поднимает на нём health-check сервер.

### Шаг 9. Переменные окружения (Environment)

В Render: сервис `lotos-vk-bot` → **Environment** → добавьте:

| Key | Value | Секрет? |
|-----|-------|---------|
| `VK_GROUP_TOKEN` | токен сообщества VK | ✅ Secret |
| `YCLIENTS_PARTNER_TOKEN` | partner token YClients | ✅ Secret |
| `YCLIENTS_USER_TOKEN` | user token YClients | ✅ Secret |
| `YCLIENTS_COMPANY_ID` | `44598` | |
| `STUDIO_NAME` | `Лотос` | |
| `YCLIENTS_BOOKING_URL` | `https://n1996926.yclients.com/` | |
| `REMINDER_MINUTES_BEFORE` | `60` | |
| `REMINDER_CHECK_INTERVAL_SEC` | `120` | |
| `PYTHON_VERSION` | `3.12.0` | |

Скопируйте значения из вашего локального `.env`.  
Файл `.env` на Render **загружать не нужно** — только переменные в Dashboard.

Нажмите **Save Changes** — Render пересоберёт и запустит бота.

### Шаг 10. Проверка

1. **Logs** в Render — должно быть:
   ```
   Бот запущен
   Режим Web Service (Render): health-check на PORT=...
   Health-check сервер: 0.0.0.0:... (/health)
   Long Poll запущен
   Напоминания запущены: за 60 мин...
   ```
2. Откройте URL сервиса в браузере: `https://lotos-vk-bot.onrender.com/health` — должно быть `ok`.
2. Напишите боту в VK — должен ответить.
3. Локальный бот на ПК **должен быть выключен**.

---

## Часть 4. Обновление бота

После изменений в коде:

```powershell
cd C:\WEB\lotos_vk_bot
git add .
git commit -m "описание изменений"
git push
```

Render с `autoDeploy: true` (в `render.yaml`) задеплоит автоматически через 2–5 минут.

Ручной деплой: Dashboard → **Manual Deploy** → **Deploy latest commit**.

---

## Данные клиентов на Render (важно!)

Бот хранит привязку «VK → телефон» в `data/users.json` на диске сервера.

На Render диск **временный**: при **пересборке** или **новом деплое** файл может **обнулиться**. Клиентам придётся снова нажать **«Войти»**.

**Варианты:**

| Вариант | Плюсы | Минусы |
|---------|-------|--------|
| Ничего не делать | бесплатно | после деплоя клиенты входят заново |
| [Persistent Disk](https://render.com/docs/disks) на Render | данные сохраняются | ~$0.25/ГБ в месяц, настройка mount |
| Oracle Cloud (см. DEPLOY_ORACLE.md) | бесплатный VPS, постоянный диск | сложнее настройка |

Для студии с десятками клиентов обычно достаточно первого варианта — перелогин после редких обновлений.

---

## Логи и диагностика

| Задача | Где |
|--------|-----|
| Логи бота | Render → сервис → **Logs** |
| Ошибка при старте | Logs, строка `RuntimeError: Заполните переменные` → не хватает env |
| Бот не отвечает | Проверьте: локальный бот выключен, `VK_GROUP_TOKEN` верный, Long Poll включён в VK |
| Два бота сразу | VK будет слать события то одному, то другому — остановите лишний |

### Включить Long Poll в VK

Сообщество → **Управление** → **Работа с API** → **Long Poll API** → **Включено**.

---

## Чеклист

- [ ] Локальный бот остановлен
- [ ] `.env` не в git (`git status` чистый от секретов)
- [ ] Репозиторий на GitHub создан (лучше Private)
- [ ] Render Web Service создан
- [ ] `/health` открывается и показывает `ok`
- [ ] Все переменные окружения заданы
- [ ] В логах Render: «Бот запущен»
- [ ] Бот отвечает в VK
- [ ] `data/studio_info.json` с актуальными контактами

---

## Как не дать боту засыпать (Free Web Service)

На Free Render «усыпляет» сервис без входящих HTTP-запросов. Пока спит — Long Poll не работает.

### Способ 1. Встроенный keep-alive (уже в боте)

На Render автоматически есть переменная `RENDER_EXTERNAL_URL`.  
Бот сам раз в **10 минут** открывает свой `/health` и не даёт сервису заснуть.

В логах после деплоя:
```
Keep-alive: https://lotos-vk-bot.onrender.com/health каждые 600 сек
```

Ничего настраивать не нужно, если задеплоена актуальная версия кода.

Опционально в Environment:

| Переменная | Значение | Зачем |
|------------|----------|--------|
| `KEEPALIVE_INTERVAL_SEC` | `600` | интервал ping (сек), минимум 300 |
| `KEEPALIVE_ENABLED` | `false` | отключить keep-alive |
| `KEEPALIVE_URL` | URL сервиса | если `RENDER_EXTERNAL_URL` нет |

### Способ 2. Внешний мониторинг (запасной)

Если встроенный ping не помогает:

1. https://uptimerobot.com (бесплатно)
2. **Add monitor** → тип **HTTP(s)**
3. URL: `https://ваш-сервис.onrender.com/health`
4. Interval: **5 minutes**
5. Сохранить

Или https://cron-job.org — GET на `/health` каждые 10 мин.

### Способ 3. Платный план Starter (~$7/мес)

Render **не усыпляет** платные Web Service — самый надёжный вариант для студии.

---

## Стоимость (ориентир)

| Пункт | Цена |
|-------|------|
| GitHub Private | бесплатно |
| Render Web Service Free | бесплатно (см. ограничения ниже) |
| Render Web Service Starter | ~$7/мес (без «засыпания») |
| Persistent Disk (опционально) | от ~$0.25/мес |

---

## Частые ошибки

**`Application failed to respond`**  
Проверьте Start Command: `python main.py`. Должен отвечать `/health`.  
Убедитесь, что задеплоена **последняя** версия с `health_server.py`.

**Бот «засыпает» на Free**  
На бесплатном Web Service Render останавливает инстанс после ~15 мин без HTTP-трафика.  
См. раздел **«Как не дать боту засыпать»** ниже.

**`Заполните переменные в .env`**  
На Render не заданы `VK_GROUP_TOKEN` / токены YClients в Environment.

**Бот отвечал и перестал после деплоя**  
Смотрите Logs. Часто — неверный токен или запущена вторая копия на ПК.

**Напоминания не приходят**  
Клиент должен нажать «Войти» на Render-версии (после деплоя `users.json` пустой).
