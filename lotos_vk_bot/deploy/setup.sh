#!/bin/bash
set -euo pipefail

APP_DIR="/home/ubuntu/lotos-vk-bot"
SERVICE_NAME="lotos-vk-bot"

echo "==> Установка системных пакетов..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-venv python3-pip

cd "$APP_DIR"

if [ ! -f ".env" ]; then
    echo ""
    echo "ОШИБКА: файл .env не найден в $APP_DIR"
    echo "Создайте его перед запуском setup.sh (скопируйте с компьютера)."
    echo "Пример: nano $APP_DIR/.env"
    exit 1
fi

echo "==> Создание виртуального окружения..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "==> Папка для данных..."
mkdir -p data

echo "==> Установка systemd-сервиса..."
sudo cp deploy/lotos-vk-bot.service /etc/systemd/system/${SERVICE_NAME}.service
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

echo "==> Запуск бота..."
sudo systemctl restart ${SERVICE_NAME}

sleep 2
sudo systemctl status ${SERVICE_NAME} --no-pager

echo ""
echo "Готово! Бот запущен."
echo "Логи:  journalctl -u ${SERVICE_NAME} -f"
echo "Стоп:  sudo systemctl stop ${SERVICE_NAME}"
echo "Старт: sudo systemctl start ${SERVICE_NAME}"
