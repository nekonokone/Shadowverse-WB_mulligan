$ErrorActionPreference = 'Stop'
$outputDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $outputDir
$siteDir = Join-Path $projectDir 'work\installer-build\site-packages'
$pythonCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'),
    'C:\Users\PC_User\AppData\Local\Programs\Python\Python314\python.exe'
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) { throw 'Python 3.14 was not found. Update the Python path in this script.' }
New-Item -ItemType Directory -Force -Path $siteDir | Out-Null
& $python -m pip install --target $siteDir -r (Join-Path $outputDir 'requirements-runtime.txt')
if ($LASTEXITCODE -ne 0) { throw 'The required libraries could not be installed. Check your internet connection and try again.' }
Write-Host 'Done. Double-click 起動する.bat to run the tracker.'
