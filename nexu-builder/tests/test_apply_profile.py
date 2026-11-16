import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "apply-profile.py"
SPEC = importlib.util.spec_from_file_location("apply_profile", SCRIPT)
apply_profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(apply_profile)


class ApplyProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.profile = self.root / "profile.json"
        self.destination = self.root / "etc" / "nexus-os"

    def tearDown(self):
        self.temporary.cleanup()

    def write_profile(self, **overrides):
        profile = {
            "schema_version": 1,
            "packages": ["nexus-server", "lynis"],
            "theme": "violet",
            "icon": "dragon-mage",
            "personality": {"name": "Nexus Test", "tone": "objetivo"},
        }
        profile.update(overrides)
        self.profile.write_text(json.dumps(profile), encoding="utf-8")

    def test_writes_personality_and_selected_profile(self):
        self.write_profile()
        self.assertEqual(
            apply_profile.apply_profile(self.profile, self.destination),
            0,
        )
        stored = json.loads((self.destination / "personality.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["name"], "Nexus Test")
        self.assertEqual(stored["theme"], "violet")

    def test_rejects_unsupported_package(self):
        self.write_profile(packages=["unreviewed-package"])
        self.assertNotEqual(apply_profile.apply_profile(self.profile, self.destination), 0)
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
