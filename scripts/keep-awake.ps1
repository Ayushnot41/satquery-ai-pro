# Project-scoped sleep prevention. Does not change Windows power settings or keep
# the display on. Removing .runtime/keep-awake.active releases the request.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeRoot = Join-Path $projectRoot '.runtime'
$marker = Join-Path $runtimeRoot 'keep-awake.active'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class SatqueryBuildPower {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
# ES_CONTINUOUS | ES_SYSTEM_REQUIRED; deliberately omit ES_DISPLAY_REQUIRED.
$requested = [SatqueryBuildPower]::SetThreadExecutionState([uint32]2147483649)
if ($requested -eq 0) { throw 'Windows did not accept the temporary keep-awake request.' }
$current = Get-Process -Id $PID
@{ Id=$current.Id; ProcessName=$current.ProcessName; StartTime=$current.StartTime.ToString('o'); Active=$true } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeRoot 'keep-awake.json')
try {
    while (Test-Path -LiteralPath $marker) { Start-Sleep -Seconds 30 }
} finally {
    [void][SatqueryBuildPower]::SetThreadExecutionState([uint32]2147483648)
    @{ Id=$current.Id; Active=$false } | ConvertTo-Json |
        Set-Content -LiteralPath (Join-Path $runtimeRoot 'keep-awake.json')
}
