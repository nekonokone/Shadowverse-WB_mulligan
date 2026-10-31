$ErrorActionPreference = 'Stop'
$outputDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $outputDir
$projectDir = Split-Path -Parent $outputDir
$workDir = Join-Path $projectDir 'work\installer-build'
$siteDir = Join-Path $workDir 'site-packages'
$pythonCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'),
    'C:\Users\PC_User\AppData\Local\Programs\Python\Python314\python.exe'
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $python) {
    throw 'Python 3.14 was not found. Update the Python path near the top of Build-Installer.ps1.'
}
New-Item -ItemType Directory -Force -Path $workDir | Out-Null
New-Item -ItemType Directory -Force -Path $siteDir | Out-Null
$env:PYTHONPATH = "$siteDir;$env:PYTHONPATH"
& $python -c "import mss, PIL, numpy, cv2"
if ($LASTEXITCODE -ne 0) { throw 'Run Install-Dependencies.ps1 before building the app.' }
& $python -c "import PyInstaller"
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install --target $siteDir 'pyinstaller>=6.0'
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller could not be downloaded. Check your internet connection and try again.' }
}

$distDir = Join-Path $outputDir 'dist'
$buildDir = Join-Path $workDir 'pyinstaller'
$iconFile = Join-Path $outputDir 'mulligan_tracker.ico'
if (-not (Test-Path -LiteralPath $iconFile)) { throw 'mulligan_tracker.ico was not found.' }
& $python -m PyInstaller --noconfirm --clean --onedir --windowed --icon $iconFile --add-data "$iconFile;." --name MulliganTracker --distpath $distDir --workpath $buildDir --specpath $workDir --collect-all cv2 --collect-all numpy (Join-Path $outputDir 'mulligan_tracker.py')
if ($LASTEXITCODE -ne 0) { throw 'The application build failed.' }

$compilerCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 7\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe')
)
$compiler = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $compiler) {
    Write-Host 'The app files are ready in outputs\dist\MulliganTracker. Install Inno Setup 6 or 7, then rerun this script to create the installer.'
    exit 0
}
& $compiler (Join-Path $outputDir 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw 'The installer compilation failed.' }
Write-Host "Installer created in $outputDir\installer-output"
