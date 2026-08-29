"""Always-on-top floating badge and overlay-only chat panel."""

import ctypes
import ctypes.util
import time

from syncplay import constants
from syncplay.product import CHAT_TITLE, ORGANIZATION_NAME, PRODUCT_SHORT_NAME
from syncplay.utils import isMacOS, isWindows
from syncplay.vendor.Qt import QtCore, QtGui, QtWidgets
from syncplay.vendor.Qt.QtCore import Qt, QPoint, QSettings


PANEL_STYLE = """
QFrame#panelSurface {
    background: rgba(12, 12, 17, 244);
    border: 1px solid rgba(255, 255, 255, 30);
    border-radius: 24px;
}
QLabel { color: #f7f7fa; font-family: -apple-system, "Segoe UI", sans-serif; }
QLabel#brandTitle { font-size: 19px; font-weight: 700; }
QLabel#roomLabel { color: rgba(255, 255, 255, 145); font-size: 12px; }
QLabel#statusLabel { color: #6de3a4; font-size: 11px; font-weight: 600; }
QScrollArea { border: 0; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QFrame#localBubble {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ff3d50, stop:1 #aa0c1e);
    border: 1px solid rgba(255, 120, 135, 90);
    border-radius: 15px;
}
QFrame#remoteBubble {
    background: rgba(255, 255, 255, 14);
    border: 1px solid rgba(255, 255, 255, 22);
    border-radius: 15px;
}
QLabel#messageMeta { color: rgba(255, 255, 255, 130); font-size: 10px; font-weight: 700; }
QLabel#messageText { color: #ffffff; font-size: 13px; }
QLineEdit {
    min-height: 38px;
    padding: 0 13px;
    color: #ffffff;
    background: rgba(255, 255, 255, 14);
    border: 1px solid rgba(255, 255, 255, 28);
    border-radius: 13px;
    selection-background-color: #ed1b2f;
}
QLineEdit:focus { border: 1px solid rgba(255, 92, 110, 155); }
QPushButton#sendButton {
    min-width: 42px; min-height: 38px;
    color: white; font-weight: 700;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ff3d50, stop:1 #aa0c1e);
    border: 1px solid rgba(255, 120, 135, 95);
    border-radius: 13px;
}
QPushButton#sendButton:disabled { background: #393940; color: #777780; border-color: #44444c; }
QPushButton#closeButton {
    min-width: 28px; min-height: 28px; max-width: 28px; max-height: 28px;
    color: rgba(255, 255, 255, 175); font-size: 16px;
    background: rgba(255, 255, 255, 12); border: 1px solid rgba(255, 255, 255, 20);
    border-radius: 14px;
}
QPushButton#closeButton:hover { background: #c31328; color: white; }
"""


def _global_position(event):
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()


def _apply_platform_window_behavior(widget):
    """Best-effort native topmost/full-screen behavior beyond Qt's flags."""
    platform_name = str(QtWidgets.QApplication.platformName() or "").lower()
    widget.winId()
    if isWindows() and platform_name == "windows":
        try:
            HWND_TOPMOST = -1
            flags = 0x0001 | 0x0002 | 0x0010  # NOSIZE | NOMOVE | NOACTIVATE
            ctypes.windll.user32.SetWindowPos(int(widget.winId()), HWND_TOPMOST, 0, 0, 0, 0, flags)
        except Exception:
            pass
    elif isMacOS() and platform_name == "cocoa":
        try:
            objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
            objc.sel_registerName.restype = ctypes.c_void_p
            objc.sel_registerName.argtypes = [ctypes.c_char_p]
            view_pointer = ctypes.c_void_p(int(widget.winId()))
            selector_window = objc.sel_registerName(b"window")
            get_window = ctypes.CFUNCTYPE(
                ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
            )(("objc_msgSend", objc))
            window_pointer = get_window(view_pointer, selector_window)
            if not window_pointer:
                return
            send_integer = ctypes.CFUNCTYPE(
                None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong
            )(("objc_msgSend", objc))
            send_integer(
                window_pointer,
                objc.sel_registerName(b"setCollectionBehavior:"),
                (1 << 0) | (1 << 8),  # CanJoinAllSpaces | FullScreenAuxiliary
            )
            send_integer(window_pointer, objc.sel_registerName(b"setLevel:"), 3)
        except Exception:
            pass


class ChatBadge(QtWidgets.QWidget):
    clicked = QtCore.Signal()
    moved = QtCore.Signal(QPoint)

    def __init__(self):
        super(ChatBadge, self).__init__(None)
        flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        if hasattr(Qt, "WA_MacAlwaysShowToolWindow"):
            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        self.setFixedSize(66, 66)
        self.setToolTip("Open {} chat".format(PRODUCT_SHORT_NAME))
        self._press_position = None
        self._start_position = None
        self._dragged = False
        self._unread = 0

    def set_unread(self, count):
        self._unread = max(0, int(count or 0))
        self.update()

    def paintEvent(self, _event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)
        gradient = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QtGui.QColor(35, 32, 43, 248))
        gradient.setColorAt(1, QtGui.QColor(5, 5, 8, 248))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 46), 1))
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect, 20, 20)
        accent = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
        accent.setColorAt(0, QtGui.QColor("#ff5c6e"))
        accent.setColorAt(1, QtGui.QColor("#aa0c1e"))
        painter.setPen(Qt.NoPen)
        painter.setBrush(accent)
        painter.drawRoundedRect(rect.adjusted(13, 14, -13, -14), 11, 11)
        painter.setPen(QtGui.QColor("white"))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(17)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, "WS")
        if self._unread:
            badge_rect = QtCore.QRect(self.width() - 25, 1, 23, 23)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 210), 1))
            painter.setBrush(QtGui.QColor("#ed1b2f"))
            painter.drawEllipse(badge_rect)
            font.setPixelSize(10)
            painter.setFont(font)
            painter.drawText(badge_rect, Qt.AlignCenter, "99+" if self._unread > 99 else str(self._unread))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_position = _global_position(event)
            self._start_position = self.pos()
            self._dragged = False
            event.accept()

    def mouseMoveEvent(self, event):
        if self._press_position is not None and event.buttons() & Qt.LeftButton:
            delta = _global_position(event) - self._press_position
            if delta.manhattanLength() > 4:
                self._dragged = True
            self.move(self._start_position + delta)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._press_position is not None:
            self._press_position = None
            self.moved.emit(self.pos())
            if not self._dragged:
                self.clicked.emit()
            event.accept()


class MessageBubble(QtWidgets.QWidget):
    def __init__(self, message, parent=None):
        super(MessageBubble, self).__init__(parent)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(2, 2, 2, 2)
        bubble = QtWidgets.QFrame()
        bubble.setObjectName("localBubble" if message.is_local else "remoteBubble")
        bubble.setMaximumWidth(285)
        layout = QtWidgets.QVBoxLayout(bubble)
        layout.setContentsMargins(12, 8, 12, 9)
        layout.setSpacing(3)
        meta = QtWidgets.QLabel(
            "{}  {}".format(message.username, time.strftime("%H:%M", time.localtime(message.received_at)))
        )
        meta.setObjectName("messageMeta")
        text = QtWidgets.QLabel(message.text)
        text.setObjectName("messageText")
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(meta)
        layout.addWidget(text)
        if message.is_local:
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)


class ChatPanel(QtWidgets.QWidget):
    closed = QtCore.Signal()

    def __init__(self, send_callback):
        super(ChatPanel, self).__init__(None)
        self._send_callback = send_callback
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        if hasattr(Qt, "WA_MacAlwaysShowToolWindow"):
            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        self.resize(410, 560)
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        self.surface = QtWidgets.QFrame()
        self.surface.setObjectName("panelSurface")
        self.surface.setStyleSheet(PANEL_STYLE)
        root.addWidget(self.surface)
        layout = QtWidgets.QVBoxLayout(self.surface)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(13)

        header = QtWidgets.QHBoxLayout()
        titles = QtWidgets.QVBoxLayout()
        self.title_label = QtWidgets.QLabel(CHAT_TITLE)
        self.title_label.setObjectName("brandTitle")
        self.room_label = QtWidgets.QLabel("Not connected")
        self.room_label.setObjectName("roomLabel")
        self.status_label = QtWidgets.QLabel("● CONNECTED")
        self.status_label.setObjectName("statusLabel")
        titles.addWidget(self.title_label)
        titles.addWidget(self.room_label)
        header.addLayout(titles, 1)
        header.addWidget(self.status_label)
        close_button = QtWidgets.QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.close)
        header.addWidget(close_button)
        layout.addLayout(header)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.messages_widget = QtWidgets.QWidget()
        self.messages_layout = QtWidgets.QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(6)
        self.messages_layout.addStretch(1)
        self.scroll.setWidget(self.messages_widget)
        layout.addWidget(self.scroll, 1)

        composer = QtWidgets.QHBoxLayout()
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Message the room…")
        self.input.setMaxLength(constants.MAX_CHAT_MESSAGE_LENGTH)
        self.input.returnPressed.connect(self.send_current_message)
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_current_message)
        composer.addWidget(self.input, 1)
        composer.addWidget(self.send_button)
        layout.addLayout(composer)

    def set_room(self, room):
        self.room_label.setText("Room: {}".format(room or "Not connected"))

    def set_connected(self, connected):
        self.status_label.setText("● CONNECTED" if connected else "● DISCONNECTED")
        self.status_label.setStyleSheet("color: #6de3a4;" if connected else "color: #ff7a87;")
        self.input.setEnabled(bool(connected))
        self.send_button.setEnabled(bool(connected))

    def set_chat_enabled(self, enabled, max_length=None):
        active = bool(enabled)
        self.input.setEnabled(active)
        self.send_button.setEnabled(active)
        if max_length:
            self.input.setMaxLength(int(max_length))
        self.input.setPlaceholderText("Message the room…" if active else "Chat is disabled by this server")

    def append_message(self, message):
        bubble = MessageBubble(message)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        QtCore.QTimer.singleShot(0, self._scroll_to_bottom)

    def clear_messages(self):
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_current_message(self):
        text = self.input.text().strip()
        if not text:
            return
        self._send_callback(text)
        self.input.clear()
        self.input.setFocus(Qt.OtherFocusReason)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        super(ChatPanel, self).keyPressEvent(event)

    def closeEvent(self, event):
        self.closed.emit()
        super(ChatPanel, self).closeEvent(event)


class OverlayController(object):
    def __init__(self, chat_store, send_callback):
        self.chat_store = chat_store
        self.badge = ChatBadge()
        self.panel = ChatPanel(send_callback)
        self.connected = False
        self.room = ""
        self.chat_enabled = True
        self.badge.clicked.connect(self.toggle_panel)
        self.badge.moved.connect(self._badge_moved)
        self.panel.closed.connect(self._panel_closed)
        self.chat_store.subscribe(self._store_changed)
        self._restore_badge_position()

    def _settings(self):
        return QSettings(ORGANIZATION_NAME, PRODUCT_SHORT_NAME)

    def _available_geometry_for_point(self, point):
        screen = QtWidgets.QApplication.screenAt(point)
        if screen is None:
            screen = QtWidgets.QApplication.primaryScreen()
        return screen.availableGeometry()

    def _constrain_badge(self, point):
        geometry = self._available_geometry_for_point(point)
        x = min(max(point.x(), geometry.left()), geometry.right() - self.badge.width() + 1)
        y = min(max(point.y(), geometry.top()), geometry.bottom() - self.badge.height() + 1)
        return QPoint(x, y)

    def _restore_badge_position(self):
        settings = self._settings()
        settings.beginGroup("ChatOverlay")
        saved = settings.value("badgePosition", None)
        settings.endGroup()
        if isinstance(saved, QPoint):
            position = saved
        else:
            geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
            position = QPoint(geometry.right() - 88, geometry.bottom() - 92)
        self.badge.move(self._constrain_badge(position))

    def _badge_moved(self, point):
        constrained = self._constrain_badge(point)
        self.badge.move(constrained)
        settings = self._settings()
        settings.beginGroup("ChatOverlay")
        settings.setValue("badgePosition", constrained)
        settings.endGroup()
        if self.panel.isVisible():
            self._position_panel()

    def _position_panel(self):
        badge_center = self.badge.geometry().center()
        geometry = self._available_geometry_for_point(badge_center)
        x = self.badge.x() + self.badge.width() - self.panel.width()
        y = self.badge.y() - self.panel.height() - 10
        if y < geometry.top():
            y = self.badge.y() + self.badge.height() + 10
        x = min(max(x, geometry.left()), geometry.right() - self.panel.width() + 1)
        y = min(max(y, geometry.top()), geometry.bottom() - self.panel.height() + 1)
        self.panel.move(x, y)

    def set_connected(self, connected, room=""):
        connected = bool(connected)
        if connected and not self.connected:
            self.chat_store.clear()
        self.connected = connected
        self.room = str(room or self.room or "")
        self.panel.set_room(self.room)
        self.panel.set_connected(connected and self.chat_enabled)
        if connected:
            self.badge.show()
            _apply_platform_window_behavior(self.badge)
        else:
            self.panel.hide()
            self.badge.hide()
            self.chat_store.set_reader_active(False)

    def set_room(self, room):
        self.room = str(room or "")
        self.panel.set_room(self.room)

    def set_chat_enabled(self, enabled, max_length=None):
        self.chat_enabled = bool(enabled)
        self.panel.set_chat_enabled(self.chat_enabled and self.connected, max_length)

    def toggle_panel(self):
        if self.panel.isVisible():
            self.panel.close()
            return
        if not self.connected:
            return
        self._position_panel()
        self.panel.show()
        _apply_platform_window_behavior(self.panel)
        self.panel.raise_()
        self.panel.activateWindow()
        self.panel.input.setFocus(Qt.OtherFocusReason)
        self.chat_store.set_reader_active(True)

    def _panel_closed(self):
        self.chat_store.set_reader_active(False)

    def _store_changed(self, event, payload):
        if event == "message":
            self.panel.append_message(payload)
        elif event == "clear":
            self.panel.clear_messages()
        elif event == "unread":
            self.badge.set_unread(payload)

    def shutdown(self):
        self.panel.hide()
        self.badge.hide()
