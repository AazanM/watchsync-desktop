@echo off
setlocal EnableDelayedExpansion
title WatchSync Desktop
cd /d "%~dp0.."

set "VENV=%CD%\.venv"
set "PYEXE=%VENV%\Scripts\pythonw.exe"

if exist "%PYEXE%" goto :launch

echo ============================================
echo   WatchSync Desktop - first-time setup
echo   This runs once and takes a few minutes.
echo ============================================
echo.

set "PY="
for %%V in (3.11 3.10 3.9) do (
  if not defined PY ( py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V" )
)
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )

if not defined PY (
  echo Python was not found. Installing it now via winget...
  echo.
  winget install --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements
  if errorlevel 1 (
    echo.
    echo Automatic install failed. Please install Python 3.11 manually from:
    echo   https://www.python.org/downloads/
    echo Tick "Add python.exe to PATH" during setup, then run this file again.
    echo.
    pause
    exit /b 1
  )
  echo.
  echo Python installed. Please CLOSE this window and double-click this file
  echo again so Windows picks up the new installation.
  echo.
  pause
  exit /b 0
)

echo Using: %PY%
echo Creating environment...
%PY% -m venv "%VENV%"
if errorlevel 1 goto :failed

echo Installing dependencies (this is the slow part)...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%VENV%\Scripts\python.exe" -m pip install -r requirements.txt -r requirements_gui.txt
if errorlevel 1 goto :failed

echo Creating desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\WatchSync Desktop.lnk');" ^
  "$s.TargetPath='%~f0'; $s.WorkingDirectory='%CD%';" ^
  "$i='%CD%\syncplay\resources\icon.ico'; if(Test-Path $i){$s.IconLocation=$i};" ^
  "$s.Save()" >nul 2>&1

echo.
echo Setup complete. Starting WatchSync Desktop...
echo From now on, use the "WatchSync Desktop" shortcut on your desktop.
echo.

:launch
start "" "%PYEXE%" "%CD%\syncplayClient.py"
exit /b 0

:failed
echo.
echo ============================================
echo   Setup failed. Please send the text above
echo   to whoever gave you this app.
echo ============================================
echo.
pause
exit /b 1
