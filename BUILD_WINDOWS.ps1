# Alias sûr : toutes les compilations utilisent des dossiers horodatés.
$ErrorActionPreference = 'Stop'
try {
    & (Join-Path $PSScriptRoot 'BUILD_WINDOWS_SAFE.ps1')
    if (-not $?) { throw 'Le script de compilation a signalé une erreur.' }
} catch {
    Write-Error $_
    exit 1
}
