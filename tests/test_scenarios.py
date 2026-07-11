from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from openqfuel.dynamics import ForceModelSettings
from openqfuel.gate4 import read_yaml
from openqfuel.scenarios import (
    CandidatePlan,
    TargetingContext,
    build_candidate_plans,
    cap_delta_v,
    correlated_ellipse_utilization,
    crew_axis_acceleration_m_s2,
    execute_candidate,
    execute_candidate_cached,
    execution_error,
    interval_overlaps_exclusion,
    planned_burn_duration_s,
    robust_cost_m_s,
    rocket_propellant_kg,
    rotate_direction,
    sample_uncertainty,
    sobol_rows,
    standard_variates,
    terminal_components,
    vehicle_from_configs,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATION = read_yaml(ROOT / "configs/scenario_generation.yaml")
UNCERTAINTY = read_yaml(ROOT / "configs/uncertainty_model.yaml")
CONSTRAINTS = read_yaml(ROOT / "configs/constraints.yaml")


def test_sobol_design_is_deterministic_and_bounded() -> None:
    first = sobol_rows(100, 17)
    second = sobol_rows(100, 17)
    np.testing.assert_array_equal(first, second)
    assert first.shape == (100, 52)
    assert np.all((first >= 0.0) & (first < 1.0))


def test_frozen_distribution_transforms_cover_nominal_bounded_and_tail() -> None:
    probabilities = np.linspace(0.001, 0.999, 100)
    gaussian = standard_variates(probabilities, "U1")
    bounded = standard_variates(probabilities, "U4")
    tail = standard_variates(probabilities, "U5")
    assert np.max(np.abs(bounded)) < 3.0
    assert np.max(np.abs(tail)) <= 6.0
    assert np.std(tail) > np.std(gaussian)


def test_uncertainty_families_apply_only_registered_components() -> None:
    row = sobol_rows(1, 29)[0]
    nominal = sample_uncertainty(row, "U0", UNCERTAINTY, GENERATION, 100000.0)
    np.testing.assert_array_equal(nominal.state_position_km, np.zeros(3))
    np.testing.assert_array_equal(nominal.navigation_position_km, np.zeros(3))
    np.testing.assert_array_equal(nominal.disturbance_velocity_m_s, np.zeros(3))
    assert nominal.communication_hold_min == 0.0
    assert nominal.burn_delay_min == 0.0
    assert nominal.mass_error_fraction == 0.0

    bounded = sample_uncertainty(row, "U4", UNCERTAINTY, GENERATION, 100000.0)
    assert np.max(np.abs(bounded.state_position_km)) <= 2.0
    assert np.max(np.abs(bounded.navigation_position_km)) <= 2.0
    assert bounded.communication_hold_min in {0.0, 15.0, 120.0}
    assert bounded.burn_delay_min in {0.0, 15.0, 60.0}
    assert bounded.mass_error_fraction in {0.0, -0.02, 0.02, -0.05, 0.05}


def test_execution_error_and_robust_cost_follow_frozen_family_roles() -> None:
    row = sobol_rows(1, 31)[0]
    sample = sample_uncertainty(row, "U3", UNCERTAINTY, GENERATION, 100000.0)
    error = execution_error(sample, "U3", 2, UNCERTAINTY, GENERATION)
    assert error.thrust_scale > 0.0
    assert np.all(np.isfinite(error.additive_delta_v_m_s))
    planned = np.array([1.0, 2.0, 0.5])
    assert robust_cost_m_s(planned, "U0", UNCERTAINTY, GENERATION) == np.linalg.norm(
        planned
    )
    assert robust_cost_m_s(planned, "U3", UNCERTAINTY, GENERATION) > np.linalg.norm(
        planned
    )


def test_vehicle_and_rocket_equation_are_source_driven() -> None:
    vehicle = vehicle_from_configs(CONSTRAINTS, GENERATION)
    assert (
        vehicle.mass_kg == CONSTRAINTS["vehicle_reference"]["post_tli_mass"]["value_kg"]
    )
    propellant = rocket_propellant_kg(vehicle.mass_kg, 5.0, vehicle.specific_impulse_s)
    duration = planned_burn_duration_s(
        vehicle.mass_kg,
        5.0,
        vehicle.main_thrust_n,
        vehicle.specific_impulse_s,
    )
    assert propellant > 0.0
    assert duration > 0.0


def test_rotation_cap_and_ellipse_helpers_are_well_behaved() -> None:
    direction = np.array([1.0, 0.0, 0.0])
    rotated = rotate_direction(direction, 0.1)
    assert np.isclose(np.linalg.norm(rotated), 1.0)
    assert not np.allclose(rotated, direction)
    capped = cap_delta_v(np.array([30.0, 0.0, 0.0]), 20.0)
    assert np.isclose(np.linalg.norm(capped), 20.0)
    assert correlated_ellipse_utilization(0.0, 0.0, 1.0, 1.0, 0.5) == 0.0


def test_crew_axis_mapping_and_lunar_exclusion_are_explicit() -> None:
    acceleration = crew_axis_acceleration_m_s2(1000.0, 25000.0, GENERATION)
    np.testing.assert_allclose(acceleration, [0.04, 0.0, 0.0])
    center = datetime(2026, 4, 6, 23, tzinfo=timezone.utc)
    assert interval_overlaps_exclusion(
        datetime(2026, 4, 6, 22, 30, tzinfo=timezone.utc),
        60.0,
        center,
        1.0,
    )
    assert not interval_overlaps_exclusion(
        datetime(2026, 4, 6, 20, tzinfo=timezone.utc),
        60.0,
        center,
        1.0,
    )


def test_linearized_candidate_builder_returns_five_capped_plans() -> None:
    vehicle = vehicle_from_configs(CONSTRAINTS, GENERATION)
    identity = np.eye(3)
    targeting = TargetingContext(
        target_epoch=datetime(2026, 4, 10, tzinfo=timezone.utc),
        duration_s=100000.0,
        target_state=np.zeros(7),
        state_to_terminal_position=np.column_stack((identity, np.zeros((3, 3)))),
        burn_offsets_s=(1000.0, 2000.0, 3000.0, 4000.0),
        burn_to_terminal_position=(identity, identity, identity, identity),
    )
    row = sobol_rows(1, 37)[0]
    sample = sample_uncertainty(row, "U1", UNCERTAINTY, GENERATION, 100000.0)
    plans = build_candidate_plans(
        np.array([30.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        sample,
        targeting,
        vehicle,
        GENERATION,
    )
    assert len(plans) == 5
    assert isinstance(plans[0], CandidatePlan)
    assert np.linalg.norm(plans[0].planned_delta_v_m_s) == 0.0
    assert all(np.linalg.norm(plan.planned_delta_v_m_s) <= 20.0 for plan in plans)


def test_terminal_components_are_zero_for_identical_states() -> None:
    state = np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 1.0, 25000.0])
    components = terminal_components(state, state.copy())
    assert all(abs(value) < 1e-12 for value in components.values())


def test_zero_burn_cache_reuses_propagation_but_retains_candidate_start() -> None:
    vehicle = vehicle_from_configs(CONSTRAINTS, GENERATION)
    epoch = datetime(2026, 4, 8, tzinfo=timezone.utc)
    state = np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 1.0, vehicle.mass_kg])
    targeting = TargetingContext(
        target_epoch=epoch + timedelta(seconds=60),
        duration_s=60.0,
        target_state=state.copy(),
        state_to_terminal_position=np.zeros((3, 6)),
        burn_offsets_s=(10.0, 20.0, 30.0, 40.0),
        burn_to_terminal_position=tuple(np.eye(3) for _ in range(4)),
    )
    sample = sample_uncertainty(
        sobol_rows(1, 41)[0], "U0", UNCERTAINTY, GENERATION, 60.0
    )
    error = execution_error(sample, "U0", 1, UNCERTAINTY, GENERATION)
    cache = {}
    first = execute_candidate_cached(
        cache,
        epoch,
        state,
        targeting,
        CandidatePlan(1, 0.0, np.zeros(3), 0.0, "RCS_LOW", vehicle.rcs_thrust_n),
        error,
        sample,
        ForceModelSettings.for_fidelity("F0"),
        None,
        vehicle,
        epoch + timedelta(days=1),
        GENERATION,
    )
    second_plan = CandidatePlan(
        2, 20.0, np.zeros(3), 0.0, "RCS_LOW", vehicle.rcs_thrust_n
    )
    second = execute_candidate_cached(
        cache,
        epoch,
        state,
        targeting,
        second_plan,
        error,
        sample,
        ForceModelSettings.for_fidelity("F0"),
        None,
        vehicle,
        epoch + timedelta(days=1),
        GENERATION,
    )
    uncached = execute_candidate(
        epoch,
        state,
        targeting,
        second_plan,
        error,
        sample,
        ForceModelSettings.for_fidelity("F0"),
        None,
        vehicle,
        epoch + timedelta(days=1),
        GENERATION,
    )
    assert len(cache) == 1
    np.testing.assert_array_equal(first.endpoint, second.endpoint)
    np.testing.assert_array_equal(second.endpoint, uncached.endpoint)
    np.testing.assert_array_equal(
        second.actual_delta_v_m_s, uncached.actual_delta_v_m_s
    )
    assert first.actual_start_offset_s == 0.0
    assert second.actual_start_offset_s == uncached.actual_start_offset_s == 20.0
    assert second.propellant_used_kg == uncached.propellant_used_kg
    assert second.minimum_lunar_surface_altitude_km == (
        uncached.minimum_lunar_surface_altitude_km
    )
    assert second.nonconverged == uncached.nonconverged
    assert second.execution_violation == uncached.execution_violation
