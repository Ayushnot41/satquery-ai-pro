param([switch]$KeepTunnel)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$processFiles = @((Join-Path $projectRoot '.runtime/tunnel-process.json'), (Join-Path $projectRoot '.runtime/processes.json'))
if ($KeepTunnel) { $processFiles = @((Join-Path $projectRoot '.runtime/processes.json')) }
foreach ($processFile in $processFiles) {
if (-not (Test-Path -LiteralPath $processFile)) { continue }
$remaining = @()
foreach ($saved in @(Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json)) {
    $running = Get-Process -Id $saved.Id -ErrorAction SilentlyContinue
    if (-not $running) { continue }
    if ($running.ProcessName -ne $saved.ProcessName -or $running.StartTime.ToUniversalTime().Ticks -ne ([datetime]$saved.StartTime).ToUniversalTime().Ticks) {
        Write-Warning "Process $($saved.Id) was reused; leaving it alone."
        continue
    }
    try {
        # PowerShell 7 / .NET terminates this verified instance and its children.
        $running.Kill($true)
        if (-not $running.WaitForExit(10000)) { throw 'The process did not stop in time.' }
    } catch {
        if (-not $running.HasExited) { $remaining += $saved; Write-Warning $_.Exception.Message }
    }
}
ConvertTo-Json -InputObject @($remaining) | Set-Content -LiteralPath $processFile
if ($remaining.Count) { throw 'Some project services remain running; inspect .runtime/processes.json.' }
}
Write-Output 'Saved project service instances and their children stopped.'
