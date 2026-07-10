"""F0/F1/F2 cislunar trajectory propagation and maneuver dynamics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Sequence

import numpy as np
from scipy.integrate import solve_ivp

from .ephemeris import JplEphemeris


Fidelity = Literal["F0", "F1", "F2"]

EARTH_MU_KM3_S2 = 398600.435507
MOON_MU_KM3_S2 = 4902.800118
SUN_MU_KM3_S2 = 132712440041.9394
EARTH_EQUATORIAL_RADIUS_KM = 6378.1363
EARTH_J2 = 1.08262668e-3
STANDARD_GRAVITY_M_S2 = 9.80665


@dataclass(frozen=True)
class Maneuver:
    """A fixed-inertial-direction finite burn."""

    start_s: float
    duration_s: float
    thrust_n: float
    specific_impulse_s: float
    direction: tuple[float, float, float]

    def __post_init__(self) -> None:
        if self.start_s < 0 or self.duration_s <= 0:
            raise ValueError("Burn start must be nonnegative and duration positive")
        if self.thrust_n <= 0 or self.specific_impulse_s <= 0:
            raise ValueError("Thrust and specific impulse must be positive")
        norm = float(np.linalg.norm(self.direction))
        if not np.isclose(norm, 1.0, rtol=0.0, atol=1e-12):
            raise ValueError("Burn direction must be a unit vector")

    @property
    def stop_s(self) -> float:
        return self.start_s + self.duration_s

    def active(self, elapsed_s: float) -> bool:
        # Including the endpoint avoids presenting an artificial derivative
        # jump to an adaptive integrator that lands exactly on burn cutoff.
        return self.start_s <= elapsed_s <= self.stop_s


@dataclass(frozen=True)
class ForceModelSettings:
    """Numerical and physical settings for a propagation fidelity."""

    fidelity: Fidelity
    moon_gravity: bool
    sun_gravity: bool
    earth_j2: bool
    rtol: float
    atol: float
    max_step_s: float

    @classmethod
    def for_fidelity(cls, fidelity: Fidelity) -> "ForceModelSettings":
        if fidelity == "F0":
            return cls("F0", False, False, False, 1e-10, 1e-12, 600.0)
        if fidelity == "F1":
            return cls("F1", True, True, False, 1e-10, 1e-12, 600.0)
        if fidelity == "F2":
            return cls("F2", True, True, True, 1e-11, 1e-13, 300.0)
        raise ValueError(f"Unknown fidelity: {fidelity}")

    def tightened(self) -> "ForceModelSettings":
        """Return the frozen 100x-tighter, half-step verification settings."""

        return ForceModelSettings(
            self.fidelity,
            self.moon_gravity,
            self.sun_gravity,
            self.earth_j2,
            self.rtol / 100.0,
            self.atol / 100.0,
            self.max_step_s / 2.0,
        )


@dataclass(frozen=True)
class PropagationResult:
    elapsed_s: np.ndarray
    states: np.ndarray
    message: str

    @property
    def endpoint(self) -> np.ndarray:
        return self.states[-1]


def point_mass_acceleration(position_km: np.ndarray) -> np.ndarray:
    distance = float(np.linalg.norm(position_km))
    if distance <= 0:
        raise ValueError("Position cannot be at the force-model singularity")
    return -EARTH_MU_KM3_S2 * position_km / distance**3


def third_body_acceleration(
    spacecraft_km: np.ndarray,
    body_from_earth_km: np.ndarray,
    body_mu_km3_s2: float,
) -> np.ndarray:
    relative = body_from_earth_km - spacecraft_km
    return body_mu_km3_s2 * (
        relative / np.linalg.norm(relative) ** 3
        - body_from_earth_km / np.linalg.norm(body_from_earth_km) ** 3
    )


def earth_j2_acceleration(position_km: np.ndarray) -> np.ndarray:
    x, y, z = position_km
    radius = float(np.linalg.norm(position_km))
    radius_squared = radius * radius
    factor = (
        1.5
        * EARTH_J2
        * EARTH_MU_KM3_S2
        * EARTH_EQUATORIAL_RADIUS_KM**2
        / radius**5
    )
    return factor * np.array(
        [
            x * (5.0 * z * z / radius_squared - 1.0),
            y * (5.0 * z * z / radius_squared - 1.0),
            z * (5.0 * z * z / radius_squared - 3.0),
        ]
    )


def apply_impulse(
    state: Sequence[float], delta_v_m_s: Sequence[float]
) -> np.ndarray:
    """Apply an inertial impulsive delta-v to a six- or seven-state vector."""

    result = np.asarray(state, dtype=float).copy()
    if result.size not in {6, 7}:
        raise ValueError("State must contain position, velocity, and optional mass")
    delta = np.asarray(delta_v_m_s, dtype=float)
    if delta.shape != (3,):
        raise ValueError("delta_v_m_s must have three components")
    result[3:6] += delta / 1000.0
    return result


def _derivative(
    elapsed_s: float,
    state: np.ndarray,
    start_epoch: datetime,
    settings: ForceModelSettings,
    ephemeris: JplEphemeris | None,
    maneuvers: Sequence[Maneuver],
) -> np.ndarray:
    position = state[:3]
    acceleration = point_mass_acceleration(position)
    if settings.moon_gravity or settings.sun_gravity:
        if ephemeris is None:
            raise ValueError(f"{settings.fidelity} propagation requires DE440s")
        bodies = ephemeris.positions(start_epoch + timedelta(seconds=elapsed_s))
        if settings.moon_gravity:
            acceleration += third_body_acceleration(
                position, bodies.moon_km, MOON_MU_KM3_S2
            )
        if settings.sun_gravity:
            acceleration += third_body_acceleration(
                position, bodies.sun_km, SUN_MU_KM3_S2
            )
    if settings.earth_j2:
        acceleration += earth_j2_acceleration(position)

    mass_rate_kg_s = 0.0
    for maneuver in maneuvers:
        if maneuver.active(elapsed_s):
            if state.size != 7 or state[6] <= 0:
                raise ValueError("Finite burns require a positive mass state")
            direction = np.asarray(maneuver.direction)
            acceleration += maneuver.thrust_n / state[6] / 1000.0 * direction
            mass_rate_kg_s -= maneuver.thrust_n / (
                maneuver.specific_impulse_s * STANDARD_GRAVITY_M_S2
            )

    derivative = np.concatenate((state[3:6], acceleration))
    if state.size == 7:
        derivative = np.append(derivative, mass_rate_kg_s)
    return derivative


def propagate(
    start_epoch: datetime,
    initial_state: Sequence[float],
    duration_s: float,
    settings: ForceModelSettings,
    ephemeris: JplEphemeris | None = None,
    evaluation_times_s: Sequence[float] | None = None,
    maneuvers: Sequence[Maneuver] = (),
) -> PropagationResult:
    """Propagate a state in Earth-centered J2000 axes with DOP853."""

    if start_epoch.tzinfo is None:
        raise ValueError("start_epoch must be timezone-aware")
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    initial = np.asarray(initial_state, dtype=float)
    if initial.size not in {6, 7}:
        raise ValueError("Initial state must have six elements plus optional mass")
    if maneuvers and initial.size != 7:
        raise ValueError("Finite burns require mass as the seventh state element")

    if evaluation_times_s is None:
        evaluation = np.array([0.0, duration_s])
    else:
        evaluation = np.asarray(evaluation_times_s, dtype=float)
        if evaluation.ndim != 1 or evaluation.size == 0:
            raise ValueError("evaluation_times_s must be a nonempty vector")
        if np.any(np.diff(evaluation) <= 0):
            raise ValueError("evaluation_times_s must be strictly increasing")
        if evaluation[0] < 0 or evaluation[-1] > duration_s:
            raise ValueError("Evaluation times must lie inside the propagation span")

    solution = solve_ivp(
        lambda elapsed, state: _derivative(
            elapsed, state, start_epoch, settings, ephemeris, maneuvers
        ),
        (0.0, duration_s),
        initial,
        method="DOP853",
        t_eval=evaluation,
        rtol=settings.rtol,
        atol=settings.atol,
        max_step=settings.max_step_s,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    return PropagationResult(evaluation, solution.y.T, solution.message)
