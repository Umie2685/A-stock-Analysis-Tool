$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runDir = Join-Path $projectRoot ".devspace-run"
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

$port = 7676
$originUrl = "http://127.0.0.1:$port"
$cloudflaredLog = Join-Path $runDir "cloudflared.log"
$cloudflaredPidFile = Join-Path $runDir "cloudflared.pid"
$devspaceCmdFile = Join-Path $runDir "run-devspace.cmd"

function Resolve-CommandPath {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$Fallbacks = @()
    )

    $found = Get-Command $Command -ErrorAction SilentlyContinue
    if ($found) {
        return $found.Source
    }

    foreach ($fallback in $Fallbacks) {
        if (Test-Path -LiteralPath $fallback) {
            return $fallback
        }
    }

    throw "Could not find $Command. Install it first or add it to PATH."
}

function Wait-ForTunnelUrl {
    param(
        [Parameter(Mandatory = $true)][string[]]$LogPaths,
        [int]$TimeoutSeconds = 90
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        foreach ($logPath in $LogPaths) {
            if (-not (Test-Path -LiteralPath $logPath)) {
                continue
            }

            $text = Get-Content -LiteralPath $logPath -Raw -ErrorAction SilentlyContinue
            if ([string]::IsNullOrWhiteSpace($text)) {
                continue
            }

            $match = [regex]::Match([string]$text, 'https://[a-z0-9-]+\.trycloudflare\.com')
            if ($match.Success) {
                return $match.Value
            }
        }
        Start-Sleep -Seconds 1
    }

    throw "Timed out waiting for cloudflared to print a trycloudflare.com URL. See: $($LogPaths -join ', ')"
}

$existingPort = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($existingPort) {
    Write-Host "Port $port is already in use by process id $($existingPort.OwningProcess)." -ForegroundColor Yellow
    Write-Host "Close the existing DevSpace server first, then run START-DEVSPACE.cmd again." -ForegroundColor Yellow
    exit 1
}

$cloudflared = Resolve-CommandPath -Command "cloudflared.exe" -Fallbacks @(
    "C:\Program Files\cloudflared\cloudflared.exe",
    "C:\Program Files (x86)\cloudflared\cloudflared.exe"
)
$devspace = Resolve-CommandPath -Command "devspace.cmd"

$cloudflaredStdoutLog = Join-Path $runDir "cloudflared.stdout.log"
$cloudflaredStderrLog = Join-Path $runDir "cloudflared.stderr.log"
Remove-Item -LiteralPath $cloudflaredLog -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $cloudflaredStdoutLog -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $cloudflaredStderrLog -ErrorAction SilentlyContinue

Write-Host "Starting Cloudflare quick tunnel..." -ForegroundColor Cyan

$cloudflaredProcess = Start-Process -FilePath $cloudflared `
    -ArgumentList @("tunnel", "--url", $originUrl) `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $cloudflaredStdoutLog `
    -RedirectStandardError $cloudflaredStderrLog `
    -WindowStyle Hidden `
    -PassThru
Set-Content -LiteralPath $cloudflaredPidFile -Value $cloudflaredProcess.Id

$publicBaseUrl = Wait-ForTunnelUrl -LogPaths @($cloudflaredLog, $cloudflaredStdoutLog, $cloudflaredStderrLog) -TimeoutSeconds 90
$mcpUrl = "$publicBaseUrl/mcp"
$ownerTokenCopyCommand = '(Get-Content "' + '$env:USERPROFILE' + '\.devspace\auth.json" -Raw | ConvertFrom-Json).ownerToken | Set-Clipboard'

Write-Host ""
Write-Host "Tunnel ready:" -ForegroundColor Green
Write-Host "  Public base URL: $publicBaseUrl"
Write-Host "  MCP client URL:  $mcpUrl"
Write-Host ""
Write-Host "Owner password copy command:" -ForegroundColor Cyan
Write-Host "``````powershell"
Write-Host $ownerTokenCopyCommand
Write-Host "``````"
Write-Host ""

Write-Host "Updating DevSpace publicBaseUrl..." -ForegroundColor Cyan
& $devspace config set publicBaseUrl $publicBaseUrl | Write-Host

$devspaceCmd = @"
@echo off
title DevSpace Server - AStockFastLane
cd /d "$projectRoot"
set "DEVSPACE_ALLOWED_ROOTS=$projectRoot"
set "DEVSPACE_PUBLIC_BASE_URL=$publicBaseUrl"
set "DEVSPACE_ALLOWED_HOSTS=localhost,127.0.0.1,::1,$($publicBaseUrl -replace '^https?://','')"
set "DEVSPACE_TOOL_MODE=full"
set "DEVSPACE_TOOL_NAMING=legacy"
set "DEVSPACE_WIDGETS=changes"
echo DevSpace allowed root:
echo   $projectRoot
echo.
echo Public base URL:
echo   $publicBaseUrl
echo MCP client URL:
echo   $mcpUrl
echo.
echo DevSpace tool mode:
echo   full, legacy names, changes widget
echo.
"$devspace" serve
echo.
echo DevSpace stopped. Press any key to close this window.
pause >nul
"@
Set-Content -LiteralPath $devspaceCmdFile -Value $devspaceCmd -Encoding ASCII

Write-Host "Starting DevSpace server in a separate window..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "`"$devspaceCmdFile`"") -WorkingDirectory $projectRoot

Write-Host ""
Write-Host "Use these values in ChatGPT DevSpace connection:" -ForegroundColor Green
Write-Host "  Public base URL: $publicBaseUrl"
Write-Host "  MCP client URL:  $mcpUrl"
Write-Host "  Owner token command:"
Write-Host "  $ownerTokenCopyCommand"
Write-Host ""
Write-Host "cloudflared PID: $($cloudflaredProcess.Id)"
Write-Host "cloudflared stdout log: $cloudflaredStdoutLog"
Write-Host "cloudflared stderr log: $cloudflaredStderrLog"
Write-Host ""
Write-Host "Keep the DevSpace window open while ChatGPT is connected."
