# WatchSync Desktop verification

## Automated and locally completed

- ChatStore message, unread, reader, bounding, and session-clear behavior.
- Overlay connection visibility, unread clearing, and overlay-only send flow.
- Private-server invalid-port, occupied-port, start, monitor, and stop behavior.
- Two live clients exchanging chat through the original Syncplay wire protocol.
- File name, byte size, and duration metadata relayed without transferring media.
- Source compile checks and an offscreen Qt main-window smoke test.
- Native macOS badge/panel creation, focus, and shutdown lifecycle.
- Bundled private-server startup and protocol interoperability.
- Universal2 (`arm64` and `x86_64`) client and server launchers.
- Strict deep verification of the ad-hoc macOS signature.

## Physical-machine release checklist

These items require the indicated apps, displays, or operating systems and are
not substitutes for the automated suite:

- macOS: two clients with VLC 3; play, pause, seek, late join, reconnect,
  readiness, chat, and all three media mismatch warnings.
- macOS: repeat with IINA, including native full-screen, another Space, and a
  second physical monitor.
- Windows 10 and 11 x64: two clients with VLC 3, always-on-top/focus behavior,
  firewall prompt, private server, and installer/uninstaller.
- One unmodified Syncplay 1.7.6 GUI client against both a public server and the
  bundled local server.
- Clean Intel Mac, Apple silicon Mac, Windows 10, and Windows 11 installs,
  including the documented unsigned-build trust flow.

The GitHub Actions workflow builds both platform artifacts, but physical player,
display, firewall, and clean-machine checks should be signed off before treating
the builds as certified releases.
