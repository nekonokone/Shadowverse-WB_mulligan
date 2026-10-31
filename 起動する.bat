@echo off
cd /d "%~dp0"
if exist "%~dp0dist\MulliganTracker\MulliganTracker.exe" (
  start "" "%~dp0dist\MulliganTracker\MulliganTracker.exe"
  exit /b
)
set "PYTHONPATH=%~dp0..\work\installer-build\site-packages;%PYTHONPATH%"
"%LOCALAPPDATA%\Programs\Python\Python314\python.exe" -c "import mss, PIL, numpy, cv2" 2>nul
if errorlevel 1 (
  echo 開発用ライブラリがまだ入っていないよ。配布版はインストーラを使ってね。
  echo 先に Install-Dependencies.ps1 を実行してね。
  pause
  exit /b 1
)
"%LOCALAPPDATA%\Programs\Python\Python314\python.exe" "%~dp0mulligan_tracker.py"
if errorlevel 1 pause
