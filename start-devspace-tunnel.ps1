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
        [Parameter(Mandatory = $true)][string]$LogPath,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath $LogPath) {
            $text = Get-Content -LiteralPath $LogPath -Raw -ErrorAction SilentlyContinue
            $match = [regex]::Match($text, 'https://[a-z0-9-]+\.trycloudflare\.com')
            if ($match.Success) {
                return $match.Value
            }
        }
        Start-Sleep -Seconds 1
    }

    throw "Timed out waiting for cloudflared to print a trycloudflare.com URL. See $LogPath"
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

Remove-Item -LiteralPath $cloudflaredLog -ErrorAction SilentlyContinue

Write-Host "Starting Cloudflare quick tunnel..." -ForegroundColor Cyan
$cloudflaredProcess = Start-Process -FilePath $cloudflared `
    -ArgumentList @("tunnel", "--url", $originUrl) `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $cloudflaredLog `
    -RedirectStandardError $cloudflaredLog `
    -WindowStyle Hidden `
    -PassThru
Set-Content -LiteralPath $cloudflaredPidFile -Value $cloudflaredProcess.Id

$publicBaseUrl = Wait-ForTunnelUrl -LogPath $cloudflaredLog -TimeoutSeconds 60
$mcpUrl = "$publicBaseUrl/mcp"

Write-Host "Tunnel ready:" -ForegroundColor Green
Write-Host "  Public base URL: $publicBaseUrl"
Write-Host "  MCP client URL:  $mcpUrl"

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
Write-Host "Use these values:" -ForegroundColor Green
Write-Host "DevSpace init public base URL:"
Write-Host $publicBaseUrl
Write-Host ""
Write-Host "MCP client address:"
Write-Host $mcpUrl
Write-Host ""
Write-Host "Owner password copy command:" -ForegroundColor Cyan
Write-Host '(Get-Content "$env:USERPROFILE\.devspace\auth.json" -Raw | ConvertFrom-Json).ownerToken | Set-Clipboard'
Write-Host ""
Write-Host "cloudflared PID: $($cloudflaredProcess.Id)"
Write-Host "cloudflared log: $cloudflaredLog"
Write-Host ""
Write-Host "Keep the DevSpace window open while ChatGPT is connected."
