import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_LIST = PROJECT_ROOT / "iso" / "config" / "package-lists" / "nexus.list.chroot"


class DefensiveIsoProfileTests(unittest.TestCase):
    def test_excludes_intrusion_packages(self):
        packages = set(PACKAGE_LIST.read_text(encoding="utf-8").split())
        excluded = {
            "aircrack-ng",
            "ettercap-text-only",
            "hashcat",
            "hydra",
            "john",
            "nmap",
            "recon-ng",
            "sqlmap",
            "wifite",
        }
        self.assertTrue(excluded.isdisjoint(packages), excluded & packages)

    def test_includes_defensive_tools(self):
        packages = set(PACKAGE_LIST.read_text(encoding="utf-8").split())
        included = {"apparmor", "clamav", "lynis", "suricata", "yara"}
        self.assertTrue(included.issubset(packages), included - packages)


if __name__ == "__main__":
    unittest.main()
