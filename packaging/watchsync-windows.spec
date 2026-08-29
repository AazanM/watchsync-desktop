# Build with: pyinstaller --noconfirm packaging/watchsync-windows.spec

import os
import sys

# PyInstaller resolves relative paths in a spec against the spec's own
# directory and execs it without the project root on sys.path, so anchor
# everything to the repository root explicitly.
PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))
sys.path.insert(0, PROJECT_ROOT)

from PyInstaller.utils.hooks import collect_submodules
from syncplay.product import PRODUCT_NAME

resource_data = [
    (os.path.join(PROJECT_ROOT, "syncplay", "resources"), "syncplay/resources")
]
# syncplay reaches Qt through its vendored shim, which imports the binding
# dynamically. PyInstaller's static analysis therefore never sees PySide2, so
# the Qt extension modules are left out and the vendored shim dies on startup.
# Naming them here also lets PyInstaller's PySide2 hooks collect the Qt
# plugins and support files.
hidden = collect_submodules("twisted.plugins") + [
    "PySide2.QtCore",
    "PySide2.QtGui",
    "PySide2.QtWidgets",
]

client = Analysis(
    [os.path.join(PROJECT_ROOT, "syncplayClient.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=resource_data,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
client_pyz = PYZ(client.pure)
client_exe = EXE(
    client_pyz,
    client.scripts,
    [],
    exclude_binaries=True,
    name=PRODUCT_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join(PROJECT_ROOT, "syncplay", "resources", "icon.ico"),
)

server = Analysis(
    [os.path.join(PROJECT_ROOT, "syncplayServer.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=resource_data,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
server_pyz = PYZ(server.pure)
server_exe = EXE(
    server_pyz,
    server.scripts,
    [],
    exclude_binaries=True,
    name="syncplayServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=os.path.join(PROJECT_ROOT, "syncplay", "resources", "icon.ico"),
)

# Console-mode smoke test, built from the same analysis settings so it proves
# the shipped bundle can import Qt and the syncplay UI. CI runs it; the NSIS
# installer leaves it out of the user-facing install.
smoke = Analysis(
    [os.path.join(SPECPATH, "smoketest.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=resource_data,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
smoke_pyz = PYZ(smoke.pure)
smoke_exe = EXE(
    smoke_pyz,
    smoke.scripts,
    [],
    exclude_binaries=True,
    name="watchsync-smoketest",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

bundle = COLLECT(
    client_exe,
    server_exe,
    smoke_exe,
    client.binaries,
    client.datas,
    server.binaries,
    server.datas,
    smoke.binaries,
    smoke.datas,
    strip=False,
    upx=True,
    name=PRODUCT_NAME,
)
