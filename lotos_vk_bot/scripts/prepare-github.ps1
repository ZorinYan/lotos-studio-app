# Проверка перед первым push на GitHub
# Запуск: .\scripts\prepare-github.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Проверка файлов перед GitHub..." -ForegroundColor Cyan
Write-Host ""

$blocked = @(
    ".env",
    "data\users.json",
    "data\reminders.json"
)

$ok = $true
foreach ($rel in $blocked) {
    $full = Join-Path $root $rel
    if (Test-Path $full) {
        Write-Host "  OK  $rel существует локально (в git не попадёт)" -ForegroundColor Green
    }
}

if (Test-Path (Join-Path $root ".env.example")) {
    Write-Host "  OK  .env.example есть" -ForegroundColor Green
} else {
    Write-Host "  !!  нет .env.example" -ForegroundColor Red
    $ok = $false
}

if (Test-Path (Join-Path $root "render.yaml")) {
    Write-Host "  OK  render.yaml есть" -ForegroundColor Green
} else {
    Write-Host "  !!  нет render.yaml" -ForegroundColor Red
    $ok = $false
}

Write-Host ""
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git не установлен. Установите: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

if (Test-Path (Join-Path $root ".git")) {
    Write-Host "Git уже инициализирован." -ForegroundColor Yellow
    git status --short
} else {
    Write-Host "Дальше выполните:" -ForegroundColor Cyan
    Write-Host "  git init"
    Write-Host "  git add ."
    Write-Host "  git status"
    Write-Host "  git commit -m `"VK bot Lotos: initial commit`""
    Write-Host "  git branch -M main"
    Write-Host "  git remote add origin https://github.com/USER/lotos-vk-bot.git"
    Write-Host "  git push -u origin main"
    Write-Host ""
    Write-Host "Подробно: DEPLOY_RENDER.md" -ForegroundColor Cyan
}

if (-not $ok) { exit 1 }
