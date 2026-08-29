import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from syncplay.chat import ChatStore
from syncplay.ui.chat_overlay import OverlayController
from syncplay.vendor.Qt import QtWidgets


class ChatOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.sent = []
        self.store = ChatStore()
        self.controller = OverlayController(self.store, self.sent.append)

    def tearDown(self):
        self.controller.shutdown()
        self.app.processEvents()

    def test_badge_and_panel_follow_connection_state(self):
        self.assertFalse(self.controller.badge.isVisible())
        self.controller.set_connected(True, "movie-room")
        self.controller.toggle_panel()
        self.app.processEvents()
        self.assertTrue(self.controller.badge.isVisible())
        self.assertTrue(self.controller.panel.isVisible())
        self.assertIn("movie-room", self.controller.panel.room_label.text())
        self.controller.set_connected(False)
        self.assertFalse(self.controller.badge.isVisible())
        self.assertFalse(self.controller.panel.isVisible())

    def test_send_keeps_chat_in_overlay_flow(self):
        self.controller.set_connected(True, "movie-room")
        self.controller.toggle_panel()
        self.controller.panel.input.setText("hello")
        self.controller.panel.send_current_message()
        self.assertEqual(self.sent, ["hello"])
        self.assertEqual(self.controller.panel.input.text(), "")

    def test_open_panel_marks_remote_messages_read(self):
        self.controller.set_connected(True, "movie-room")
        self.store.append("Alice", "hello")
        self.assertEqual(self.store.unread_count, 1)
        self.controller.toggle_panel()
        self.assertEqual(self.store.unread_count, 0)


if __name__ == "__main__":
    unittest.main()

