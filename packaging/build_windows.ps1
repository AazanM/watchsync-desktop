$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

if (-not (Test-Path ".venv-windows")) {
  $py = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
  if ($py -eq "py") { & py -3.9 -m venv .venv-windows } else { & python -m venv .venv-windows }
  if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
}

& .\.venv-windows\Scripts\python.exe -m pip install --upgrade pip wheel setuptools
if ($LASTEXITCODE -ne 0) { throw "pip bootstrap failed." }

& .\.venv-windows\Scripts\pip.exe install -r requirements.txt -r requirements_gui.txt pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

& .\.venv-windows\Scripts\pyinstaller.exe --noconfirm --clean (Join-Path $PSScriptRoot "watchsync-windows.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

$portable = Join-Path $root "dist\WatchSync Desktop\WatchSync Desktop.exe"
if (-not (Test-Path $portable)) { throw "Expected executable was not produced: $portable" }
Write-Host "Portable build ready: dist\WatchSync Desktop\"

$makensisPath = $null
$found = Get-Command makensis.exe -ErrorAction SilentlyContinue
if ($found) {
  $makensisPath = $found.Source
} else {
  $candidate = Join-Path ${env:ProgramFiles(x86)} "NSIS\makensis.exe"
  if (Test-Path $candidate) { $makensisPath = $candidate }
}

if ($makensisPath) {
  # Pass an absolute script path so ${__FILEDIR__} inside the .nsi resolves
  # against the real packaging directory rather than a relative duplicate.
  & $makensisPath (Join-Path $PSScriptRoot "WatchSyncDesktop.nsi")
  if ($LASTEXITCODE -ne 0) { throw "NSIS installer build failed." }
  Write-Host "Installer: dist\WatchSync-Desktop-1.7.6-Setup.exe"
} else {
  Write-Warning "NSIS was not found. Portable build is ready in dist\WatchSync Desktop\."
}
