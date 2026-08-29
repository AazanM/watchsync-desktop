"""Lifecycle controller for the bundled personal Syncplay server."""

import atexit
import os
import secrets
import socket
import subprocess
import sys
import threading
from collections import deque


class PrivateServerError(RuntimeError):
    pass


def generate_password():
    return secrets.token_urlsafe(12)


def generate_room_name():
    return "watchsync-{}".format(secrets.token_hex(3))


def local_address():
    try:
        addresses = socket.gethostbyname_ex(socket.gethostname())[2]
        for address in addresses:
            if address and not address.startswith("127."):
                return address
    except OSError:
        pass
    return "127.0.0.1"


class PrivateServerController(object):
    def __init__(self, command=None, max_log_lines=500):
        self._command = list(command) if command else self._default_command()
        self._process = None
        self._reader = None
        self._callbacks = []
        self._logs = deque(maxlen=max(10, int(max_log_lines)))
        self.port = None
        self.password = None
        self._lock = threading.RLock()
        atexit.register(self.stop)

    @staticmethod
    def _default_command():
        executable_dir = os.path.dirname(os.path.abspath(sys.executable))
        bundled_name = "syncplayServer.exe" if os.name == "nt" else "syncplayServer"
        bundled_server = os.path.join(executable_dir, bundled_name)
        if os.path.isfile(bundled_server):
            return [bundled_server]
        source_entrypoint = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, "syncplayServer.py")
        )
        return [sys.executable, source_entrypoint]

    @property
    def command(self):
        return tuple(self._command)

    @property
    def logs(self):
        with self._lock:
            return tuple(self._logs)

    @property
    def is_running(self):
        return self._process is not None and self._process.poll() is None

    @property
    def pid(self):
        return self._process.pid if self.is_running else None

    def subscribe(self, callback):
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

        def unsubscribe():
            with self._lock:
                if callback in self._callbacks:
                    self._callbacks.remove(callback)

        return unsubscribe

    def _emit(self, event, payload=None):
        with self._lock:
            callbacks = tuple(self._callbacks)
        for callback in callbacks:
            callback(event, payload)

    @staticmethod
    def _validate_port(port):
        try:
            value = int(port)
        except (TypeError, ValueError):
            raise PrivateServerError("Port must be a number.")
        if not 1 <= value <= 65535:
            raise PrivateServerError("Port must be between 1 and 65535.")
        return value

    @staticmethod
    def _ensure_port_available(port):
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as error:
            raise PrivateServerError("Port {} is already in use: {}".format(port, error))
        finally:
            probe.close()

    def start(self, port=8999, password=None):
        if self.is_running:
            raise PrivateServerError("The private server is already running.")
        port = self._validate_port(port)
        self._ensure_port_available(port)
        password = str(password or generate_password()).strip()
        if not password:
            raise PrivateServerError("A private server password is required.")
        args = self._command + [
            "--port", str(port),
            "--password", password,
            "--isolate-rooms",
            "--ipv4-only",
        ]
        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as error:
            raise PrivateServerError("Could not start the private server: {}".format(error))
        self._process = process
        self.port = port
        self.password = password
        self._logs.clear()
        self._reader = threading.Thread(target=self._read_output, args=(process,), daemon=True)
        self._reader.start()
        self._emit("started", {"port": port, "password": password, "pid": process.pid})
        return process.pid

    def _read_output(self, process):
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                clean_line = line.rstrip()
                if clean_line:
                    with self._lock:
                        self._logs.append(clean_line)
                    self._emit("log", clean_line)
        return_code = process.wait()
        if self._process is process:
            self._process = None
            self._emit("stopped", return_code)

    def stop(self):
        process = self._process
        if process is None:
            return
        self._process = None
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        if process.stdout:
            process.stdout.close()
        self._emit("stopped", process.returncode)
