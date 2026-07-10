from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from openqfuel.constraints import check_candidate_burn


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE = ROOT / "configs/crew_schedule.yaml"
ACCELERATION = ROOT / "configs/human_acceleration_limits.yaml"
UTC = timezone.utc


class ConstraintTests(unittest.TestCase):
    def test_routine_burn_during_protected_sleep_is_rejected(self) -> None:
        result = check_candidate_burn(
            datetime(2026, 4, 3, 10, tzinfo=UTC),
            30.0,
            (0.01, 0.0, 0.0),
            SCHEDULE,
            ACCELERATION,
        )
        self.assertFalse(result.passed)
        self.assertIn("protected_crew_interval:S02", result.violations)

    def test_emergency_override_requires_reason(self) -> None:
        missing = check_candidate_burn(
            datetime(2026, 4, 3, 10, tzinfo=UTC),
            30.0,
            (0.01, 0.0, 0.0),
            SCHEDULE,
            ACCELERATION,
            emergency_override=True,
        )
        accepted = check_candidate_burn(
            datetime(2026, 4, 3, 10, tzinfo=UTC),
            30.0,
            (0.01, 0.0, 0.0),
            SCHEDULE,
            ACCELERATION,
            emergency_override=True,
            override_reason="time-critical navigation correction",
        )
        self.assertIn("emergency_override_missing_reason", missing.violations)
        self.assertTrue(accepted.passed)

    def test_excessive_z_acceleration_is_rejected(self) -> None:
        result = check_candidate_burn(
            datetime(2026, 4, 3, 18, tzinfo=UTC),
            120.0,
            (0.0, 0.0, 5.0),
            SCHEDULE,
            ACCELERATION,
        )
        self.assertFalse(result.passed)
        self.assertTrue(any(item.startswith("acceleration:z_axis") for item in result.violations))


if __name__ == "__main__":
    unittest.main()
