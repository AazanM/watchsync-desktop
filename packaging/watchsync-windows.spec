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
hidden = collect_submodules("twisted.plugins")

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

bundle = COLLECT(
    client_exe,
    server_exe,
    client.binaries,
    client.datas,
    server.binaries,
    server.datas,
    strip=False,
    upx=True,
    name=PRODUCT_NAME,
)
