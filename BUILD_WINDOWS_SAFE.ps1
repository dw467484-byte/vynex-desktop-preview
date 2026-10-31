$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$source = Join-Path $root 'VYNEX.py'
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { throw 'Python introuvable. Installe Python 3.10+ et rends python accessible dans PowerShell.' }
$python = $pythonCommand.Source
if (-not (Test-Path -LiteralPath $source)) { throw "Source introuvable : $source" }

# Chaque compilation reçoit des répertoires différents pour éviter les DLL bloquées
# si une ancienne version de VYNEX est encore ouverte.
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$dist = Join-Path $root "dist_release_$stamp"
$work = Join-Path $root "build_release_$stamp"
$spec = Join-Path $root "spec_release_$stamp"
$assetDir = Join-Path $root 'assets'
$ico = Join-Path $assetDir 'VYNEX.ico'
$png = Join-Path $assetDir 'VYNEX_icon.png'

Write-Host '=== VYNEX : vérification de syntaxe ===' -ForegroundColor Cyan
& $python -m py_compile $source
if ($LASTEXITCODE -ne 0) { throw 'Syntaxe Python invalide : compilation annulée.' }

Write-Host '=== Installation/vérification des outils de compilation ===' -ForegroundColor Cyan
& $python -m pip install -r (Join-Path $root 'requirements-build.txt')
if ($LASTEXITCODE -ne 0) { throw 'Installation des dépendances de compilation échouée.' }

$argsPy = @('-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--name','VYNEX','--distpath',$dist,'--workpath',$work,'--specpath',$spec)
if (Test-Path -LiteralPath $ico) { $argsPy += @('--icon', $ico) }
if (Test-Path -LiteralPath $png) { $argsPy += @('--add-data', ("$assetDir;assets")) }
$argsPy += $source
Write-Host '=== Création du logiciel Windows ===' -ForegroundColor Cyan
& $python @argsPy
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller a échoué. Envoie les dernières lignes de la sortie.' }

$bundle = Join-Path $dist 'VYNEX'
$exe = Join-Path $bundle 'VYNEX.exe'
if (-not (Test-Path -LiteralPath $exe)) { throw "EXE introuvable après compilation : $exe" }
$archive = Join-Path $root "VYNEX-windows-x64-$stamp.zip"
Compress-Archive -Path $bundle -DestinationPath $archive -Force
Write-Host ''
Write-Host "SUCCÈS : $exe" -ForegroundColor Green
Write-Host "Archive : $archive" -ForegroundColor Green
Write-Host 'Les moteurs IA (Ollama/llama.cpp) et les modèles sont distincts et ne sont pas inclus dans cet EXE.' -ForegroundColor Yellow
