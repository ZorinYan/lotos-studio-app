# Stops local API and clears stale uvicorn/python workers (Windows).
param(
    [int[]]$Ports = @(8081, 8080)
)

$ErrorActionPreference = "SilentlyContinue"

function Get-PortPids([int]$localPort) {
    Get-NetTCPConnection -LocalPort $localPort -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
}

function Get-UvicornPids {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -match 'uvicorn' -and $_.CommandLine -match 'main:app'
        } |
        Select-Object -ExpandProperty ProcessId -Unique
}

function Get-ApiServerPids {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -match 'personal_acc_lotos' -and $_.CommandLine -match 'server'
        } |
        Select-Object -ExpandProperty ProcessId -Unique
}

$targets = @()
foreach ($port in $Ports) {
    $targets += Get-PortPids $port
}
$targets += Get-UvicornPids
$targets += Get-ApiServerPids
$targets = $targets | Where-Object { $_ -gt 0 } | Select-Object -Unique

if (-not $targets) {
    Write-Host "API ports $($Ports -join ', ') are free, no uvicorn workers." -ForegroundColor Green
    exit 0
}

foreach ($procId in $targets) {
    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if (-not $proc) { continue }
    taskkill /F /T /PID $procId 2>$null | Out-Null
    Write-Host "Stopped $($proc.ProcessName) tree (PID $procId)" -ForegroundColor Yellow
}

Start-Sleep -Milliseconds 1200

$stillBusy = @()
foreach ($port in $Ports) {
    if (Get-PortPids $port) { $stillBusy += $port }
}
if ($stillBusy.Count -gt 0) {
    Write-Host "Warning: ports still in use: $($stillBusy -join ', ')" -ForegroundColor Yellow
}

Write-Host "Run: npm run dev:api:fresh" -ForegroundColor Green
