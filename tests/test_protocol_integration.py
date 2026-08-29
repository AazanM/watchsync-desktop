import hashlib
import json
import socket
import time
import unittest

from syncplay.private_server import PrivateServerController


def free_port():
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


class RawSyncplayClient(object):
    def __init__(self, port, username, password, room):
        self.socket = socket.create_connection(("127.0.0.1", port), timeout=2)
        self.socket.settimeout(0.15)
        self.buffer = b""
        self.send({
            "Hello": {
                "username": username,
                "password": hashlib.md5(password.encode("utf-8")).hexdigest(),
                "room": {"name": room},
                "version": "1.2.255",
                "realversion": "1.7.6",
                "features": {
                    "chat": True,
                    "uiMode": "GUI",
                    "sharedPlaylists": True,
                    "readiness": True,
                },
            }
        })

    def send(self, payload):
        self.socket.sendall((json.dumps(payload) + "\r\n").encode("utf-8"))

    def messages_until(self, predicate, timeout=3):
        messages = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                line = line.strip()
                if line:
                    message = json.loads(line.decode("utf-8"))
                    messages.append(message)
                    if predicate(message):
                        return messages
            try:
                chunk = self.socket.recv(8192)
                if not chunk:
                    break
                self.buffer += chunk
            except socket.timeout:
                pass
        self.fail_messages(messages, predicate)

    @staticmethod
    def fail_messages(messages, predicate):
        raise AssertionError("Expected protocol message was not received. Got: {!r}".format(messages))

    def close(self):
        self.socket.close()


class ProtocolIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.port = free_port()
        self.password = "integration-password"
        self.server = PrivateServerController()
        self.server.start(self.port, self.password)
        deadline = time.time() + 3
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.05)
        self.clients = []

    def tearDown(self):
        for client in self.clients:
            client.close()
        self.server.stop()

    def client(self, username):
        client = RawSyncplayClient(self.port, username, self.password, "integration-room")
        self.clients.append(client)
        client.messages_until(lambda message: "Hello" in message)
        return client

    def test_unmodified_protocol_broadcasts_chat_to_both_clients(self):
        alice = self.client("Alice")
        bob = self.client("Bob")
        alice.send({"Chat": "hello from Alice"})
        expected = lambda message: message.get("Chat", {}).get("message") == "hello from Alice"
        alice_messages = alice.messages_until(expected)
        bob_messages = bob.messages_until(expected)
        self.assertEqual(alice_messages[-1]["Chat"]["username"], "Alice")
        self.assertEqual(bob_messages[-1]["Chat"]["username"], "Alice")

    def test_file_metadata_is_relayed_without_media_transfer(self):
        alice = self.client("Alice")
        bob = self.client("Bob")
        file_info = {"name": "movie.mkv", "size": 123456, "duration": 5400.0}
        alice.send({"Set": {"file": file_info}})
        bob_messages = bob.messages_until(
            lambda message: message.get("Set", {}).get("user", {}).get("Alice", {}).get("file") == file_info
        )
        relayed = bob_messages[-1]["Set"]["user"]["Alice"]["file"]
        self.assertEqual(relayed, file_info)


if __name__ == "__main__":
    unittest.main()

