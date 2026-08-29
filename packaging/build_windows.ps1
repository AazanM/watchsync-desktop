$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv-windows")) {
  py -3.9 -m venv .venv-windows
}
& .\.venv-windows\Scripts\python.exe -m pip install --upgrade pip wheel setuptools
& .\.venv-windows\Scripts\pip.exe install -r requirements.txt -r requirements_gui.txt pyinstaller
& .\.venv-windows\Scripts\pyinstaller.exe --noconfirm --clean packaging\watchsync-windows.spec

$makensis = Get-Command makensis.exe -ErrorAction SilentlyContinue
if ($makensis) {
  & $makensis.Source packaging\WatchSyncDesktop.nsi
  Write-Host "Installer: dist\WatchSync-Desktop-1.7.6-Setup.exe"
} else {
  Write-Warning "NSIS was not found. Portable build is ready in dist\WatchSync Desktop\."
}
