# Temporary, sample-only HTTPS preview. Requires the official cloudflared CLI.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot '.runtime'
$previewDir = Join-Path $runtimeDir 'public-preview'
$cloudflared = (Get-Command cloudflared -ErrorAction Stop).Source
New-Item -ItemType Directory -Path $previewDir -Force | Out-Null
& (Join-Path $PSScriptRoot 'stop-pro.ps1')
$tunnel = $null
$previous = @{}
try {
    $tunnel = Start-Process -FilePath $cloudflared -ArgumentList @('tunnel','--url','http://127.0.0.1:3010','--no-autoupdate') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'tunnel.log') -RedirectStandardError (Join-Path $runtimeDir 'tunnel-error.log')
    ConvertTo-Json -InputObject @($tunnel | Select-Object Id,ProcessName,StartTime) | Set-Content -LiteralPath (Join-Path $runtimeDir 'tunnel-process.json')
    $previewUrl = $null
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($tunnel.HasExited) { throw 'Tunnel exited. Inspect .runtime/tunnel-error.log.' }
        $output = Get-Content -LiteralPath (Join-Path $runtimeDir 'tunnel-error.log') -Raw -ErrorAction SilentlyContinue
        if ($output -match 'https://[a-z0-9-]+\.trycloudflare\.com') { $previewUrl = $Matches[0]; break }
        Start-Sleep -Milliseconds 500
    }
    if (-not $previewUrl) { throw 'No preview URL received. Inspect .runtime/tunnel-error.log.' }
    $secretPath = Join-Path $previewDir 'auth-secret.txt'
    if (-not (Test-Path -LiteralPath $secretPath)) {
        [Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(48)) | Set-Content -LiteralPath $secretPath
    }
    $configuration = @{
        ENVIRONMENT='preview'; COOKIE_SECURE='true'; CORS_ORIGINS=$previewUrl
        AUTH_PEPPER=(Get-Content -LiteralPath $secretPath -Raw).Trim()
        ALLOW_DEMO_GUEST='true'; DEVELOPMENT_VERIFICATION_CODES='false'; DEMO_MODE='true'; VLM_BACKEND='demo'
        DATABASE_URL=('sqlite:///' + (Join-Path $previewDir 'preview.db').Replace('\','/'))
        UPLOAD_DIR=(Join-Path $previewDir 'uploads')
    }
    foreach ($key in $configuration.Keys) {
        $previous[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        [Environment]::SetEnvironmentVariable($key, $configuration[$key], 'Process')
    }
    & (Join-Path $PSScriptRoot 'start-pro.ps1') -Production
    $previewUrl | Set-Content -LiteralPath (Join-Path $runtimeDir 'preview-url.txt')
    Write-Output "Temporary sample-only preview: $previewUrl"
    Write-Output 'The link requires this computer, app services, and tunnel to remain running. It is not permanent hosting.'
} catch {
    if ($tunnel -and -not $tunnel.HasExited) { $tunnel.Kill($true) }
    throw
} finally {
    foreach ($key in $previous.Keys) { [Environment]::SetEnvironmentVariable($key, $previous[$key], 'Process') }
}
