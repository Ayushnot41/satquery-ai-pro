param([switch]$Production, [string]$BuildRoot = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $BuildRoot -and (Test-Path -LiteralPath (Join-Path $projectRoot '.runtime/build-root.txt'))) {
    $BuildRoot = (Get-Content -LiteralPath (Join-Path $projectRoot '.runtime/build-root.txt') -Raw).Trim()
}
if (-not $BuildRoot) { $BuildRoot = $projectRoot }
$BuildRoot = [System.IO.Path]::GetFullPath($BuildRoot)
$pythonExe = Join-Path $BuildRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Create the project .venv and install backend/requirements-core.txt first.' }
$runtimeDir = Join-Path $projectRoot '.runtime'
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$services = @()
function Save-Services {
    ConvertTo-Json -InputObject @($services | Select-Object Id,ProcessName,StartTime) | Set-Content -LiteralPath (Join-Path $runtimeDir 'processes.json')
}
function Wait-Service([string]$Url, [System.Diagnostics.Process]$Process) {
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($Process.HasExited) { throw "Service exited. Inspect logs in $runtimeDir." }
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -SkipHttpErrorCheck
            if ($response.StatusCode -eq 200) { return }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    throw "Service did not become ready at $Url. Inspect logs in $runtimeDir."
}
foreach ($port in @(8010,3010)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Port $port is already in use. Stop the existing project services before starting another copy."
    }
}
try {
$services += Start-Process -FilePath $pythonExe -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8010','--no-proxy-headers') -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'api.log') -RedirectStandardError (Join-Path $runtimeDir 'api-error.log')
Save-Services
Wait-Service 'http://127.0.0.1:8010/api/health/ready' $services[-1]
$services += Start-Process -FilePath $pythonExe -ArgumentList @('-m','app.worker') -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'worker.log') -RedirectStandardError (Join-Path $runtimeDir 'worker-error.log')
$nextCommand = if ($Production) { 'start' } else { 'dev' }
$webArguments = if ($Production) { @('../scripts/serve-frontend.cjs') } else { @('node_modules/next/dist/bin/next',$nextCommand,'-p','3010','-H','127.0.0.1') }
$services += Start-Process -FilePath 'node' -ArgumentList $webArguments -WorkingDirectory (Join-Path $BuildRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'web.log') -RedirectStandardError (Join-Path $runtimeDir 'web-error.log')
Save-Services
Wait-Service 'http://127.0.0.1:3010' $services[-1]
Write-Output 'Satquery AI Pro is ready at http://127.0.0.1:3010. Service logs are in .runtime.'
} catch {
    Save-Services
    & (Join-Path $PSScriptRoot 'stop-pro.ps1')
    throw
}
