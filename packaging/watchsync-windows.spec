# Build with: pyinstaller --noconfirm packaging/watchsync-windows.spec

from PyInstaller.utils.hooks import collect_submodules
from syncplay.product import PRODUCT_NAME

resource_data = [("syncplay/resources", "syncplay/resources")]
hidden = collect_submodules("twisted.plugins")

client = Analysis(
    ["syncplayClient.py"],
    pathex=["."],
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
    icon="syncplay/resources/icon.ico",
)

server = Analysis(
    ["syncplayServer.py"],
    pathex=["."],
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
    icon="syncplay/resources/icon.ico",
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
