from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from openqfuel.oem import OemEphemeris, StateVector
from openqfuel.validation import (
    ValidationWindow,
    aggregate_gate_status,
    leave_one_out_interpolation_metrics,
    parse_gmat_endpoint_report,
    relative_improvement,
    render_gmat_script,
    trajectory_error_metrics,
)


UTC = timezone.utc


def linear_ephemeris() -> OemEphemeris:
    start = datetime(2026, 4, 1, tzinfo=UTC)
    states = tuple(
        StateVector(
            start + timedelta(seconds=offset),
            (float(offset), 2.0 * offset, -float(offset)),
            (1.0, 2.0, -1.0),
        )
        for offset in (0, 10, 20, 30, 40)
    )
    return OemEphemeris(
        Path("sample.asc"),
        {"CREATION_DATE": "2026-04-01T00:00:40Z"},
        states,
        0,
    )


class ValidationMetricTests(unittest.TestCase):
    def test_relative_improvement_uses_baseline_denominator(self) -> None:
        self.assertAlmostEqual(relative_improvement(10.0, 2.0), 0.8)

    def test_gate_status_preserves_failures_and_pending_checks(self) -> None:
        self.assertEqual(
            aggregate_gate_status(["pass", "fail", "pending"]),
            "failed_repair_required",
        )
        self.assertEqual(
            aggregate_gate_status(["pass", "pending"]),
            "pending_external_validation",
        )

    def test_linear_hermite_leave_one_out_is_exact(self) -> None:
        metrics = leave_one_out_interpolation_metrics(linear_ephemeris(), [])
        self.assertEqual(metrics.samples, 3)
        self.assertLess(metrics.position_p95_km, 1e-12)
        self.assertLess(metrics.velocity_p95_m_s, 1e-12)

    def test_exclusion_removes_overlapping_interpolation_segments(self) -> None:
        ephemeris = linear_ephemeris()
        exclusion = [(ephemeris.states[1].epoch, ephemeris.states[1].epoch)]
        metrics = leave_one_out_interpolation_metrics(ephemeris, exclusion)
        self.assertEqual(metrics.samples, 1)

    def test_trajectory_metrics_keep_velocity_units_in_metres_per_second(self) -> None:
        reference = linear_ephemeris().states[:2]
        predicted = np.array(
            [
                reference[0].position_km + reference[0].velocity_km_s,
                reference[1].position_km
                + tuple(value + 0.001 for value in reference[1].velocity_km_s),
            ]
        )
        metrics = trajectory_error_metrics(predicted, reference)
        self.assertAlmostEqual(metrics.velocity_endpoint_m_s, np.sqrt(3.0))


class GmatEvidenceTests(unittest.TestCase):
    def test_script_freezes_same_force_terms_and_no_srp(self) -> None:
        ephemeris = linear_ephemeris()
        window = ValidationWindow(
            "V01", "test", ephemeris.states[0].epoch, ephemeris.states[-1].epoch
        )
        script = render_gmat_script([window], ephemeris)
        self.assertIn("SolarSystem.EphemerisSource = 'SPICE'", script)
        self.assertIn("PointMasses = {Luna, Sun}", script)
        self.assertIn("GravityField.Earth.Degree = 2", script)
        self.assertIn("F2ForceModel.SRP = Off", script)

    def test_endpoint_report_parser_reads_six_state_components(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "endpoints.txt"
            path.write_text("1 21600 1 2 3 4 5 6\n", encoding="utf-8")
            rows = parse_gmat_endpoint_report(path)
        np.testing.assert_allclose(rows[1], [1, 2, 3, 4, 5, 6])


if __name__ == "__main__":
    unittest.main()
