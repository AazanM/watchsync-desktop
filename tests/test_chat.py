import unittest

from syncplay.chat import ChatStore


class ChatStoreTests(unittest.TestCase):
    def test_remote_messages_increment_unread_until_reader_is_active(self):
        store = ChatStore()
        store.append("Alice", "First")
        self.assertEqual(store.unread_count, 1)
        store.set_reader_active(True)
        self.assertEqual(store.unread_count, 0)
        store.append("Alice", "Second")
        self.assertEqual(store.unread_count, 0)

    def test_local_messages_do_not_increment_unread(self):
        store = ChatStore()
        store.append("Me", "Hello", is_local=True)
        self.assertEqual(store.unread_count, 0)

    def test_store_is_bounded_and_clear_removes_session_history(self):
        store = ChatStore(max_messages=2)
        store.append("A", "one")
        store.append("B", "two")
        store.append("C", "three")
        self.assertEqual([message.text for message in store.snapshot()], ["two", "three"])
        store.clear()
        self.assertEqual(store.snapshot(), ())
        self.assertEqual(store.unread_count, 0)

    def test_subscribers_receive_message_and_unread_events(self):
        events = []
        store = ChatStore()
        unsubscribe = store.subscribe(lambda event, payload: events.append((event, payload)))
        message = store.append("Alice", "Hello")
        unsubscribe()
        store.append("Bob", "Ignored by subscriber")
        self.assertEqual(events[0], ("message", message))
        self.assertEqual(events[1], ("unread", 1))


if __name__ == "__main__":
    unittest.main()

