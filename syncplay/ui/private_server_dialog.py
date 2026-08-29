"""Qt controls for one-click hosting of the bundled private server."""

from syncplay.private_server import (
    PrivateServerError,
    generate_password,
    generate_room_name,
    local_address,
)
from syncplay.product import PRIVATE_SERVER_TITLE, PRODUCT_NAME
from syncplay.vendor.Qt import QtCore, QtWidgets


class PrivateServerDialog(QtWidgets.QDialog):
    def __init__(self, controller, connect_callback, parent=None):
        super(PrivateServerDialog, self).__init__(parent)
        self.controller = controller
        self.connect_callback = connect_callback
        self._last_log_count = 0
        self.setWindowTitle(PRIVATE_SERVER_TITLE)
        self.resize(560, 590)
        root = QtWidgets.QVBoxLayout(self)

        intro = QtWidgets.QLabel(
            "Run the bundled Syncplay-compatible server on this computer. "
            "Friends on your LAN can connect directly; internet guests may require router port forwarding."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        form = QtWidgets.QFormLayout()
        self.port_input = QtWidgets.QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(8999)
        self.host_input = QtWidgets.QLineEdit(local_address())
        self.host_input.setPlaceholderText("Address guests should use")

        password_row = QtWidgets.QHBoxLayout()
        self.password_input = QtWidgets.QLineEdit(generate_password())
        self.password_input.setEchoMode(QtWidgets.QLineEdit.PasswordEchoOnEdit)
        password_button = QtWidgets.QPushButton("Regenerate")
        password_button.clicked.connect(lambda: self.password_input.setText(generate_password()))
        password_row.addWidget(self.password_input, 1)
        password_row.addWidget(password_button)

        room_row = QtWidgets.QHBoxLayout()
        self.room_input = QtWidgets.QLineEdit(generate_room_name())
        room_button = QtWidgets.QPushButton("Regenerate")
        room_button.clicked.connect(lambda: self.room_input.setText(generate_room_name()))
        room_row.addWidget(self.room_input, 1)
        room_row.addWidget(room_button)

        form.addRow("Port", self.port_input)
        form.addRow("Guest address", self.host_input)
        form.addRow("Server password", password_row)
        form.addRow("Room", room_row)
        root.addLayout(form)

        action_row = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("Start server")
        self.start_button.clicked.connect(self.start_server)
        self.stop_button = QtWidgets.QPushButton("Stop server")
        self.stop_button.clicked.connect(self.stop_server)
        self.connect_button = QtWidgets.QPushButton("Connect this app")
        self.connect_button.clicked.connect(self.connect_client)
        action_row.addWidget(self.start_button)
        action_row.addWidget(self.stop_button)
        action_row.addWidget(self.connect_button)
        root.addLayout(action_row)

        self.status_label = QtWidgets.QLabel("Server is stopped")
        root.addWidget(self.status_label)

        details_row = QtWidgets.QHBoxLayout()
        self.details = QtWidgets.QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(110)
        copy_button = QtWidgets.QPushButton("Copy connection details")
        copy_button.clicked.connect(self.copy_details)
        details_row.addWidget(self.details, 1)
        details_row.addWidget(copy_button)
        root.addLayout(details_row)

        root.addWidget(QtWidgets.QLabel("Server log"))
        self.log_output = QtWidgets.QPlainTextEdit()
        self.log_output.setReadOnly(True)
        root.addWidget(self.log_output, 1)

        note = QtWidgets.QLabel(
            "The password protects server access. Room isolation prevents clients from listing other rooms. "
            "This local server does not configure TLS or router/firewall rules."
        )
        note.setWordWrap(True)
        root.addWidget(note)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def connection_text(self):
        return (
            "{} private room\n"
            "Server: {}:{}\n"
            "Password: {}\n"
            "Room: {}"
        ).format(
            PRODUCT_NAME,
            self.host_input.text().strip() or local_address(),
            self.port_input.value(),
            self.password_input.text(),
            self.room_input.text().strip(),
        )

    def start_server(self):
        try:
            self.controller.start(self.port_input.value(), self.password_input.text())
        except PrivateServerError as error:
            QtWidgets.QMessageBox.warning(self, "Private server", str(error))
            return
        self.status_label.setText("Server is starting on port {}…".format(self.port_input.value()))
        self.details.setPlainText(self.connection_text())
        self.refresh()

    def stop_server(self):
        self.controller.stop()
        self.refresh()

    def connect_client(self):
        if not self.controller.is_running:
            QtWidgets.QMessageBox.information(self, "Private server", "Start the server before connecting.")
            return
        room = self.room_input.text().strip()
        if not room:
            QtWidgets.QMessageBox.warning(self, "Private server", "Enter a room name.")
            return
        self.connect_callback(
            "127.0.0.1",
            self.port_input.value(),
            self.password_input.text(),
            room,
        )
        self.status_label.setText("Switching this app to the private server…")

    def copy_details(self):
        text = self.connection_text()
        self.details.setPlainText(text)
        QtWidgets.QApplication.clipboard().setText(text)
        self.status_label.setText("Connection details copied")

    def refresh(self):
        running = self.controller.is_running
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.connect_button.setEnabled(running)
        self.port_input.setEnabled(not running)
        self.password_input.setEnabled(not running)
        logs = self.controller.logs
        if len(logs) != self._last_log_count:
            self.log_output.setPlainText("\n".join(logs))
            self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())
            self._last_log_count = len(logs)
        if running and not self.status_label.text().startswith("Switching"):
            self.status_label.setText("Server is running (PID {})".format(self.controller.pid))
            self.details.setPlainText(self.connection_text())
        elif not running and self.controller._process is None:
            self.status_label.setText("Server is stopped")
