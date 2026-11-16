import hashlib
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "nexus-os"))
from core.web_importer import ImportRejected, OfflineImporter


class OfflineImporterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.inbox = self.root / "inbox"
        self.inbox.mkdir()
        self.destination = self.root / "imported"
        self.trusted = self.root / "trusted.json"
        self.events = []

    def tearDown(self):
        self.temporary.cleanup()

    def make_importer(self, archive: Path) -> OfflineImporter:
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.trusted.write_text(json.dumps({digest: "approved.bundle"}), encoding="utf-8")
        return OfflineImporter(
            self.inbox,
            self.destination,
            self.trusted,
            lambda event_type, payload: self.events.append((event_type, payload)) or 7,
        )

    def test_imports_trusted_data_archive_without_executable_permissions(self):
        archive = self.inbox / "data.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("records/catalog.csv", "id,label\n1,test\n")
        result = self.make_importer(archive).import_archive(archive.name)
        imported = self.destination / "approved.bundle" / "records" / "catalog.csv"
        self.assertEqual(result["package"], "approved.bundle")
        self.assertEqual(result["event_id"], 7)
        self.assertEqual(self.events[0][0], "import.completed")
        self.assertEqual(self.events[0][1]["package"], "approved.bundle")
        self.assertTrue(imported.is_file())
        if os.name == "posix":
            self.assertEqual(imported.stat().st_mode & 0o777, 0o600)

    def test_rejects_archive_without_trusted_digest(self):
        archive = self.inbox / "unknown.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("data.txt", "untrusted")
        self.trusted.write_text("{}", encoding="utf-8")
        with self.assertRaises(ImportRejected):
            OfflineImporter(self.inbox, self.destination, self.trusted).import_archive(archive.name)

    def test_rejects_path_traversal_and_executable_members(self):
        for member in ("../escape.txt", "run.sh"):
            archive = self.inbox / "bad.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr(member, "content")
            with self.subTest(member=member):
                with self.assertRaises(ImportRejected):
                    self.make_importer(archive).import_archive(archive.name)

    def test_rolls_back_files_if_event_bus_registration_fails(self):
        archive = self.inbox / "data.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("records.txt", "data")
        importer = self.make_importer(archive)

        def fail_event_writer(_event_type, _payload):
            raise OSError("database unavailable")

        importer.event_writer = fail_event_writer
        with self.assertRaises(ImportRejected):
            importer.import_archive(archive.name)
        self.assertFalse((self.destination / "approved.bundle").exists())


if __name__ == "__main__":
    unittest.main()
