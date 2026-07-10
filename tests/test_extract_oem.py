from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract_artemis2_oem.py"


def load_module():
    spec = importlib.util.spec_from_file_location("extract_artemis2_oem", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load extraction script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class NestedArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def build_outer(self, nested_member: str = "sample.asc") -> Path:
        nested_buffer = io.BytesIO()
        with ZipFile(nested_buffer, "w") as nested:
            nested.writestr(nested_member, b"CCSDS_OEM_VERS = 2.0\n")
        outer_path = self.root / "outer.zip"
        with ZipFile(outer_path, "w") as outer:
            outer.writestr("sample.zip", nested_buffer.getvalue())
        return outer_path

    def test_nested_archive_extracts_idempotently(self) -> None:
        archive = self.build_outer()
        output = self.root / "out"
        first = self.module.extract_nested_archive(archive, output)
        second = self.module.extract_nested_archive(archive, output)
        self.assertEqual(first, second)
        self.assertEqual(
            (output / "asc" / "sample.asc").read_bytes(),
            b"CCSDS_OEM_VERS = 2.0\n",
        )

    def test_nested_payload_path_traversal_is_rejected(self) -> None:
        archive = self.build_outer("../escape.asc")
        with self.assertRaises(ValueError):
            self.module.extract_nested_archive(archive, self.root / "out")


if __name__ == "__main__":
    unittest.main()
