"""Post-Gate-5 exploratory protocol guards and compute admission helpers."""

from __future__ import annotations

import math
from typing import Any, Mapping

from .gate4 import FinalTestAccessError


LOCKED_DATA_SCOPES = {
    "calibration",
    "uncertainty_calibration",
    "final_test",
    "in_distribution_final_test",
    "out_of_distribution_final_test",
    "gate6",
}


def _post_gate5_block(config: Mapping[str, Any]) -> Mapping[str, Any]:
    if "post_gate5_exploratory_protocol" in config:
        block = config["post_gate5_exploratory_protocol"]
    else:
        block = config
    if not isinstance(block, Mapping):
        raise ValueError("Post-Gate-5 config block must be a mapping")
    return block


def assert_post_gate5_scope(
    config: Mapping[str, Any],
    *,
    action: str,
    data_scope: str,
) -> None:
    """Enforce the active post-Gate-5 data and action boundary."""

    block = _post_gate5_block(config)
    if data_scope in LOCKED_DATA_SCOPES:
        raise FinalTestAccessError(f"{data_scope} remains locked after D008")
    if data_scope != "synthetic":
        if not bool(block.get("research_data_fitting_authorized", False)):
            raise PermissionError(
                "D008 does not authorize research-data fitting or execution"
            )
        if action not in {"preflight", "research_fit"}:
            raise PermissionError(f"Unexpected post-Gate-5 action: {action}")
        return
    if action == "implementation" and bool(block.get("implementation_authorized")):
        return
    if action == "synthetic_validation" and bool(
        block.get("synthetic_validation_authorized")
    ):
        return
    if action == "compute_preflight" and bool(
        block.get("preflight_execution_authorized")
    ):
        return
    raise PermissionError(f"D008 does not authorize {action} on {data_scope} data")


def equivalent_preflight_work_units(config: Mapping[str, Any]) -> float:
    """Return D009's conservative campaign size in 1,024-row work units."""

    block = _post_gate5_block(config)
    projection = block["campaign_projection"]
    folds = int(projection["grouped_folds"])
    benchmark_rows = int(block["benchmark"]["training_rows"])
    if folds <= 0 or benchmark_rows <= 0:
        raise ValueError("Preflight folds and benchmark rows must be positive")

    tuning_units = 0.0
    for rung in projection["tuning_rungs"]:
        rows = int(rung["development_samples"])
        trials = int(rung["trials_retained"])
        if rows <= 0 or trials <= 0:
            raise ValueError("Preflight rung rows and trials must be positive")
        tuning_units += folds * trials * rows / benchmark_rows

    selected_units = (
        folds
        * int(projection["selected_configuration_seeds"])
        * float(projection["selected_exact_units_per_seed_fold"])
    )
    sensitivity_units = (
        folds
        * int(projection["selected_configuration_seeds"])
        * int(projection["report_only_sensitivity_conditions"])
        * float(projection["sensitivity_units_per_seed_fold"])
    )
    total = tuning_units + selected_units + sensitivity_units
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("Projected preflight work units must be finite and positive")
    return float(total)


def project_preflight_resources(
    config: Mapping[str, Any],
    *,
    benchmark_cpu_seconds: float,
    benchmark_wall_seconds: float,
    peak_rss_gib: float,
    free_disk_gib: float,
) -> dict[str, float]:
    """Scale one D009 benchmark by the frozen conservative campaign formula."""

    block = _post_gate5_block(config)
    projection = block["campaign_projection"]
    values = (
        benchmark_cpu_seconds,
        benchmark_wall_seconds,
        peak_rss_gib,
        free_disk_gib,
    )
    if any(not math.isfinite(float(value)) or float(value) < 0.0 for value in values):
        raise ValueError("Observed preflight resources must be finite and nonnegative")
    units = equivalent_preflight_work_units(block)
    margin = float(projection["projection_margin"])
    artifact_bytes_per_unit = int(projection["artifact_bytes_per_work_unit"])
    if margin < 1.0 or artifact_bytes_per_unit <= 0:
        raise ValueError("Preflight margin and artifact budget must be positive")

    artifact_gib = (
        units * margin * artifact_bytes_per_unit / float(1024**3)
    )
    return {
        "equivalent_1024_row_work_units": units,
        "projection_margin": margin,
        "projected_cpu_core_hours": (
            float(benchmark_cpu_seconds) * units * margin / 3600.0
        ),
        "projected_wall_clock_days": (
            float(benchmark_wall_seconds) * units * margin / 86400.0
        ),
        "projected_new_artifacts_gib": artifact_gib,
        "observed_peak_rss_gib": float(peak_rss_gib),
        "observed_free_disk_gib": float(free_disk_gib),
        "projected_free_disk_after_artifacts_gib": float(free_disk_gib)
        - artifact_gib,
    }


def evaluate_preflight_admission(
    config: Mapping[str, Any], projected: Mapping[str, float]
) -> dict[str, Any]:
    """Evaluate every D009 admission limit without changing the experiment."""

    block = _post_gate5_block(config)
    ceilings = block["ceilings"]
    checks = {
        "cpu_core_hours": {
            "observed": float(projected["projected_cpu_core_hours"]),
            "limit": float(ceilings["branch_cpu_core_hours"]),
            "comparison": "less_than_or_equal",
        },
        "wall_clock_days": {
            "observed": float(projected["projected_wall_clock_days"]),
            "limit": float(ceilings["branch_wall_clock_days"]),
            "comparison": "less_than_or_equal",
        },
        "new_artifacts_gib": {
            "observed": float(projected["projected_new_artifacts_gib"]),
            "limit": float(ceilings["branch_new_artifacts_gib"]),
            "comparison": "less_than_or_equal",
        },
        "peak_rss_gib": {
            "observed": float(projected["observed_peak_rss_gib"]),
            "limit": float(ceilings["max_total_project_working_set_gib"]),
            "comparison": "less_than_or_equal",
        },
        "free_disk_after_artifacts_gib": {
            "observed": float(
                projected["projected_free_disk_after_artifacts_gib"]
            ),
            "limit": float(ceilings["minimum_free_disk_gib"]),
            "comparison": "greater_than_or_equal",
        },
    }
    for name, check in checks.items():
        observed = check["observed"]
        limit = check["limit"]
        if not math.isfinite(observed) or not math.isfinite(limit):
            raise ValueError(f"Non-finite preflight admission value: {name}")
        if check["comparison"] == "less_than_or_equal":
            check["passed"] = observed <= limit
            check["utilization_fraction"] = observed / limit
        else:
            check["passed"] = observed >= limit
            check["utilization_fraction"] = (
                limit / observed if observed > 0.0 else math.inf
            )
    return {
        "status": "PASS" if all(check["passed"] for check in checks.values()) else "STOP",
        "checks": checks,
    }


def validate_future_research_discussion_row(
    row: Mapping[str, Any],
    required_fields: list[str],
) -> None:
    """Validate the D008 future-research firewall row shape and booleans."""

    missing = [field for field in required_fields if field not in row]
    if missing:
        raise ValueError(f"Future-research discussion row missing fields: {missing}")
    expected = {
        "new_protocol_required": True,
        "active_pipeline_change_authorized": False,
        "post_outcome_retry_authorized": False,
    }
    for field, expected_value in expected.items():
        actual = row[field]
        if isinstance(actual, str):
            actual = actual.strip().lower() == "true"
        if bool(actual) != expected_value:
            raise ValueError(f"{field} must be {expected_value}")
