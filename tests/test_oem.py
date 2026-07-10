from __future__ import annotations

import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from openqfuel.oem import parse_oem


SAMPLE = """<html>archive wrapper</html>
CCSDS_OEM_VERS = 2.0
CREATION_DATE = 2026-04-02T00:05:00
ORIGINATOR = NASA/JSC/FOD/FDO
META_START
OBJECT_NAME = EM2
OBJECT_ID = 24
CENTER_NAME = EARTH
REF_FRAME = EME2000
TIME_SYSTEM = UTC
START_TIME = 2026-04-02T00:00:00
STOP_TIME = 2026-04-02T00:10:00
META_STOP
2026-04-02T00:00:00 0 0 0 1 0 0
2026-04-02T00:10:00 600 0 0 1 0 0
"""


class OemParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "sample.asc"
        self.path.write_text(SAMPLE, encoding="utf-8")

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_html_prefix_is_ignored(self) -> None:
        ephemeris = parse_oem(self.path)
        self.assertEqual(ephemeris.wrapper_prefix_lines, 1)
        self.assertEqual(len(ephemeris.states), 2)
        self.assertEqual(ephemeris.header["REF_FRAME"], "EME2000")

    def test_hermite_interpolation_preserves_constant_velocity(self) -> None:
        ephemeris = parse_oem(self.path)
        midpoint = ephemeris.start_time + timedelta(minutes=5)
        state = ephemeris.interpolate(midpoint)
        self.assertAlmostEqual(state.position_km[0], 300.0, places=12)
        self.assertAlmostEqual(state.velocity_km_s[0], 1.0, places=12)

    def test_out_of_range_interpolation_fails(self) -> None:
        ephemeris = parse_oem(self.path)
        with self.assertRaises(ValueError):
            ephemeris.interpolate(ephemeris.start_time - timedelta(seconds=1))


if __name__ == "__main__":
    unittest.main()
