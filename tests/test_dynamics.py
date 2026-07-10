from __future__ import annotations

import math
import unittest
from datetime import datetime, timezone

import numpy as np

from openqfuel.dynamics import (
    EARTH_MU_KM3_S2,
    ForceModelSettings,
    Maneuver,
    apply_impulse,
    propagate,
)
from openqfuel.propulsion import (
    constant_thrust_propellant_kg,
    rocket_equation_propellant_kg,
)


UTC = timezone.utc


class DynamicsTests(unittest.TestCase):
    def test_f0_closes_a_circular_orbit(self) -> None:
        radius_km = 7000.0
        speed_km_s = math.sqrt(EARTH_MU_KM3_S2 / radius_km)
        period_s = 2.0 * math.pi * math.sqrt(radius_km**3 / EARTH_MU_KM3_S2)
        initial = [radius_km, 0.0, 0.0, 0.0, speed_km_s, 0.0]
        result = propagate(
            datetime(2026, 4, 1, tzinfo=UTC),
            initial,
            period_s,
            ForceModelSettings.for_fidelity("F0"),
        )
        np.testing.assert_allclose(result.endpoint, initial, rtol=0.0, atol=2e-5)

    def test_impulse_uses_metres_per_second(self) -> None:
        state = apply_impulse([7000, 0, 0, 0, 7.5, 0], [1, -2, 3])
        np.testing.assert_allclose(state[3:6], [0.001, 7.498, 0.003])

    def test_finite_burn_mass_matches_constant_flow_equation(self) -> None:
        maneuver = Maneuver(0.0, 10.0, 1000.0, 300.0, (0.0, 1.0, 0.0))
        initial_mass = 25000.0
        result = propagate(
            datetime(2026, 4, 1, tzinfo=UTC),
            [7000, 0, 0, 0, 7.5, 0, initial_mass],
            10.0,
            ForceModelSettings.for_fidelity("F0"),
            maneuvers=[maneuver],
        )
        expected = constant_thrust_propellant_kg(1000.0, 10.0, 300.0)
        self.assertAlmostEqual(initial_mass - result.endpoint[6], expected, places=9)

    def test_rocket_equation_zero_delta_v_uses_no_propellant(self) -> None:
        self.assertEqual(rocket_equation_propellant_kg(25000, 0, 314), 0.0)

    def test_tightened_settings_follow_frozen_rule(self) -> None:
        nominal = ForceModelSettings.for_fidelity("F2")
        tight = nominal.tightened()
        self.assertEqual(tight.rtol, nominal.rtol / 100)
        self.assertEqual(tight.atol, nominal.atol / 100)
        self.assertEqual(tight.max_step_s, nominal.max_step_s / 2)


if __name__ == "__main__":
    unittest.main()
