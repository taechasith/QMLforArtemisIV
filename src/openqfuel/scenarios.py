"""D003 scenario generation primitives for the Phase 1 prediction benchmark."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import norm, qmc, t, truncnorm

from .constraints import check_candidate_burn
from .dynamics import (
    STANDARD_GRAVITY_M_S2,
    ForceModelSettings,
    Maneuver,
    apply_impulse,
    propagate,
)
from .gate4 import boundary_case_ids, derive_seed
from .oem import OemEphemeris, parse_utc


SOBOL_DIMENSIONS = 52
PROBABILITY_EPSILON = 1e-12


@dataclass(frozen=True)
class Vehicle:
    mass_kg: float
    usable_propellant_kg: float
    reserve_kg: float
    specific_impulse_s: float
    rcs_thrust_n: float
    auxiliary_thrust_n: float
    main_thrust_n: float


@dataclass(frozen=True)
class UncertaintySample:
    state_position_km: np.ndarray
    state_velocity_m_s: np.ndarray
    navigation_position_km: np.ndarray
    navigation_velocity_m_s: np.ndarray
    disturbance_velocity_m_s: np.ndarray
    communication_hold_min: float
    burn_delay_min: float
    mass_error_fraction: float
    sobol_row: np.ndarray


@dataclass(frozen=True)
class ExecutionError:
    thrust_scale: float
    pointing_bias_deg: float
    additive_delta_v_m_s: np.ndarray


@dataclass(frozen=True)
class TargetingContext:
    target_epoch: datetime
    duration_s: float
    target_state: np.ndarray
    state_to_terminal_position: np.ndarray
    burn_offsets_s: tuple[float, float, float, float]
    burn_to_terminal_position: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]


@dataclass(frozen=True)
class CandidatePlan:
    index: int
    planned_start_offset_s: float
    planned_delta_v_m_s: np.ndarray
    planned_duration_s: float
    thrust_class: str
    thrust_n: float


@dataclass(frozen=True)
class ExecutionResult:
    endpoint: np.ndarray
    actual_delta_v_m_s: np.ndarray
    propellant_used_kg: float
    actual_start_offset_s: float
    actual_duration_s: float
    burn_mass_kg: float
    actual_thrust_n: float
    minimum_lunar_surface_altitude_km: float | None
    nonconverged: bool
    execution_violation: str | None


@dataclass(frozen=True)
class Outcome:
    robust_total_correction_delta_v_m_s: float
    independently_propagated_feasible: bool
    correction_delta_v_m_s: float
    burn_vector_x_m_s: float
    burn_vector_y_m_s: float
    burn_vector_z_m_s: float
    terminal_position_error_km: float
    terminal_velocity_error_m_s: float
    terminal_margin: float
    propellant_used_kg: float
    minimum_lunar_surface_altitude_km: float | None
    nonconverged: bool
    violation_code: str | None

    def as_mapping(self) -> dict[str, Any]:
        return asdict(self)


def sobol_rows(count: int, seed: int, dimensions: int = SOBOL_DIMENSIONS) -> np.ndarray:
    """Return a deterministic scrambled Sobol design without balance warnings."""

    if count <= 0 or dimensions <= 0:
        raise ValueError("Sobol count and dimensions must be positive")
    exponent = int(math.ceil(math.log2(count)))
    sampler = qmc.Sobol(d=dimensions, scramble=True, seed=seed)
    return sampler.random_base2(exponent)[:count]


def _clipped_probability(value: np.ndarray | float) -> np.ndarray:
    return np.clip(
        np.asarray(value, dtype=float), PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON
    )


def standard_variates(probabilities: Sequence[float], family: str) -> np.ndarray:
    """Transform Sobol probabilities under the frozen family distribution."""

    values = _clipped_probability(probabilities)
    if family == "U4":
        return truncnorm.ppf(values, -3.0, 3.0)
    if family == "U5":
        raw = t.ppf(values, df=5)
        variance_scale = math.sqrt(5.0 / 3.0)
        return np.clip(raw / variance_scale, -6.0, 6.0)
    return norm.ppf(values)


def _select(values: Sequence[float], probability: float) -> float:
    index = min(int(float(probability) * len(values)), len(values) - 1)
    return float(values[index])


def sample_uncertainty(
    sobol_row: np.ndarray,
    family: str,
    uncertainty_config: Mapping[str, Any],
    generation_config: Mapping[str, Any],
    remaining_seconds: float,
) -> UncertaintySample:
    if sobol_row.shape != (SOBOL_DIMENSIONS,):
        raise ValueError(f"Expected one {SOBOL_DIMENSIONS}-dimensional Sobol row")
    if family not in {"U0", "U1", "U2", "U3", "U4", "U5"}:
        raise ValueError(f"Unknown uncertainty family: {family}")

    normal_values = standard_variates(sobol_row[:18], family)
    state_active = family in set(
        generation_config["uncertainty_application"]["state_dispersion"][
            "active_families"
        ]
    )
    navigation_active = family in set(
        generation_config["uncertainty_application"]["navigation_error"][
            "active_families"
        ]
    )
    disturbance_active = family in set(
        generation_config["uncertainty_application"]["disturbance"]["active_families"]
    )
    stress_active = family in set(
        generation_config["uncertainty_application"]["operational_stress"][
            "active_families"
        ]
    )

    state = uncertainty_config["initial_state_dispersion_3sigma"]
    navigation = uncertainty_config["initial_navigation_uncertainty_3sigma"]
    state_position = normal_values[0:3] * float(state["position_km"]) / 3.0
    state_velocity = normal_values[3:6] * float(state["velocity_m_s"]) / 3.0
    navigation_position = normal_values[6:9] * float(navigation["position_km"]) / 3.0
    navigation_velocity = normal_values[9:12] * float(navigation["velocity_m_s"]) / 3.0
    if not state_active:
        state_position = np.zeros(3)
        state_velocity = np.zeros(3)
    if not navigation_active:
        navigation_position = np.zeros(3)
        navigation_velocity = np.zeros(3)

    disturbance_velocity = np.zeros(3)
    if disturbance_active:
        q_si = float(
            uncertainty_config["disturbance_process_noise"]["events"][
                "pressure_swing_adsorption_awake"
            ]["q_si"]
        )
        sigma_m_s = math.sqrt(q_si * remaining_seconds)
        disturbance_velocity = normal_values[12:15] * sigma_m_s

    stress = generation_config["uncertainty_application"]["operational_stress"]
    if stress_active:
        communication_hold = _select(
            stress["communication_hold_values_min"], sobol_row[15]
        )
        burn_delay = _select(stress["burn_delay_values_min"], sobol_row[16])
        mass_error = _select(stress["mass_error_fraction_values"], sobol_row[17])
    else:
        communication_hold = 0.0
        burn_delay = 0.0
        mass_error = 0.0

    return UncertaintySample(
        state_position,
        state_velocity,
        navigation_position,
        navigation_velocity,
        disturbance_velocity,
        communication_hold,
        burn_delay,
        mass_error,
        sobol_row,
    )


def _unit_vector(values: Sequence[float]) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    norm_value = float(np.linalg.norm(vector))
    if norm_value <= 1e-15:
        return np.array([1.0, 0.0, 0.0])
    return vector / norm_value


def execution_error(
    sample: UncertaintySample,
    family: str,
    candidate_index: int,
    uncertainty_config: Mapping[str, Any],
    generation_config: Mapping[str, Any],
) -> ExecutionError:
    if not 1 <= candidate_index <= 5:
        raise ValueError("candidate_index must lie in [1, 5]")
    active = family in set(
        generation_config["uncertainty_application"]["execution_error"][
            "active_families"
        ]
    )
    if not active or candidate_index == 1:
        return ExecutionError(1.0, 0.0, np.zeros(3))
    offset = 21 + (candidate_index - 1) * 6
    z = standard_variates(sample.sobol_row[offset : offset + 6], family)
    execution = uncertainty_config["thruster_execution_3sigma"]
    scale_sigma = float(execution["scale_factor_ppm"]) / 3.0e6
    pointing_sigma = float(execution["misalignment_deg"]) / 3.0
    additive_sigma = math.hypot(
        float(execution["additive_bias_m_s"]) / 3.0,
        float(execution["additive_noise_m_s"]) / 3.0,
    )
    return ExecutionError(
        max(0.0, 1.0 + z[0] * scale_sigma),
        float(z[1] * pointing_sigma),
        _unit_vector(z[3:6]) * float(z[2] * additive_sigma),
    )


def vehicle_from_configs(
    constraints: Mapping[str, Any], generation: Mapping[str, Any]
) -> Vehicle:
    reference = constraints["vehicle_reference"]
    hard = constraints["hard_constraints"]
    return Vehicle(
        float(reference["post_tli_mass"]["value_kg"]),
        float(reference["usable_propellant"]["value_kg"]),
        float(hard["propellant_reserve"]["nominal_reserve_kg"]),
        float(generation["vehicle_and_burn"]["specific_impulse_s"]),
        float(
            reference["thrust_classes"]["reaction_control_thruster"]["each_thrust_n"]
        ),
        float(reference["thrust_classes"]["auxiliary_engine"]["each_thrust_n"]),
        float(reference["thrust_classes"]["main_engine"]["nominal_thrust_n"]),
    )


def select_thrust(delta_v_m_s: float, vehicle: Vehicle) -> tuple[str, float]:
    if delta_v_m_s <= 0.75:
        return "RCS_LOW", vehicle.rcs_thrust_n
    if delta_v_m_s <= 3.0:
        return "AUX_MED", vehicle.auxiliary_thrust_n
    return "MAIN_HIGH", vehicle.main_thrust_n


def rocket_propellant_kg(mass_kg: float, delta_v_m_s: float, isp_s: float) -> float:
    if delta_v_m_s <= 0.0:
        return 0.0
    return mass_kg * (1.0 - math.exp(-delta_v_m_s / (isp_s * STANDARD_GRAVITY_M_S2)))


def planned_burn_duration_s(
    mass_kg: float, delta_v_m_s: float, thrust_n: float, isp_s: float
) -> float:
    propellant = rocket_propellant_kg(mass_kg, delta_v_m_s, isp_s)
    if propellant == 0.0:
        return 0.0
    mass_flow = thrust_n / (isp_s * STANDARD_GRAVITY_M_S2)
    return propellant / mass_flow


def _least_aligned_axis(direction: np.ndarray) -> np.ndarray:
    return np.eye(3)[int(np.argmin(np.abs(direction)))]


def rotate_direction(direction: np.ndarray, angle_deg: float) -> np.ndarray:
    unit = _unit_vector(direction)
    if angle_deg == 0.0:
        return unit
    axis = _unit_vector(np.cross(unit, _least_aligned_axis(unit)))
    angle = math.radians(angle_deg)
    rotated = (
        unit * math.cos(angle)
        + np.cross(axis, unit) * math.sin(angle)
        + axis * np.dot(axis, unit) * (1.0 - math.cos(angle))
    )
    return _unit_vector(rotated)


def _propagate_no_burn(
    epoch: datetime,
    state: np.ndarray,
    duration_s: float,
    settings: ForceModelSettings,
    ephemeris: Any,
) -> np.ndarray:
    return propagate(epoch, state, duration_s, settings, ephemeris).endpoint


def _ideal_impulse_endpoint(
    epoch: datetime,
    state: np.ndarray,
    duration_s: float,
    start_offset_s: float,
    delta_v_m_s: np.ndarray,
    settings: ForceModelSettings,
    ephemeris: Any,
) -> np.ndarray:
    if start_offset_s <= 0.0:
        at_burn = state.copy()
    else:
        at_burn = propagate(epoch, state, start_offset_s, settings, ephemeris).endpoint
    after_burn = apply_impulse(at_burn, delta_v_m_s)
    remaining = duration_s - start_offset_s
    if remaining <= 0.0:
        return after_burn
    return propagate(
        epoch + timedelta(seconds=start_offset_s),
        after_burn,
        remaining,
        settings,
        ephemeris,
    ).endpoint


def _burn_offsets(
    epoch: datetime,
    target_epoch: datetime,
    tli_epoch: datetime,
    quantiles: Sequence[float],
) -> tuple[float, float, float, float]:
    duration = (target_epoch - epoch).total_seconds()
    earliest = max(0.0, (tli_epoch + timedelta(hours=3) - epoch).total_seconds())
    latest = duration - 3.0 * 3600.0 - 120.0
    if latest <= earliest:
        raise ValueError("No valid correction-burn timing interval remains")
    values = tuple(earliest + float(value) * (latest - earliest) for value in quantiles)
    if len(values) != 4:
        raise ValueError("Exactly four targeted candidate times are required")
    return values  # type: ignore[return-value]


def build_targeting_context(
    epoch: datetime,
    nominal_state: np.ndarray,
    target_epoch: datetime,
    tli_epoch: datetime,
    settings: ForceModelSettings,
    ephemeris: Any,
    generation_config: Mapping[str, Any],
) -> TargetingContext:
    duration_s = (target_epoch - epoch).total_seconds()
    if duration_s <= 0.0:
        raise ValueError("Target epoch must follow the group epoch")
    target_state = _propagate_no_burn(
        epoch, nominal_state, duration_s, settings, ephemeris
    )
    target_config = generation_config["targeting_reference"]
    position_step = float(target_config["state_sensitivity"]["position_step_km"])
    velocity_step = float(target_config["state_sensitivity"]["velocity_step_m_s"])
    state_matrix = np.empty((3, 6), dtype=float)
    for index in range(6):
        perturbed = nominal_state.copy()
        step = position_step if index < 3 else velocity_step
        perturbed[index] += step if index < 3 else step / 1000.0
        endpoint = _propagate_no_burn(epoch, perturbed, duration_s, settings, ephemeris)
        state_matrix[:, index] = (endpoint[:3] - target_state[:3]) / step

    timing = generation_config["decision_set"]["targeted_candidates"]
    offsets = _burn_offsets(epoch, target_epoch, tli_epoch, timing["timing_quantiles"])
    burn_step = float(target_config["burn_sensitivity"]["delta_v_step_m_s"])
    burn_matrices: list[np.ndarray] = []
    for offset in offsets:
        matrix = np.empty((3, 3), dtype=float)
        for axis in range(3):
            impulse = np.zeros(3)
            impulse[axis] = burn_step
            endpoint = _ideal_impulse_endpoint(
                epoch,
                nominal_state,
                duration_s,
                offset,
                impulse,
                settings,
                ephemeris,
            )
            matrix[:, axis] = (endpoint[:3] - target_state[:3]) / burn_step
        burn_matrices.append(matrix)
    return TargetingContext(
        target_epoch,
        duration_s,
        target_state,
        state_matrix,
        offsets,
        tuple(burn_matrices),  # type: ignore[arg-type]
    )


def cap_delta_v(vector: np.ndarray, maximum_m_s: float) -> np.ndarray:
    magnitude = float(np.linalg.norm(vector))
    if magnitude <= maximum_m_s or magnitude == 0.0:
        return vector
    return vector * (maximum_m_s / magnitude)


def build_candidate_plans(
    estimated_perturbation: np.ndarray,
    sample: UncertaintySample,
    targeting: TargetingContext,
    vehicle: Vehicle,
    generation_config: Mapping[str, Any],
) -> list[CandidatePlan]:
    if estimated_perturbation.shape != (6,):
        raise ValueError("Estimated perturbation must have six components")
    miss = targeting.state_to_terminal_position @ estimated_perturbation
    decision = generation_config["decision_set"]
    targeted = decision["targeted_candidates"]
    scales = [float(value) for value in targeted["correction_scale"]]
    maximum = float(decision["maximum_candidate_delta_v_m_s"])
    probe_direction = _unit_vector(standard_variates(sample.sobol_row[18:21], "U0"))
    plans = [CandidatePlan(1, 0.0, np.zeros(3), 0.0, "RCS_LOW", vehicle.rcs_thrust_n)]
    for offset_index, (offset, matrix, scale) in enumerate(
        zip(targeting.burn_offsets_s, targeting.burn_to_terminal_position, scales),
        start=2,
    ):
        correction = -np.linalg.pinv(matrix, rcond=1e-10) @ miss
        correction *= scale
        if offset_index == 5:
            correction += probe_direction * float(
                targeted["candidate_5_orthogonal_probe_m_s"]
            )
        correction = cap_delta_v(correction, maximum)
        magnitude = float(np.linalg.norm(correction))
        thrust_class, thrust = select_thrust(magnitude, vehicle)
        duration = planned_burn_duration_s(
            vehicle.mass_kg, magnitude, thrust, vehicle.specific_impulse_s
        )
        plans.append(
            CandidatePlan(
                offset_index,
                float(offset),
                correction,
                duration,
                thrust_class,
                thrust,
            )
        )
    return plans


def robust_cost_m_s(
    planned_delta_v_m_s: np.ndarray,
    family: str,
    uncertainty_config: Mapping[str, Any],
    generation_config: Mapping[str, Any],
) -> float:
    magnitude = float(np.linalg.norm(planned_delta_v_m_s))
    active = family in set(
        generation_config["uncertainty_application"]["execution_error"][
            "active_families"
        ]
    )
    if not active or magnitude == 0.0:
        return magnitude
    execution = uncertainty_config["thruster_execution_3sigma"]
    scale_sigma = float(execution["scale_factor_ppm"]) / 3.0e6
    pointing_sigma = math.radians(float(execution["misalignment_deg"]) / 3.0)
    additive_bias_sigma = float(execution["additive_bias_m_s"]) / 3.0
    additive_noise_sigma = float(execution["additive_noise_m_s"]) / 3.0
    sigma = math.sqrt(
        (magnitude * scale_sigma) ** 2
        + (magnitude * math.sin(pointing_sigma)) ** 2
        + additive_bias_sigma**2
        + additive_noise_sigma**2
    )
    return magnitude + 3.0 * sigma


def _lunar_sample_epochs(
    center: datetime, generation_config: Mapping[str, Any]
) -> tuple[datetime, ...]:
    definition = generation_config["lunar_altitude_evaluation"]
    half_width_s = int(float(definition["half_width_min"]) * 60.0)
    step_s = int(definition["step_s"])
    if half_width_s <= 0 or step_s <= 0 or (2 * half_width_s) % step_s:
        raise ValueError("Lunar-altitude sampling window must divide evenly")
    return tuple(
        center + timedelta(seconds=offset)
        for offset in range(-half_width_s, half_width_s + 1, step_s)
    )


def _propagate_with_markers(
    start_epoch: datetime,
    state: np.ndarray,
    duration_s: float,
    settings: ForceModelSettings,
    ephemeris: Any,
    marker_epochs: Sequence[datetime],
    maneuvers: Sequence[Maneuver] = (),
) -> tuple[np.ndarray, list[tuple[datetime, np.ndarray]]]:
    relevant = [
        (marker, (marker - start_epoch).total_seconds())
        for marker in marker_epochs
        if 0.0 <= (marker - start_epoch).total_seconds() <= duration_s
    ]
    evaluation = sorted(
        {duration_s, *(offset for _marker, offset in relevant if offset > 0.0)}
    )
    result = propagate(
        start_epoch,
        state,
        duration_s,
        settings,
        ephemeris,
        evaluation_times_s=evaluation,
        maneuvers=maneuvers,
    )
    states_by_offset = {
        float(offset): result.states[index]
        for index, offset in enumerate(result.elapsed_s)
    }
    samples = [
        (
            marker,
            state.copy() if offset == 0.0 else states_by_offset[float(offset)].copy(),
        )
        for marker, offset in relevant
    ]
    return result.endpoint, samples


def _minimum_lunar_surface_altitude_km(
    samples: Sequence[tuple[datetime, np.ndarray]],
    ephemeris: Any,
    mean_radius_km: float,
) -> float | None:
    if not samples:
        return None
    return min(
        float(np.linalg.norm(state[:3] - ephemeris.positions(epoch).moon_km))
        - mean_radius_km
        for epoch, state in samples
    )


def execute_candidate(
    epoch: datetime,
    true_state: np.ndarray,
    targeting: TargetingContext,
    plan: CandidatePlan,
    error: ExecutionError,
    sample: UncertaintySample,
    settings: ForceModelSettings,
    ephemeris: Any,
    vehicle: Vehicle,
    lunar_flyby_epoch: datetime,
    generation_config: Mapping[str, Any],
) -> ExecutionResult:
    actual_start = plan.planned_start_offset_s + 60.0 * (
        sample.communication_hold_min + sample.burn_delay_min
    )
    marker_epochs = _lunar_sample_epochs(lunar_flyby_epoch, generation_config)
    lunar_radius_km = float(
        generation_config["lunar_altitude_evaluation"]["mean_radius_km"]
    )
    if plan.index == 1 or np.linalg.norm(plan.planned_delta_v_m_s) == 0.0:
        try:
            endpoint, lunar_samples = _propagate_with_markers(
                epoch,
                true_state,
                targeting.duration_s,
                settings,
                ephemeris,
                marker_epochs,
            )
            lunar_altitude = _minimum_lunar_surface_altitude_km(
                lunar_samples, ephemeris, lunar_radius_km
            )
            return ExecutionResult(
                endpoint,
                np.zeros(3),
                0.0,
                actual_start,
                0.0,
                float(true_state[6]),
                0.0,
                lunar_altitude,
                False,
                None,
            )
        except Exception:
            return ExecutionResult(
                true_state.copy(),
                np.zeros(3),
                0.0,
                actual_start,
                0.0,
                float(true_state[6]),
                0.0,
                None,
                True,
                "propagation_failed",
            )
    if actual_start >= targeting.duration_s:
        endpoint, lunar_samples = _propagate_with_markers(
            epoch,
            true_state,
            targeting.duration_s,
            settings,
            ephemeris,
            marker_epochs,
        )
        lunar_altitude = _minimum_lunar_surface_altitude_km(
            lunar_samples, ephemeris, lunar_radius_km
        )
        return ExecutionResult(
            endpoint,
            np.zeros(3),
            0.0,
            actual_start,
            0.0,
            float(true_state[6]),
            0.0,
            lunar_altitude,
            False,
            "burn_after_target_epoch",
        )

    planned_magnitude = float(np.linalg.norm(plan.planned_delta_v_m_s))
    planned_direction = _unit_vector(plan.planned_delta_v_m_s)
    actual_direction = rotate_direction(planned_direction, error.pointing_bias_deg)
    scaled_vector = actual_direction * planned_magnitude * error.thrust_scale
    actual_vector = scaled_vector + error.additive_delta_v_m_s
    actual_direction = _unit_vector(actual_vector)
    actual_magnitude = float(np.linalg.norm(actual_vector))
    actual_thrust = plan.thrust_n * error.thrust_scale
    actual_duration = planned_burn_duration_s(
        float(true_state[6]),
        actual_magnitude,
        actual_thrust,
        vehicle.specific_impulse_s,
    )
    actual_duration = min(actual_duration, targeting.duration_s - actual_start)
    try:
        lunar_samples: list[tuple[datetime, np.ndarray]] = []
        if actual_start > 0.0:
            at_burn, before_samples = _propagate_with_markers(
                epoch,
                true_state,
                actual_start,
                settings,
                ephemeris,
                marker_epochs,
            )
            lunar_samples.extend(before_samples)
        else:
            at_burn = true_state.copy()
        if settings.fidelity == "F0":
            after_burn = apply_impulse(at_burn, actual_vector)
            propellant = rocket_propellant_kg(
                float(at_burn[6]), actual_magnitude, vehicle.specific_impulse_s
            )
            after_burn[6] = max(float(at_burn[6]) - propellant, 1.0)
            remaining = targeting.duration_s - actual_start
            endpoint, after_samples = _propagate_with_markers(
                epoch + timedelta(seconds=actual_start),
                after_burn,
                remaining,
                settings,
                ephemeris,
                marker_epochs,
            )
        else:
            maneuver = Maneuver(
                0.0,
                max(actual_duration, 1e-9),
                actual_thrust,
                vehicle.specific_impulse_s,
                tuple(actual_direction.tolist()),
            )
            remaining = targeting.duration_s - actual_start
            endpoint, after_samples = _propagate_with_markers(
                epoch + timedelta(seconds=actual_start),
                at_burn,
                remaining,
                settings,
                ephemeris,
                marker_epochs,
                maneuvers=(maneuver,),
            )
            propellant = max(float(at_burn[6]) - float(endpoint[6]), 0.0)
            if propellant > 0.0:
                actual_magnitude = (
                    vehicle.specific_impulse_s
                    * STANDARD_GRAVITY_M_S2
                    * math.log(float(at_burn[6]) / float(endpoint[6]))
                )
                actual_vector = actual_direction * actual_magnitude
        lunar_samples.extend(after_samples)
        lunar_altitude = _minimum_lunar_surface_altitude_km(
            lunar_samples, ephemeris, lunar_radius_km
        )
        return ExecutionResult(
            endpoint,
            actual_vector,
            propellant,
            actual_start,
            actual_duration,
            float(at_burn[6]),
            actual_thrust,
            lunar_altitude,
            False,
            None,
        )
    except Exception:
        return ExecutionResult(
            true_state.copy(),
            np.zeros(3),
            0.0,
            actual_start,
            0.0,
            float(true_state[6]),
            0.0,
            None,
            True,
            "propagation_failed",
        )


def execute_candidate_cached(
    cache: dict[tuple[float, ...], ExecutionResult],
    epoch: datetime,
    true_state: np.ndarray,
    targeting: TargetingContext,
    plan: CandidatePlan,
    error: ExecutionError,
    sample: UncertaintySample,
    settings: ForceModelSettings,
    ephemeris: Any,
    vehicle: Vehicle,
    lunar_flyby_epoch: datetime,
    generation_config: Mapping[str, Any],
) -> ExecutionResult:
    if float(np.linalg.norm(plan.planned_delta_v_m_s)) != 0.0:
        return execute_candidate(
            epoch,
            true_state,
            targeting,
            plan,
            error,
            sample,
            settings,
            ephemeris,
            vehicle,
            lunar_flyby_epoch,
            generation_config,
        )

    key = tuple(float(value) for value in true_state)
    if key not in cache:
        cache[key] = execute_candidate(
            epoch,
            true_state,
            targeting,
            plan,
            error,
            sample,
            settings,
            ephemeris,
            vehicle,
            lunar_flyby_epoch,
            generation_config,
        )
    actual_start = plan.planned_start_offset_s + 60.0 * (
        sample.communication_hold_min + sample.burn_delay_min
    )
    return replace(cache[key], actual_start_offset_s=actual_start)


def _flight_path_angle(position: np.ndarray, velocity: np.ndarray) -> float:
    denominator = float(np.linalg.norm(position) * np.linalg.norm(velocity))
    value = float(np.dot(position, velocity)) / denominator
    return math.degrees(math.asin(float(np.clip(value, -1.0, 1.0))))


def correlated_ellipse_utilization(
    first: float,
    second: float,
    first_limit: float,
    second_limit: float,
    correlation: float,
) -> float:
    x = first / first_limit
    y = second / second_limit
    numerator = x * x - 2.0 * correlation * x * y + y * y
    return math.sqrt(max(numerator / (1.0 - correlation * correlation), 0.0))


def terminal_components(
    target_state: np.ndarray, endpoint: np.ndarray
) -> dict[str, float]:
    target_position = target_state[:3]
    target_velocity = target_state[3:6]
    position_error = endpoint[:3] - target_position
    velocity_error = endpoint[3:6] - target_velocity
    radial = _unit_vector(target_position)
    normal_axis = _unit_vector(np.cross(target_position, target_velocity))
    along_track = _unit_vector(np.cross(normal_axis, radial))
    return {
        "position_norm_km": float(np.linalg.norm(position_error)),
        "downrange_position_km": float(np.dot(position_error, along_track)),
        "cross_track_position_km": float(np.dot(position_error, normal_axis)),
        "velocity_magnitude_error_m_s": (
            float(np.linalg.norm(endpoint[3:6]))
            - float(np.linalg.norm(target_velocity))
        )
        * 1000.0,
        "cross_track_velocity_m_s": float(np.dot(velocity_error, normal_axis)) * 1000.0,
        "flight_path_angle_error_deg": _flight_path_angle(endpoint[:3], endpoint[3:6])
        - _flight_path_angle(target_position, target_velocity),
    }


def crew_axis_acceleration_m_s2(
    thrust_n: float,
    mass_kg: float,
    generation_config: Mapping[str, Any],
) -> np.ndarray:
    mapping = generation_config["vehicle_and_burn"]["crew_axis_mapping"]
    if mapping != "positive_body_x_after_burn_attitude_alignment":
        raise ValueError(f"Unsupported crew-axis mapping: {mapping}")
    if thrust_n < 0.0 or mass_kg <= 0.0:
        raise ValueError("Thrust must be nonnegative and mass must be positive")
    return np.asarray([thrust_n / mass_kg, 0.0, 0.0])


def interval_overlaps_exclusion(
    start: datetime,
    duration_s: float,
    center: datetime,
    half_width_h: float,
) -> bool:
    stop = start + timedelta(seconds=duration_s)
    exclusion_start = center - timedelta(hours=half_width_h)
    exclusion_stop = center + timedelta(hours=half_width_h)
    return start < exclusion_stop and stop > exclusion_start


def assess_outcome(
    plan: CandidatePlan,
    execution: ExecutionResult,
    targeting: TargetingContext,
    robust_cost: float,
    constraints: Mapping[str, Any],
    generation_config: Mapping[str, Any],
    vehicle: Vehicle,
    epoch: datetime,
    lunar_flyby_epoch: datetime,
    settings: ForceModelSettings,
    crew_schedule_path: Path,
    acceleration_path: Path,
) -> Outcome:
    if execution.nonconverged:
        return Outcome(
            robust_total_correction_delta_v_m_s=round(robust_cost, 9),
            independently_propagated_feasible=False,
            correction_delta_v_m_s=0.0,
            burn_vector_x_m_s=0.0,
            burn_vector_y_m_s=0.0,
            burn_vector_z_m_s=0.0,
            terminal_position_error_km=9999.0,
            terminal_velocity_error_m_s=9999.0,
            terminal_margin=-1.0,
            propellant_used_kg=0.0,
            minimum_lunar_surface_altitude_km=None,
            nonconverged=True,
            violation_code=execution.execution_violation or "propagation_failed",
        )

    components = terminal_components(targeting.target_state, execution.endpoint)
    ellipse = constraints["hard_constraints"]["entry_interface_3sigma_ellipse"]
    utilizations: list[float] = []
    violations: list[str] = []
    values = {
        "downrange_position_km": components["downrange_position_km"],
        "cross_track_position_km": components["cross_track_position_km"],
        "velocity_magnitude_m_s": components["velocity_magnitude_error_m_s"],
        "cross_track_velocity_m_s": components["cross_track_velocity_m_s"],
        "flight_path_angle_deg": components["flight_path_angle_error_deg"],
    }
    for pair in ellipse["pairwise_limits"]:
        first_name, second_name = pair["variables"]
        first_limit, second_limit = pair["limits"]
        utilization = correlated_ellipse_utilization(
            values[first_name],
            values[second_name],
            float(first_limit),
            float(second_limit),
            float(pair["correlation"]),
        )
        utilizations.append(utilization)
        if utilization > 1.0:
            violations.append(f"entry_ellipse:{first_name}+{second_name}")

    delta_v_limit = float(
        constraints["hard_constraints"]["total_correction_delta_v"]["upper_bound_m_s"]
    )
    delta_v_utilization = robust_cost / delta_v_limit
    utilizations.append(delta_v_utilization)
    if delta_v_utilization > 1.0:
        violations.append("total_correction_delta_v")

    available_propellant = vehicle.usable_propellant_kg - vehicle.reserve_kg
    propellant_utilization = execution.propellant_used_kg / available_propellant
    utilizations.append(propellant_utilization)
    if propellant_utilization > 1.0:
        violations.append("propellant_reserve")

    lunar_altitude = execution.minimum_lunar_surface_altitude_km
    if lunar_altitude is not None:
        lunar_limit = float(
            constraints["hard_constraints"][
                "lunar_surface_altitude_including_dispersion"
            ]["lower_bound_km"]
        )
        utilizations.append(lunar_limit / max(lunar_altitude, 1e-9))
        if lunar_altitude < lunar_limit:
            violations.append("lunar_surface_altitude")

    if execution.execution_violation:
        violations.append(execution.execution_violation)
    if (
        plan.index != 1
        and execution.actual_start_offset_s + execution.actual_duration_s
        > targeting.duration_s - 3.0 * 3600.0
    ):
        violations.append("burn_timing")

    if plan.index != 1 and execution.actual_duration_s > 0.0:
        flyby_exclusion_h = float(
            constraints["hard_constraints"]["burn_timing"][
                "lunar_flyby_exclusion_before_after_h"
            ]
        )
        if interval_overlaps_exclusion(
            epoch + timedelta(seconds=execution.actual_start_offset_s),
            execution.actual_duration_s,
            lunar_flyby_epoch,
            flyby_exclusion_h,
        ):
            violations.append("lunar_flyby_exclusion")

    if plan.index != 1 and execution.actual_duration_s > 0.0:
        acceleration = crew_axis_acceleration_m_s2(
            execution.actual_thrust_n,
            execution.burn_mass_kg,
            generation_config,
        )
        crew = check_candidate_burn(
            epoch + timedelta(seconds=execution.actual_start_offset_s),
            execution.actual_duration_s,
            acceleration,
            crew_schedule_path,
            acceleration_path,
        )
        violations.extend(crew.violations)

    maximum_utilization = max(utilizations) if utilizations else 0.0
    if any(
        value.startswith("protected_")
        or value in {"burn_timing", "lunar_flyby_exclusion"}
        for value in violations
    ):
        maximum_utilization = max(maximum_utilization, 2.0)
    terminal_margin = 1.0 - maximum_utilization
    actual_vector = execution.actual_delta_v_m_s
    return Outcome(
        robust_total_correction_delta_v_m_s=round(robust_cost, 9),
        independently_propagated_feasible=not violations,
        correction_delta_v_m_s=round(float(np.linalg.norm(actual_vector)), 9),
        burn_vector_x_m_s=round(float(actual_vector[0]), 9),
        burn_vector_y_m_s=round(float(actual_vector[1]), 9),
        burn_vector_z_m_s=round(float(actual_vector[2]), 9),
        terminal_position_error_km=round(components["position_norm_km"], 9),
        terminal_velocity_error_m_s=round(
            abs(components["velocity_magnitude_error_m_s"]), 9
        ),
        terminal_margin=round(terminal_margin, 9),
        propellant_used_kg=round(execution.propellant_used_kg, 9),
        minimum_lunar_surface_altitude_km=(
            round(lunar_altitude, 9) if lunar_altitude is not None else None
        ),
        nonconverged=False,
        violation_code=";".join(sorted(set(violations))) or None,
    )


def physics_derived(
    position_km: np.ndarray, velocity_km_s: np.ndarray
) -> dict[str, float]:
    from .dynamics import EARTH_MU_KM3_S2

    radius = float(np.linalg.norm(position_km))
    speed = float(np.linalg.norm(velocity_km_s))
    return {
        "radius_km": radius,
        "speed_km_s": speed,
        "specific_orbital_energy_km2_s2": 0.5 * speed * speed
        - EARTH_MU_KM3_S2 / radius,
        "angular_momentum_km2_s": float(
            np.linalg.norm(np.cross(position_km, velocity_km_s))
        ),
        "radial_velocity_km_s": float(np.dot(position_km / radius, velocity_km_s)),
    }


def generate_group_records(
    manifest: Mapping[str, str],
    phase1_config: Mapping[str, Any],
    generation_config: Mapping[str, Any],
    uncertainty_config: Mapping[str, Any],
    constraints: Mapping[str, Any],
    oem: OemEphemeris,
    ephemeris: Any,
    tli_epoch: datetime,
    target_epoch: datetime,
    lunar_flyby_epoch: datetime,
    crew_schedule_path: Path,
    acceleration_path: Path,
) -> list[dict[str, Any]]:
    fidelity = manifest["fidelity"]
    group_id = manifest["group_id"]
    family = manifest["uncertainty_family"]
    epoch = parse_utc(manifest["mission_epoch_utc"])
    source_state = oem.interpolate(epoch)
    vehicle = vehicle_from_configs(constraints, generation_config)
    nominal_state = np.asarray(
        [*source_state.position_km, *source_state.velocity_km_s, vehicle.mass_kg],
        dtype=float,
    )
    settings = ForceModelSettings.for_fidelity(fidelity)
    targeting = build_targeting_context(
        epoch,
        nominal_state,
        target_epoch,
        tli_epoch,
        settings,
        ephemeris,
        generation_config,
    )
    set_count = int(manifest["decision_set_count"])
    master_seed = int(phase1_config["scenario_design"]["master_seed"])
    design_seed = derive_seed(
        master_seed, "scenario_generation_d003", fidelity, group_id
    )
    design = sobol_rows(set_count, design_seed)
    boundary_ids = set(
        boundary_case_ids(
            master_seed,
            fidelity,
            group_id,
            int(manifest["case_count"]),
            family,
        )
    )
    elapsed_since_tli_h = (epoch - tli_epoch).total_seconds() / 3600.0
    time_to_target_h = targeting.duration_s / 3600.0
    records: list[dict[str, Any]] = []
    no_burn_cache: dict[tuple[float, ...], ExecutionResult] = {}

    for set_index, sobol_row in enumerate(design, start=1):
        sample = sample_uncertainty(
            sobol_row,
            family,
            uncertainty_config,
            generation_config,
            targeting.duration_s,
        )
        true_position = nominal_state[:3] + sample.state_position_km
        true_velocity = (
            nominal_state[3:6]
            + (sample.state_velocity_m_s + sample.disturbance_velocity_m_s) / 1000.0
        )
        true_mass = vehicle.mass_kg * (1.0 + sample.mass_error_fraction)
        true_state = np.asarray([*true_position, *true_velocity, true_mass])
        estimated_position = true_position + sample.navigation_position_km
        estimated_velocity = true_velocity + sample.navigation_velocity_m_s / 1000.0
        estimated_perturbation = np.asarray(
            [
                *(estimated_position - nominal_state[:3]),
                *((estimated_velocity - nominal_state[3:6]) * 1000.0),
            ]
        )
        plans = build_candidate_plans(
            estimated_perturbation,
            sample,
            targeting,
            vehicle,
            generation_config,
        )
        miss = targeting.state_to_terminal_position @ estimated_perturbation
        set_id = f"{fidelity}-{group_id}-D{set_index:06d}"
        derived = physics_derived(estimated_position, estimated_velocity)

        for plan in plans:
            scenario_index = (set_index - 1) * len(plans) + plan.index
            scenario_id = f"{fidelity}-{group_id}-{scenario_index:06d}"
            error = execution_error(
                sample,
                family,
                plan.index,
                uncertainty_config,
                generation_config,
            )
            execution = execute_candidate_cached(
                no_burn_cache,
                epoch,
                true_state,
                targeting,
                plan,
                error,
                sample,
                settings,
                ephemeris,
                vehicle,
                lunar_flyby_epoch,
                generation_config,
            )
            robust_cost = robust_cost_m_s(
                plan.planned_delta_v_m_s,
                family,
                uncertainty_config,
                generation_config,
            )
            outcome = assess_outcome(
                plan,
                execution,
                targeting,
                robust_cost,
                constraints,
                generation_config,
                vehicle,
                epoch,
                lunar_flyby_epoch,
                settings,
                crew_schedule_path,
                acceleration_path,
            )
            if plan.index == 1:
                linear_terminal_error = float(np.linalg.norm(miss))
            else:
                matrix = targeting.burn_to_terminal_position[plan.index - 2]
                linear_terminal_error = float(
                    np.linalg.norm(miss + matrix @ plan.planned_delta_v_m_s)
                )
            inputs = {
                "elapsed_since_tli_h": elapsed_since_tli_h,
                "time_to_entry_interface_h": time_to_target_h,
                "initial_x_km": float(estimated_position[0]),
                "initial_y_km": float(estimated_position[1]),
                "initial_z_km": float(estimated_position[2]),
                "initial_vx_km_s": float(estimated_velocity[0]),
                "initial_vy_km_s": float(estimated_velocity[1]),
                "initial_vz_km_s": float(estimated_velocity[2]),
                "initial_mass_kg": true_mass,
                "usable_propellant_remaining_kg": vehicle.usable_propellant_kg,
                "navigation_dx_km": float(sample.navigation_position_km[0]),
                "navigation_dy_km": float(sample.navigation_position_km[1]),
                "navigation_dz_km": float(sample.navigation_position_km[2]),
                "navigation_dvx_m_s": float(sample.navigation_velocity_m_s[0]),
                "navigation_dvy_m_s": float(sample.navigation_velocity_m_s[1]),
                "navigation_dvz_m_s": float(sample.navigation_velocity_m_s[2]),
                "candidate_burn_start_offset_s": plan.planned_start_offset_s,
                "candidate_burn_duration_s": plan.planned_duration_s,
                "candidate_delta_v_x_m_s": float(plan.planned_delta_v_m_s[0]),
                "candidate_delta_v_y_m_s": float(plan.planned_delta_v_m_s[1]),
                "candidate_delta_v_z_m_s": float(plan.planned_delta_v_m_s[2]),
                "thrust_scale": error.thrust_scale,
                "pointing_bias_deg": error.pointing_bias_deg,
                "mass_error_fraction": sample.mass_error_fraction,
                "communication_hold_min": sample.communication_hold_min,
                "burn_delay_min": sample.burn_delay_min,
                "disturbance_scale": float(
                    np.linalg.norm(sample.disturbance_velocity_m_s)
                ),
                "low_fidelity_cost_m_s": float(
                    np.linalg.norm(plan.planned_delta_v_m_s)
                ),
                "low_fidelity_terminal_error_km": linear_terminal_error,
                **derived,
                "mission_phase": manifest["mission_phase"],
                "uncertainty_family": family,
                "navigation_mode": (
                    "dsn_estimated"
                    if family in {"U1", "U3", "U4", "U5"}
                    else "perfect_state"
                ),
                "thrust_class": plan.thrust_class,
                "fidelity": fidelity,
            }
            records.append(
                {
                    "scenario_id": scenario_id,
                    "decision_set_id": set_id,
                    "candidate_index": plan.index,
                    "group_id": group_id,
                    "base_trajectory": manifest["base_trajectory"],
                    "boundary_or_tail": scenario_id in boundary_ids,
                    "payload_version": generation_config["payload_version"],
                    "fidelity": fidelity,
                    "split": manifest["split"],
                    "inputs": inputs,
                    "outcomes": outcome.as_mapping(),
                }
            )
    return records
