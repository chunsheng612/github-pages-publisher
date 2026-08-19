import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from preflight import scan


class PreflightTests(unittest.TestCase):
    def test_static_site_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "index.html").write_text("<html><body>Hello</body></html>", encoding="utf-8")
            result = scan(root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["kind"], "static")

    def test_env_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "index.html").write_text("<html></html>", encoding="utf-8")
            (root / ".env").write_text("SECRET=abcdef1234567890", encoding="utf-8")
            result = scan(root)
            self.assertFalse(result["ok"])
            self.assertTrue(any("敏感" in x for x in result["blockers"]))

    def test_absolute_path_warns(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "index.html").write_text('<script src="/assets/app.js"></script>', encoding="utf-8")
            result = scan(root)
            self.assertTrue(result["ok"])
            self.assertTrue(result["warnings"])

    def test_needs_build(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "package.json").write_text('{"scripts":{"build":"vite build"}}', encoding="utf-8")
            result = scan(root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["kind"], "needs-build")


if __name__ == "__main__":
    unittest.main()
