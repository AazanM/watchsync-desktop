"""Session-only chat model used by the floating desktop overlay."""

import threading
import time


class ChatMessage(object):
    __slots__ = ("username", "text", "received_at", "is_local")

    def __init__(self, username, text, received_at=None, is_local=False):
        self.username = str(username or "Anonymous")
        self.text = str(text or "")
        self.received_at = float(received_at if received_at is not None else time.time())
        self.is_local = bool(is_local)

    def __eq__(self, other):
        return isinstance(other, ChatMessage) and (
            self.username,
            self.text,
            self.received_at,
            self.is_local,
        ) == (
            other.username,
            other.text,
            other.received_at,
            other.is_local,
        )


class ChatStore(object):
    """Small observable store whose contents never leave the current session."""

    def __init__(self, max_messages=500):
        self.max_messages = max(1, int(max_messages))
        self._messages = []
        self._subscribers = []
        self._unread_count = 0
        self._reader_active = False
        self._lock = threading.RLock()

    @property
    def unread_count(self):
        with self._lock:
            return self._unread_count

    def snapshot(self):
        with self._lock:
            return tuple(self._messages)

    def subscribe(self, callback):
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

        def unsubscribe():
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return unsubscribe

    def _notify(self, event, payload=None):
        with self._lock:
            subscribers = tuple(self._subscribers)
        for callback in subscribers:
            callback(event, payload)

    def append(self, username, text, is_local=False, received_at=None):
        message = ChatMessage(username, text, received_at, is_local)
        if not message.text:
            return None
        with self._lock:
            self._messages.append(message)
            if len(self._messages) > self.max_messages:
                del self._messages[:-self.max_messages]
            if not message.is_local and not self._reader_active:
                self._unread_count += 1
        self._notify("message", message)
        self._notify("unread", self.unread_count)
        return message

    def clear(self):
        with self._lock:
            self._messages = []
            self._unread_count = 0
        self._notify("clear")
        self._notify("unread", 0)

    def set_reader_active(self, active):
        with self._lock:
            self._reader_active = bool(active)
            if self._reader_active:
                self._unread_count = 0
        self._notify("unread", self.unread_count)

