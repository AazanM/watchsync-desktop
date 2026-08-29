# WatchSync Desktop

WatchSync Desktop is a personal-use fork of Syncplay 1.7.6 with an overlay-only chat interface. Playback synchronization and the Syncplay client/server wire protocol remain compatible with ordinary Syncplay 1.7.6 clients and servers.

## What changed

- Chat lives in a draggable always-on-top `WS` badge and dark floating panel instead of the main window.
- The overlay tracks unread messages, remembers its display position, and supports Enter to send and Escape to close.
- The File menu includes **Host private WatchSync server…**, which starts the bundled room-isolated server, generates connection details, and can reconnect the current client through localhost.
- Main-window playback, room, user, playlist, readiness, TLS, privacy, reconnect, and mismatch-warning behavior is inherited from Syncplay.

## Run from source on macOS

```sh
cd watchsync-desktop
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements_gui.txt
.venv/bin/python syncplayClient.py
```

Select VLC 3 or IINA in the Syncplay configuration window. The floating chat badge appears after the server handshake succeeds.

## Private rooms

Choose **File → Host private WatchSync server…**, then:

1. Keep or change port `8999`, the generated password, and room name.
2. Start the server and allow it through the operating-system firewall if prompted.
3. Copy the connection details for the other participant.
4. Select **Connect this app** to move the host client to `127.0.0.1`.

LAN guests use the shown local address. Internet guests need a publicly reachable address and may need TCP port forwarding. The bundled personal server does not add NAT traversal or configure TLS certificates.

## Build and test

Run the automated suite:

```sh
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
```

Build an unsigned/ad-hoc-signed macOS app with a universal2 Python toolchain:

```sh
sh packaging/build_macos.sh
```

The app is written to `dist/WatchSync Desktop.app`. To install the personal
build, drag it to Applications, then Control-click it and choose **Open** the
first time. If macOS still blocks it, use **System Settings → Privacy &
Security → Open Anyway**. Only bypass the warning for a build you produced or
received through a trusted channel.

On Windows 10/11 x64, run PowerShell from the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\packaging\build_windows.ps1
```

Installing NSIS adds `dist\WatchSync-Desktop-1.7.6-Setup.exe`; without NSIS the script still produces the portable directory.

Because the Windows installer is unsigned, Windows SmartScreen may display a
warning. On a trusted self-built copy, choose **More info → Run anyway**.

See [VERIFICATION.md](VERIFICATION.md) for the automated coverage and the
remaining physical-machine certification checklist.

## Privacy and limitations

WatchSync does not upload or transfer video. Each viewer needs their own media file. Filename, byte size, duration, timestamps, room details, and chat follow the selected Syncplay server's normal privacy and TLS behavior. Chat history is memory-only and is cleared on a new connection.

The app does not add voice/video calling, accounts, end-to-end encryption, or media streaming. Filename/size/duration differences warn users but do not block playback.

## License

WatchSync Desktop preserves Syncplay's Apache License 2.0 and the bundled third-party notices. Syncplay copyright and attribution remain with the original Syncplay contributors.
