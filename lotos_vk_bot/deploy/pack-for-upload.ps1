# Создаёт архив lotos-vk-bot.zip для загрузки на сервер
# Запуск в PowerShell из корня проекта:
#   .\deploy\pack-for-upload.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$zipPath = Join-Path $root "lotos-vk-bot.zip"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

$items = @(
    "main.py",
    "config.py",
    "requirements.txt",
    "bot",
    "yclients",
    "services",
    "utils",
    "scripts",
    "deploy",
    "data/studio_info.json"
)

Push-Location $root
try {
    Compress-Archive -Path $items -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Host "Архив создан: $zipPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Не забудьте отдельно скопировать на сервер:" -ForegroundColor Yellow
    Write-Host "  - .env"
    Write-Host "  - data\users.json  (если уже есть привязанные телефоны)"
    Write-Host "  - data\studio_info.json  (контакты и FAQ студии)"
}
finally {
    Pop-Location
}
