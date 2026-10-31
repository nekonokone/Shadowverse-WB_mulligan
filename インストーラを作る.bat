@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\PC_User\Documents\Codex\2026-10-31\referenced-chatgpt-conversation-this-is-an\outputs\Build-Installer.ps1"
set "BUILD_EXIT=%ERRORLEVEL%"
echo.
if "%BUILD_EXIT%"=="0" (
  echo Build process finished. Check the output above.
) else (
  echo Build failed. Please copy the error text above.
)
pause
