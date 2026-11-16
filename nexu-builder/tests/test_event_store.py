import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "nexus-os"))
from core import event_store


class EventStoreTests(unittest.TestCase):
    def test_events_are_persisted_and_queryable_by_cursor(self):
        original_dir = event_store.DATA_DIR
        original_database = event_store.DATABASE
        original_initialized = event_store._initialized
        with tempfile.TemporaryDirectory() as temporary:
            event_store.DATA_DIR = Path(temporary)
            event_store.DATABASE = event_store.DATA_DIR / "events.sqlite3"
            event_store._initialized = False
            try:
                first_id = event_store.record_event("import.completed", {"package": "one"})
                second_id = event_store.record_event("avatar.message", {"text": "hello"})
                later = event_store.events_after(after=first_id)
                self.assertEqual(second_id, first_id + 1)
                self.assertEqual([event["event_type"] for event in later], ["avatar.message"])
            finally:
                event_store.DATA_DIR = original_dir
                event_store.DATABASE = original_database
                event_store._initialized = original_initialized


if __name__ == "__main__":
    unittest.main()
