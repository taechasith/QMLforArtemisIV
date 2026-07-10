from __future__ import annotations

import csv
import math
import unittest
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs"


def load_yaml(name: str):
    with (CONFIG / name).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class Gate2ConfigurationTests(unittest.TestCase):
    def test_all_gate2_yaml_is_machine_readable(self) -> None:
        expected = {
            "compute_budget.yaml",
            "constraints.yaml",
            "crew_schedule.yaml",
            "human_acceleration_limits.yaml",
            "simulator_acceptance.yaml",
            "uncertainty_model.yaml",
        }
        self.assertTrue(expected.issubset({path.name for path in CONFIG.glob("*.yaml")}))
        for name in expected:
            with self.subTest(name=name):
                data = load_yaml(name)
                self.assertEqual(data["schema_version"], "0.2.0")
                self.assertEqual(data["status"], "frozen_gate_2_accepted")

    def test_practical_threshold_and_safety_margin_are_frozen(self) -> None:
        data = load_yaml("constraints.yaml")["practical_significance"]
        self.assertEqual(data["mission_stage"]["minimum_absolute_delta_v_improvement_m_s"], 0.25)
        self.assertEqual(data["mission_stage"]["minimum_relative_delta_v_improvement"], 0.10)
        self.assertEqual(data["mission_stage"]["safety_noninferiority_margin_absolute"], 0.001)

    def test_sleep_durations_match_utc_intervals(self) -> None:
        schedule = load_yaml("crew_schedule.yaml")
        for interval in schedule["protected_intervals"]:
            start = datetime.fromisoformat(interval["start_utc"].replace("Z", "+00:00"))
            stop = datetime.fromisoformat(interval["stop_utc"].replace("Z", "+00:00"))
            duration_h = (stop - start).total_seconds() / 3600.0
            with self.subTest(interval=interval["id"]):
                self.assertAlmostEqual(duration_h, interval["duration_h"], places=8)

    def test_acceleration_envelopes_become_no_less_restrictive(self) -> None:
        envelopes = load_yaml("human_acceleration_limits.yaml")[
            "deconditioned_conservative_envelopes"
        ]
        for axis, envelope in envelopes.items():
            upper = envelope["upper"]["acceleration_m_s2"]
            lower = envelope["lower"]["acceleration_m_s2"]
            with self.subTest(axis=axis, side="upper"):
                self.assertTrue(all(a >= b for a, b in zip(upper, upper[1:])))
            with self.subTest(axis=axis, side="lower"):
                self.assertTrue(all(a <= b for a, b in zip(lower, lower[1:])))

    def test_process_noise_si_conversion(self) -> None:
        model = load_yaml("uncertainty_model.yaml")
        factor = model["disturbance_process_noise"]["conversion_factor"]
        for name, event in model["disturbance_process_noise"]["events"].items():
            with self.subTest(event=name):
                self.assertTrue(
                    math.isclose(event["q_si"], event["q_source"] * factor, rel_tol=1e-12)
                )

    def test_published_rtc_sum_is_a_lower_bound(self) -> None:
        with (ROOT / "data" / "artemis2_event_registry.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            events = list(csv.DictReader(handle))
        total = sum(
            float(row["derived_delta_v_m_s"])
            for row in events
            if row["event_id"] in {"E007", "E008", "E009"}
        )
        expected = load_yaml("constraints.yaml")["historical_sanity_checks"][
            "actual_rtc1_to_rtc3_published_delta_v_lower_bound_m_s"
        ]
        self.assertAlmostEqual(total, expected, places=12)

    def test_compute_budget_contains_hard_ceiling(self) -> None:
        budget = load_yaml("compute_budget.yaml")
        ceiling = budget["global_resource_ceiling"]
        self.assertEqual(ceiling["cpu_core_hours"], 10000)
        self.assertEqual(ceiling["qpu_shots"], 50000000)
        self.assertTrue(budget["model_selection_limits"]["no_post_test_hyperparameter_changes"])


if __name__ == "__main__":
    unittest.main()
