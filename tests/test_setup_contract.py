"""SETUP.bat contract checks.

Дракончик Тоору
Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SetupContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / "SETUP.bat").read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_official_python_3147_sources_and_hashes_are_pinned(self):
        self.assertIn("python-3.14.7-embeddable-amd64.zip", self.text)
        self.assertIn(
            "76c3c0384ab3f822486f32450f3a4d20f5d65ad0ec32ee34290971aa0eb817e6",
            self.lower,
        )
        self.assertIn("python-3.14.7-embeddable-arm64.zip", self.text)
        self.assertIn(
            "b777fa08b68a177e350f8730c3e97a2b216d81e3eb5d183b039c65d43a6a2b3e",
            self.lower,
        )
        self.assertIn("python-3.14.7-embeddable-win32.zip", self.text)
        self.assertIn(
            "c784a4596d706d647d430286e2db1d1e3dcc1acb8bc6993fabf147fc00606e18",
            self.lower,
        )
        hashes = re.findall(r"python_sha256=([0-9a-f]{64})", self.lower)
        self.assertEqual(len(hashes), 3)

    def test_setup_uses_verified_https_without_powershell_command(self):
        self.assertIsNone(re.search(r"(?im)^\s*powershell(?:\.exe)?\b", self.text))
        self.assertIn("curl.exe", self.lower)
        self.assertIn("--proto =https", self.lower)
        self.assertIn("certutil.exe -hashfile", self.lower)
        self.assertIn("tar.exe -xf", self.lower)

    def test_runtime_is_portable_and_project_root_is_on_embedded_path(self):
        self.assertIn(r'set "TARGET=runtime\python"', self.text)
        self.assertIn(r"echo ..\..", self.text)
        self.assertIn("import core.server", self.text)
        self.assertNotRegex(self.text, r"(?i)\b[A-Z]:\\")

    def test_staging_and_rollback_are_present(self):
        self.assertIn(r'set "STAGING=runtime\python.new"', self.text)
        self.assertIn(r'set "PREVIOUS=runtime\python.previous"', self.text)
        self.assertIn("Выполняется откат", self.text)


if __name__ == "__main__":
    unittest.main()
