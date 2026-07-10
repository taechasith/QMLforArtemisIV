"""Transparent correction-burn and propellant calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import yaml

from .dynamics import STANDARD_GRAVITY_M_S2


@dataclass(frozen=True)
class EngineSpec:
    name: str
    unit_thrust_n: float
    count: int

    @property
    def total_thrust_n(self) -> float:
        return self.unit_thrust_n * self.count


def load_public_engine_catalog(constraints_path: Path | str) -> dict[str, EngineSpec]:
    """Load public Orion thrust classes from the frozen Gate 2 configuration."""

    with Path(constraints_path).open(encoding="utf-8") as handle:
        thrust = yaml.safe_load(handle)["vehicle_reference"]["thrust_classes"]
    return {
        "main_engine": EngineSpec(
            "main_engine", float(thrust["main_engine"]["nominal_thrust_n"]), 1
        ),
        "auxiliary_engine": EngineSpec(
            "auxiliary_engine",
            float(thrust["auxiliary_engine"]["each_thrust_n"]),
            int(thrust["auxiliary_engine"]["count"]),
        ),
        "reaction_control_thruster": EngineSpec(
            "reaction_control_thruster",
            float(thrust["reaction_control_thruster"]["each_thrust_n"]),
            int(thrust["reaction_control_thruster"]["count"]),
        ),
    }


def rocket_equation_propellant_kg(
    initial_mass_kg: float, delta_v_m_s: float, specific_impulse_s: float
) -> float:
    """Return propellant consumed by an ideal impulsive maneuver."""

    if initial_mass_kg <= 0 or delta_v_m_s < 0 or specific_impulse_s <= 0:
        raise ValueError("Mass and Isp must be positive; delta-v must be nonnegative")
    final_mass = initial_mass_kg / math.exp(
        delta_v_m_s / (specific_impulse_s * STANDARD_GRAVITY_M_S2)
    )
    return initial_mass_kg - final_mass


def constant_thrust_propellant_kg(
    thrust_n: float, duration_s: float, specific_impulse_s: float
) -> float:
    """Return propellant consumed by a constant-thrust finite burn."""

    if thrust_n <= 0 or duration_s < 0 or specific_impulse_s <= 0:
        raise ValueError("Thrust and Isp must be positive; duration nonnegative")
    return thrust_n * duration_s / (specific_impulse_s * STANDARD_GRAVITY_M_S2)
