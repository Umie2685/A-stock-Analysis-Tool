$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $projectRoot ".devspace-run\cloudflared.pid"

if (!(Test-Path -LiteralPath $pidFile)) {
    Write-Host "No cloudflared PID file found. Nothing to stop." -ForegroundColor Yellow
    exit 0
}

$cloudflaredPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()
if ($cloudflaredPid -notmatch '^\d+$') {
    Write-Host "Invalid PID file: $pidFile" -ForegroundColor Yellow
    exit 1
}

$process = Get-Process -Id ([int]$cloudflaredPid) -ErrorAction SilentlyContinue
if (!$process) {
    Write-Host "cloudflared process $cloudflaredPid is not running." -ForegroundColor Yellow
    Remove-Item -LiteralPath $pidFile -ErrorAction SilentlyContinue
    exit 0
}

if ($process.ProcessName -ne "cloudflared") {
    Write-Host "PID $cloudflaredPid is $($process.ProcessName), not cloudflared. Refusing to stop it." -ForegroundColor Yellow
    exit 1
}

Stop-Process -Id $process.Id
Remove-Item -LiteralPath $pidFile -ErrorAction SilentlyContinue
Write-Host "Stopped cloudflared process $cloudflaredPid." -ForegroundColor Green
