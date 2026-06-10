# Деплой бота на Oracle Cloud Free

Пошаговая инструкция: что сделать в Oracle Cloud и что на вашем компьютере.

**Важно:** перед деплоем **остановите бота на своём ПК** (`Ctrl+C` в терминале).  
На сервере и на ПК одновременно бот работать не должен.

---

## Часть 1. Oracle Cloud (регистрация и сервер)

### Шаг 1. Регистрация

1. Откройте https://www.oracle.com/cloud/free/
2. Нажмите **Start for free** и создайте аккаунт.
3. Потребуется карта (списания не будет, если не выйти за лимиты Always Free).
4. Выберите регион ближе к России, например **Germany Central (Frankfurt)**.

### Шаг 2. Создать виртуальную машину (VM)

1. Войдите в консоль: https://cloud.oracle.com
2. Меню ☰ → **Compute** → **Instances** → **Create instance**.

Заполните:

| Поле | Значение |
|------|----------|
| Name | `lotos-vk-bot` |
| Compartment | оставить по умолчанию |
| Image | **Canonical Ubuntu 22.04** (или 24.04) |
| Shape | **Ampere** → `VM.Standard.A1.Flex` → 1 OCPU, 6 GB RAM (бесплатно) |
| | Если Ampere недоступен: **AMD** → `VM.Standard.E2.1.Micro` (тоже free) |
| Networking | оставить VCN по умолчанию |
| Public IP | **Assign a public IPv4 address** ✓ |

**SSH keys** (выберите один вариант):

- **Вариант А (проще):** скачайте приватный ключ `ssh-key-*.key` — сохраните, он понадобится для PuTTY/WinSCP.
- **Вариант Б:** вставьте свой публичный ключ, если умеете генерировать.

3. Нажмите **Create**.
4. Дождитесь статуса **Running** (зелёный).
5. Скопируйте **Public IP address** — например `123.45.67.89`.

### Шаг 3. Открыть SSH (порт 22)

1. На странице инстанса кликните имя **Subnet** (в разделе Primary VNIC).
2. Слева **Security Lists** → откройте список по умолчанию.
3. **Add Ingress Rules**:

| Поле | Значение |
|------|----------|
| Source CIDR | `0.0.0.0/0` (или ваш IP/32 — безопаснее) |
| IP Protocol | TCP |
| Destination Port | 22 |

4. **Add Ingress Rules**.

Другие порты открывать **не нужно** — бот сам ходит в VK и YClients.

---

## Часть 2. На вашем компьютере (Windows)

### Шаг 4. Подготовить архив проекта

Откройте PowerShell в папке проекта:

```powershell
cd C:\WEB\lotos_vk_bot
.\deploy\pack-for-upload.ps1
```

Появится файл `C:\WEB\lotos_vk_bot\lotos-vk-bot.zip`.

### Шаг 5. Загрузить файлы на сервер

**Способ 1 — WinSCP (удобнее):**

1. Скачайте WinSCP: https://winscp.net
2. Подключение:
   - Host: `ваш Public IP`
   - User: `ubuntu`
   - Private key: файл `.key` из Oracle (в WinSCP: Advanced → SSH → Authentication)
3. Загрузите на сервер в `/home/ubuntu/`:
   - `lotos-vk-bot.zip`
   - `.env` (из папки проекта)
   - `data\users.json` — если файл уже есть и нужны сохранённые телефоны

**Способ 2 — PowerShell (если есть OpenSSH):**

```powershell
scp C:\WEB\lotos_vk_bot\lotos-vk-bot.zip ubuntu@ВАШ_IP:/home/ubuntu/
scp C:\WEB\lotos_vk_bot\.env ubuntu@ВАШ_IP:/home/ubuntu/
```

---

## Часть 3. На сервере (SSH)

### Шаг 6. Подключиться по SSH

**PowerShell:**

```powershell
ssh -i C:\путь\к\ssh-key-XXXX.key ubuntu@ВАШ_IP
```

**PuTTY:** загрузите `.key` через PuTTYgen → сохраните `.ppk` → подключитесь как `ubuntu`.

### Шаг 7. Распаковать и установить

Выполните на сервере по очереди:

```bash
cd /home/ubuntu
unzip -o lotos-vk-bot.zip -d lotos-vk-bot
cd lotos-vk-bot

# Перенести .env в папку проекта (если загрузили в /home/ubuntu/)
mv /home/ubuntu/.env . 2>/dev/null || true

# Проверить, что .env на месте
ls -la .env

# Папка данных
mkdir -p data
# Если загружали users.json:
mv /home/ubuntu/users.json data/ 2>/dev/null || true

# Установка и запуск
chmod +x deploy/setup.sh
./deploy/setup.sh
```

Если всё ок, в конце увидите `active (running)`.

### Шаг 8. Проверить бота

1. Напишите сообществу VK в личные сообщения.
2. На сервере смотрите логи:

```bash
journalctl -u lotos-vk-bot -f
```

Выход из логов: `Ctrl+C`.

---

## Полезные команды на сервере

```bash
# Статус
sudo systemctl status lotos-vk-bot

# Перезапуск (после обновления кода)
sudo systemctl restart lotos-vk-bot

# Остановить
sudo systemctl stop lotos-vk-bot

# Логи за последний час
journalctl -u lotos-vk-bot --since "1 hour ago"
```

---

## Обновление бота (когда меняете код)

**На ПК:**

```powershell
cd C:\WEB\lotos_vk_bot
.\deploy\pack-for-upload.ps1
scp lotos-vk-bot.zip ubuntu@ВАШ_IP:/home/ubuntu/
```

**На сервере:**

```bash
sudo systemctl stop lotos-vk-bot
cd /home/ubuntu
unzip -o lotos-vk-bot.zip -d lotos-vk-bot
cd lotos-vk-bot
./venv/bin/pip install -r requirements.txt
sudo systemctl start lotos-vk-bot
```

Файлы `.env` и `data/users.json` при этом **не перезаписываются**, если вы их не трогаете.

---

## Частые проблемы

### Ampere (A1) недоступен при создании

Выберите **AMD** `VM.Standard.E2.1.Micro` или попробуйте другой регион (Frankfurt, Amsterdam).

### `Connection refused` при SSH

- Проверьте Ingress Rule для порта 22.
- Убедитесь, что инстанс в статусе **Running**.
- Проверьте правильный Public IP.

### Бот не отвечает в VK

```bash
journalctl -u lotos-vk-bot -n 50
```

Частые причины:
- ошибка в `.env` (проверьте `nano /home/ubuntu/lotos-vk-bot/.env`);
- бот всё ещё запущен на вашем ПК;
- неверный `VK_GROUP_TOKEN`.

### `unzip: command not found`

```bash
sudo apt-get update && sudo apt-get install -y unzip
```

---

## Чеклист

- [ ] Oracle: VM создана, статус Running
- [ ] Oracle: открыт порт 22
- [ ] ПК: бот остановлен локально
- [ ] ПК: создан `lotos-vk-bot.zip`
- [ ] Сервер: загружены zip + `.env`
- [ ] Сервер: выполнен `./deploy/setup.sh`
- [ ] VK: бот отвечает на сообщение
- [ ] Ссылка на бот для клиентов: `https://vk.me/КОРОТКОЕ_ИМЯ_ГРУППЫ`

---

## Содержимое `.env` на сервере

```
VK_GROUP_TOKEN=...
YCLIENTS_PARTNER_TOKEN=...
YCLIENTS_USER_TOKEN=...
YCLIENTS_COMPANY_ID=44598
STUDIO_NAME=Лотос
```

Файл `.env` **никому не показывайте** и не выкладывайте в интернет.
