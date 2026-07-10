from __future__ import annotations

import csv
import importlib.util
import sys
import unittest
from datetime import timedelta
from pathlib import Path

from openqfuel.oem import parse_utc


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "source_registry.csv"
FETCH_SCRIPT = ROOT / "scripts" / "fetch_public_data.py"
WINDOWS = ROOT / "data" / "processed" / "artemis2" / "validation_windows.csv"
DISCONTINUITIES = (
    ROOT / "data" / "processed" / "artemis2" / "oem_detected_discontinuities.csv"
)
EVENTS = ROOT / "data" / "artemis2_event_registry.csv"


def load_fetch_module():
    spec = importlib.util.spec_from_file_location("fetch_public_data", FETCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load fetch_public_data.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SourceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with REGISTRY.open(newline="", encoding="utf-8") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_source_ids_are_unique(self) -> None:
        ids = [row["source_id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_urls_use_https(self) -> None:
        for row in self.rows:
            with self.subTest(source_id=row["source_id"]):
                self.assertTrue(row["url"].startswith("https://"))

    def test_downloadable_sources_have_local_filenames(self) -> None:
        for row in self.rows:
            if row["download"].lower() == "true":
                with self.subTest(source_id=row["source_id"]):
                    self.assertTrue(row["local_filename"].strip())

    def test_required_observed_flight_source_exists(self) -> None:
        source = next(row for row in self.rows if row["source_id"] == "D001")
        self.assertEqual(source["source_class"], "flight_ephemeris")
        self.assertEqual(
            source["observation_status"],
            "mixed_historical_reconstructed_and_predicted_operational_solution",
        )


class FetchScriptTests(unittest.TestCase):
    def test_registry_parser_finds_downloadable_sources(self) -> None:
        module = load_fetch_module()
        sources = module.read_sources(REGISTRY, None)
        self.assertGreaterEqual(len(sources), 5)
        self.assertIn("D001", {source.source_id for source in sources})

    def test_registry_parser_rejects_unknown_requested_id(self) -> None:
        module = load_fetch_module()
        with self.assertRaises(ValueError):
            module.read_sources(REGISTRY, {"DOES_NOT_EXIST"})


class ValidationWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with WINDOWS.open(newline="", encoding="utf-8") as handle:
            cls.windows = list(csv.DictReader(handle))
        with DISCONTINUITIES.open(newline="", encoding="utf-8") as handle:
            cls.discontinuities = list(csv.DictReader(handle))
        with EVENTS.open(newline="", encoding="utf-8") as handle:
            cls.events = list(csv.DictReader(handle))

    def test_five_validation_windows_are_frozen(self) -> None:
        validation = [row for row in self.windows if row["role"] == "validation"]
        self.assertEqual(len(validation), 5)

    def test_windows_do_not_overlap(self) -> None:
        intervals = sorted(
            (
                parse_utc(row["start_utc"]),
                parse_utc(row["stop_utc"]),
                row["window_id"],
            )
            for row in self.windows
        )
        for left, right in zip(intervals, intervals[1:]):
            self.assertLessEqual(left[1], right[0], f"{left[2]} overlaps {right[2]}")

    def test_windows_avoid_detected_discontinuity_buffers(self) -> None:
        for window in self.windows:
            start = parse_utc(window["start_utc"])
            stop = parse_utc(window["stop_utc"])
            for discontinuity in self.discontinuities:
                excluded_start = parse_utc(discontinuity["first_flagged_utc"]) - timedelta(
                    minutes=30
                )
                excluded_stop = parse_utc(discontinuity["last_flagged_utc"]) + timedelta(
                    minutes=30
                )
                with self.subTest(
                    window=window["window_id"],
                    discontinuity=discontinuity["discontinuity_id"],
                ):
                    self.assertTrue(stop <= excluded_start or start >= excluded_stop)

    def test_windows_avoid_published_burn_buffers(self) -> None:
        burns = [
            row
            for row in self.events
            if row["status"] == "executed"
            and (
                "correction" in row["event_name"].lower()
                or "injection" in row["event_name"].lower()
            )
        ]
        for window in self.windows:
            start = parse_utc(window["start_utc"])
            stop = parse_utc(window["stop_utc"])
            for burn in burns:
                burn_start = parse_utc(burn["actual_utc"])
                duration_s = float(burn["duration_s"])
                excluded_start = burn_start - timedelta(minutes=30)
                excluded_stop = burn_start + timedelta(
                    seconds=duration_s, minutes=30
                )
                with self.subTest(window=window["window_id"], burn=burn["event_id"]):
                    self.assertTrue(stop <= excluded_start or start >= excluded_stop)


if __name__ == "__main__":
    unittest.main()
