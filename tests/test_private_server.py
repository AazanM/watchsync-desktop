import socket
import sys
import time
import unittest

from syncplay.private_server import PrivateServerController, PrivateServerError


class PrivateServerControllerTests(unittest.TestCase):
    def test_rejects_invalid_port(self):
        controller = PrivateServerController(command=[sys.executable, "-c", "pass"])
        with self.assertRaises(PrivateServerError):
            controller.start(70000, "password")

    def test_rejects_port_already_in_use(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        controller = PrivateServerController(command=[sys.executable, "-c", "pass"])
        try:
            with self.assertRaises(PrivateServerError):
                controller.start(port, "password")
        finally:
            listener.close()

    def test_start_and_stop_owns_child_process(self):
        controller = PrivateServerController(
            command=[sys.executable, "-u", "-c", "import time; print('ready'); time.sleep(30)"]
        )
        controller.start(18888, "password")
        try:
            deadline = time.time() + 2
            while not controller.logs and time.time() < deadline:
                time.sleep(0.02)
            self.assertTrue(controller.is_running)
            self.assertEqual(controller.logs, ("ready",))
        finally:
            controller.stop()
        self.assertFalse(controller.is_running)


if __name__ == "__main__":
    unittest.main()

