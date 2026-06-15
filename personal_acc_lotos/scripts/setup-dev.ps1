# Быстрая настройка окружения для разработки (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "==> Lotos Mini App — setup dev" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Создан .env — заполните YCLIENTS_PARTNER_TOKEN и YCLIENTS_USER_TOKEN" -ForegroundColor Yellow
} else {
    Write-Host ".env уже есть" -ForegroundColor Green
}

Write-Host "==> npm install"
npm install

Write-Host "==> pip install (server)"
python -m pip install -r server/requirements.txt

Write-Host ""
Write-Host "Готово. Запуск в двух терминалах:" -ForegroundColor Green
Write-Host "  npm run dev:api:fresh   # если API завис — перезапуск на порту 8081"
Write-Host "  npm run dev"
Write-Host "  → http://localhost:5173"
