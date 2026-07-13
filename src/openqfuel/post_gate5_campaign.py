"""D011 guards and scientific helpers for the P001 development campaign."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import yaml

from .gate4 import read_yaml
from .gate5 import (
    TargetStandardizer,
    audit_development_records,
    fold_manifest_rows,
    load_development_records,
    nested_training_indices,
    validate_development_output_path,
)
from .models import (
    build_classical_classifier,
    build_classical_regressor,
    build_qml_control_classifier,
    build_qml_control_regressor,
)
from .phase1_analysis import (
    development_target_scale,
    feasibility_constrained_regret,
    feasibility_metrics,
    regression_metrics,
)
from .post_gate5 import process_memory_observation
from .preprocessing import FrozenFeaturePreprocessor, QuantumFeatureProjector
from .qml import (
    NoiseSensitivity,
    deterministic_landmark_indices,
    median_projected_kernel_gamma,
    projected_quantum_features,
    projected_quantum_kernel_from_features,
    symmetrize_and_clip_psd,
)


D011_ACCEPTED_STATUS = (
    "accepted_conditional_fold_shape_preflight_and_development_campaign_authorized"
)
D011_C1_ACCEPTED_STATUS = "accepted_launcher_correction_and_one_preflight_attempt"
D011_C2_ACCEPTED_STATUS = "accepted_raw_blob_hash_correction_and_one_preflight"
TRACK_IDS = ("Q01b", "FQK")
RUNG_SAMPLES = (128, 256, 512, 1024)


class GovernedIneligibleFold(ValueError):
    """A preregistered scientific eligibility condition was not met."""


@dataclass(frozen=True)
class ProjectionSpec:
    projection_id: str
    qubits: int
    layers: int
    feature_scale: float
    entangle: bool
    gamma_multiplier: float
    alpha: float
    landmarks: int


@dataclass
class FoldContext:
    fold_id: str
    rung_samples: int
    train_indices: np.ndarray
    validation_indices: np.ndarray
    row_ids: list[str]
    x_train_full: np.ndarray
    x_validation_full: np.ndarray
    compressed_train: dict[int, np.ndarray]
    compressed_validation: dict[int, np.ndarray]
    y_train_standardized: np.ndarray
    y_validation: np.ndarray
    feasible_train: np.ndarray
    feasible_validation: np.ndarray
    decision_set_ids: list[str]
    baseline_train_standardized: np.ndarray
    baseline_validation_standardized: np.ndarray
    target_standardizer: TargetStandardizer
    development_scale: float


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


def clean_source_commit(root: Path) -> tuple[str, str]:
    """Require a clean main checkout and return its source identity."""

    status = str(_git(root, "status", "--porcelain")).strip()
    if status:
        raise PermissionError("D011 execution requires a clean Git worktree")
    branch = str(_git(root, "branch", "--show-current")).strip()
    if branch != "main":
        raise PermissionError("D011 execution is accepted only on main")
    return str(_git(root, "rev-parse", "HEAD")).strip(), branch


def git_blob_sha256(root: Path, commit: str, relative_path: str) -> str:
    blob = _git(root, "show", f"{commit}:{relative_path}", binary=True)
    if not isinstance(blob, bytes):
        raise TypeError("Git blob reader returned text unexpectedly")
    return hashlib.sha256(blob).hexdigest()


def committed_yaml(root: Path, commit: str, relative_path: str) -> dict[str, Any]:
    blob = _git(root, "show", f"{commit}:{relative_path}", binary=True)
    if not isinstance(blob, bytes):
        raise TypeError("Git blob reader returned text unexpectedly")
    payload = yaml.safe_load(blob.decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Committed YAML must be a mapping: {relative_path}")
    return payload


def _verify_dependency_blobs(
    root: Path, config: Mapping[str, Any], source_commit: str
) -> None:
    accepted = str(config["accepted_dependencies"]["accepted_result_commit"])
    dependency_names = (
        "d008_config",
        "d010_result",
        "trial_manifest",
        "fold_manifest",
        "model_registry",
    )
    for name in dependency_names:
        dependency = config["accepted_dependencies"][name]
        path = str(dependency["path"])
        expected = str(dependency["git_blob_sha256"])
        historical = git_blob_sha256(root, accepted, path)
        current = git_blob_sha256(root, source_commit, path)
        if historical != expected:
            raise PermissionError(f"D011 accepted dependency hash is invalid: {name}")
        if current != expected:
            raise PermissionError(f"D011 dependency changed after acceptance: {name}")

    result_path = str(config["accepted_dependencies"]["d010_result"]["path"])
    blob = _git(root, "show", f"{source_commit}:{result_path}", binary=True)
    if not isinstance(blob, bytes):
        raise TypeError("D010 result reader returned text unexpectedly")
    result = json.loads(blob.decode("utf-8"))
    if result.get("decision_id") != "D010" or result.get("status") != "PASS":
        raise PermissionError("D011 requires the accepted D010 PASS result")


def verify_d011_c1_launcher_correction(
    root: Path, source_commit: str
) -> dict[str, Any]:
    """Validate the prospective D011-C1 launcher-only correction authority."""

    relative = "configs/post_gate5_d011_c1_launcher_correction.yaml"
    config = committed_yaml(root, source_commit, relative)
    if (
        config.get("decision_id") != "D011-C1"
        or config.get("status") != D011_C1_ACCEPTED_STATUS
    ):
        raise PermissionError("The accepted D011-C1 correction is not active")
    authority = config["authority"]
    if (
        authority.get("corrected_decision") != "D011"
        or int(authority.get("authorized_preflight_attempts", -1)) != 1
        or bool(authority.get("research_data_fitting_authorized"))
    ):
        raise PermissionError("D011-C1 authority is not limited to one preflight")
    locks = config["locks"]
    for field in (
        "d011_scientific_design_unchanged",
        "d011_stop_evidence_immutable",
        "no_model_refit_authorized",
        "no_threshold_change_authorized",
        "no_seed_or_split_change_authorized",
    ):
        if not bool(locks.get(field)):
            raise PermissionError(f"D011-C1 lock is invalid: {field}")
    for field in (
        "development_rows_read",
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs_submitted",
        "gate6_runs",
    ):
        if int(locks.get(field, -1)) != 0:
            raise PermissionError(f"D011-C1 prohibited access is nonzero: {field}")

    dependencies = config["accepted_dependencies"]
    for name in ("d011_config", "d011_stop_evidence", "d011_launcher_script"):
        dependency = dependencies[name]
        path = str(dependency["path"])
        expected = str(dependency["git_blob_sha256"])
        historical = git_blob_sha256(root, str(dependency["source_commit"]), path)
        if historical != expected:
            raise PermissionError(f"D011-C1 dependency hash is invalid: {name}")
        if name != "d011_launcher_script":
            current = git_blob_sha256(root, source_commit, path)
            if current != expected:
                raise PermissionError(f"D011-C1 immutable dependency changed: {name}")

    correction = config["authorized_correction"]
    if correction.get("root_cause") != "direct_file_scripts_namespace_import":
        raise PermissionError("D011-C1 root cause is not the recorded launcher failure")
    if correction.get("scientific_workload_change_authorized") is not False:
        raise PermissionError("D011-C1 cannot change the scientific workload")
    return config


def verify_d011_c2_hash_correction(
    root: Path, source_commit: str
) -> dict[str, Any]:
    """Validate the prospective D011-C2 raw-blob hash correction authority."""

    relative = "configs/post_gate5_d011_c2_hash_correction.yaml"
    config = committed_yaml(root, source_commit, relative)
    if (
        config.get("decision_id") != "D011-C2"
        or config.get("status") != D011_C2_ACCEPTED_STATUS
    ):
        raise PermissionError("The accepted D011-C2 correction is not active")
    authority = config["authority"]
    if (
        authority.get("corrected_decision") != "D011-C1"
        or int(authority.get("authorized_preflight_attempts", -1)) != 1
        or bool(authority.get("research_data_fitting_authorized"))
        or bool(authority.get("campaign_execution_authorized"))
    ):
        raise PermissionError("D011-C2 authority is not limited to one preflight")
    locks = config["locks"]
    for field in (
        "d011_scientific_design_unchanged",
        "d011_c1_stop_evidence_immutable",
        "no_model_refit_authorized",
        "no_threshold_change_authorized",
        "no_seed_or_split_change_authorized",
    ):
        if not bool(locks.get(field)):
            raise PermissionError(f"D011-C2 lock is invalid: {field}")
    for field in (
        "development_rows_read",
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs_submitted",
        "gate6_runs",
    ):
        if int(locks.get(field, -1)) != 0:
            raise PermissionError(f"D011-C2 prohibited access is nonzero: {field}")

    dependencies = config["accepted_dependencies"]
    for name, dependency in dependencies.items():
        if not isinstance(dependency, Mapping) or "path" not in dependency:
            continue
        path = str(dependency["path"])
        expected = str(dependency["git_blob_sha256"])
        historical = git_blob_sha256(root, str(dependency["source_commit"]), path)
        if historical != expected:
            raise PermissionError(f"D011-C2 dependency hash is invalid: {name}")
        if bool(dependency.get("must_match_current", True)):
            current = git_blob_sha256(root, source_commit, path)
            if current != expected:
                raise PermissionError(f"D011-C2 immutable dependency changed: {name}")

    correction = config["authorized_correction"]
    if correction.get("root_cause") != "non_raw_git_blob_dependency_hashes":
        raise PermissionError("D011-C2 root cause is not the recorded hash failure")
    if correction.get("scientific_workload_change_authorized") is not False:
        raise PermissionError("D011-C2 cannot change the scientific workload")
    return config


def verify_d011_preflight_correction(
    root: Path, source_commit: str
) -> dict[str, Any]:
    """Return the active prospective correction for a stopped D011 preflight."""

    c1 = committed_yaml(
        root, source_commit, "configs/post_gate5_d011_c1_launcher_correction.yaml"
    )
    if c1.get("outcome", {}).get("current_status") == (
        "terminal_authority_hash_check_stop"
    ):
        return verify_d011_c2_hash_correction(root, source_commit)
    return verify_d011_c1_launcher_correction(root, source_commit)


def verify_d011_authority(
    root: Path,
    *,
    action: str,
    require_fold_shape_pass: bool,
) -> tuple[dict[str, Any], str, str]:
    """Validate D011 source, dependencies, locks, and conditional authority."""

    source_commit, branch = clean_source_commit(root)
    relative = "configs/post_gate5_development_execution.yaml"
    config = committed_yaml(root, source_commit, relative)
    if (
        config.get("decision_id") != "D011"
        or config.get("status") != D011_ACCEPTED_STATUS
    ):
        raise PermissionError("The accepted D011 decision is not active")
    _verify_dependency_blobs(root, config, source_commit)

    authority = config["authority"]
    if action == "fold_shape_preflight":
        if not bool(authority.get("fold_shape_preflight_authorized")):
            raise PermissionError("D011 fold-shape preflight is not authorized")
        if config.get("outcome", {}).get("current_status") == (
            "terminal_prelaunch_technical_stop"
        ):
            verify_d011_preflight_correction(root, source_commit)
    elif action == "development_campaign":
        if not bool(authority.get("campaign_execution_authorized")):
            raise PermissionError("D011 development campaign is not authorized")
        if not bool(authority.get("research_data_fitting_authorized")):
            raise PermissionError("D011 development fitting is not authorized")
    elif action == "reporting":
        if not bool(authority.get("reporting_authorized")):
            raise PermissionError("D011 reporting is not authorized")
    else:
        raise ValueError(f"Unexpected D011 action: {action}")

    locks = config["locks"]
    if locks.get("allowed_data_scope") != "development":
        raise PermissionError("D011 allows development data only")
    for field in ("calibration_rows_read", "final_test_rows_read"):
        if int(locks.get(field, -1)) != 0:
            raise PermissionError(f"D011 lock is invalid: {field}")
    for field in (
        "final_payload_access_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate6_authorized",
    ):
        if bool(locks.get(field)):
            raise PermissionError(f"D011 prohibited authority is enabled: {field}")

    if require_fold_shape_pass:
        result_path = root / str(config["fold_shape_correction"]["output"])
        if not result_path.is_file():
            raise PermissionError("D011 fold-shape preflight result is absent")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if (
            result.get("decision_id") != "D011"
            or result.get("status") != "PASS"
            or result.get("source_commit") != source_commit
            or result.get("development_rows_read") != 0
            or result.get("calibration_rows_read") != 0
            or result.get("final_test_rows_read") != 0
        ):
            raise PermissionError("D011 fold-shape preflight is not admissible")
    return config, source_commit, branch


def load_projection_specs(path: Path) -> list[ProjectionSpec]:
    """Load and validate the immutable paired projection manifest."""

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    specs: list[ProjectionSpec] = []
    for row in rows:
        if (
            row["track_ids"] != "Q01b;FQK"
            or row["execution_status"] != "frozen_not_run"
        ):
            raise ValueError("D011 trial manifest scope/status is invalid")
        specs.append(
            ProjectionSpec(
                projection_id=str(row["projection_id"]),
                qubits=int(row["qubits"]),
                layers=int(row["data_reupload_layers"]),
                feature_scale=float(row["feature_scale"]),
                entangle=str(row["entangle"]).lower() == "true",
                gamma_multiplier=float(row["gamma_multiplier"]),
                alpha=float(row["regularization_alpha"]),
                landmarks=int(row["nystrom_landmarks"]),
            )
        )
    if len(specs) != 30 or len({spec.projection_id for spec in specs}) != 30:
        raise ValueError("D011 requires exactly 30 unique projection IDs")
    return specs


def stable_seed(*parts: object) -> int:
    """Return the low unsigned 32 bits of the frozen D011 SHA-256 material."""

    material = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[-4:], "big")


def tuning_landmark_seed(projection_id: str, fold_id: str) -> int:
    return stable_seed("P001", "D011", projection_id, fold_id)


def control_seed(
    stage: str,
    rung: int,
    control_id: str,
    fold_id: str,
    seed_index: int,
) -> int:
    return stable_seed("P001", "D011", stage, rung, control_id, fold_id, seed_index)


def shot_seed(
    track_id: str,
    projection_id: str,
    fold_id: str,
    seed_index: int,
    condition: str,
    partition: str,
) -> int:
    return stable_seed(
        "P001",
        "D011",
        track_id,
        projection_id,
        fold_id,
        seed_index,
        condition,
        partition,
    )


def endpoint_rank_key(summary: Mapping[str, Any], track_id: str) -> tuple[Any, ...]:
    """Return the fully frozen D011 endpoint ordering."""

    if track_id == "Q01b":
        return (
            float(summary["pooled_oof_nrmse"]),
            float(summary["mean_regret_m_s"]),
            float(summary["regularized_condition_number"]),
            int(summary["qubits"]),
            int(summary["layers"]),
            str(summary["projection_id"]),
        )
    if track_id == "FQK":
        return (
            float(summary["pooled_oof_brier"]),
            -float(summary["recall_at_0_5"]),
            -float(summary["auroc"]),
            -float(summary["precision_at_0_5"]),
            float(summary["regularized_condition_number"]),
            int(summary["qubits"]),
            str(summary["projection_id"]),
        )
    raise ValueError(f"Unexpected D011 track: {track_id}")


def select_with_advancement_floor(
    summaries: Sequence[Mapping[str, Any]],
    *,
    track_id: str,
    retain: int,
) -> list[dict[str, Any]]:
    """Apply endpoint rank after the frozen qubit/entanglement diversity floor."""

    if retain <= 0:
        raise ValueError("D011 retain count must be positive")
    eligible = [dict(row) for row in summaries if bool(row.get("eligible", False))]
    ranked = sorted(eligible, key=lambda row: endpoint_rank_key(row, track_id))
    if len(ranked) <= retain:
        return ranked

    selected: list[dict[str, Any]] = []

    def add_best(candidates: Sequence[dict[str, Any]]) -> None:
        if len(selected) >= retain:
            return
        for candidate in candidates:
            if candidate not in selected:
                selected.append(candidate)
                return

    for qubits in (4, 6, 8):
        add_best([row for row in ranked if int(row["qubits"]) == qubits])
    for entangle in (False, True):
        if not any(bool(row["entangle"]) is entangle for row in selected):
            add_best([row for row in ranked if bool(row["entangle"]) is entangle])
    for row in ranked:
        add_best([row])
    return sorted(selected, key=lambda row: endpoint_rank_key(row, track_id))


def project_fold_shape_resources(
    config: Mapping[str, Any],
    *,
    benchmark_cpu_seconds: float,
    benchmark_wall_seconds: float,
    peak_rss_gib: float,
    free_disk_gib: float,
) -> dict[str, float]:
    """Project the D011 largest-fold bundle against unchanged laptop limits."""

    correction = config["fold_shape_correction"]
    units = int(correction["total_worst_fold_bundle_units"])
    margin = float(correction["projection_margin"])
    artifact_bytes = int(correction["artifact_bytes_per_unit"])
    values = (
        benchmark_cpu_seconds,
        benchmark_wall_seconds,
        peak_rss_gib,
        free_disk_gib,
    )
    if any(not math.isfinite(float(value)) or float(value) < 0.0 for value in values):
        raise ValueError("D011 resource observations must be finite and nonnegative")
    artifacts = units * margin * artifact_bytes / float(1024**3)
    return {
        "worst_fold_bundle_units": float(units),
        "projection_margin": margin,
        "projected_cpu_core_hours": benchmark_cpu_seconds * units * margin / 3600.0,
        "projected_wall_clock_days": benchmark_wall_seconds * units * margin / 86400.0,
        "projected_new_artifacts_gib": artifacts,
        "observed_peak_rss_gib": peak_rss_gib,
        "observed_free_disk_gib": free_disk_gib,
        "projected_free_disk_after_artifacts_gib": free_disk_gib - artifacts,
    }


def evaluate_fold_shape_admission(
    config: Mapping[str, Any], projected: Mapping[str, float]
) -> dict[str, Any]:
    correction = config["fold_shape_correction"]
    ceilings = correction["ceilings"]
    checks = {
        "cpu_core_hours": (
            float(projected["projected_cpu_core_hours"]),
            float(ceilings["cpu_core_hours"]),
            "maximum",
        ),
        "wall_clock_days": (
            float(projected["projected_wall_clock_days"]),
            float(ceilings["wall_clock_days"]),
            "maximum",
        ),
        "new_artifacts_gib": (
            float(projected["projected_new_artifacts_gib"]),
            float(ceilings["new_artifacts_gib"]),
            "maximum",
        ),
        "peak_working_set_gib": (
            float(projected["observed_peak_rss_gib"]),
            float(ceilings["peak_working_set_gib"]),
            "maximum",
        ),
        "free_disk_after_artifacts_gib": (
            float(projected["projected_free_disk_after_artifacts_gib"]),
            float(ceilings["minimum_free_disk_gib"]),
            "minimum",
        ),
    }
    rows: dict[str, dict[str, Any]] = {}
    for name, (observed, limit, kind) in checks.items():
        if not math.isfinite(observed) or not math.isfinite(limit) or limit <= 0.0:
            raise ValueError(f"D011 admission value is invalid: {name}")
        passed = observed <= limit if kind == "maximum" else observed >= limit
        pressure = observed / limit if kind == "maximum" else limit / observed
        rows[name] = {
            "observed": observed,
            "limit": limit,
            "comparison": "less_than_or_equal"
            if kind == "maximum"
            else "greater_than_or_equal",
            "passed": passed,
            "utilization_fraction": pressure,
        }
    return {
        "status": "PASS" if all(row["passed"] for row in rows.values()) else "STOP",
        "checks": rows,
    }


def sample_projected_expectations(
    exact: np.ndarray,
    *,
    shots: int,
    seed: int,
    attenuation: float = 1.0,
) -> np.ndarray:
    """Sample independent Pauli expectations under the frozen D011 rule."""

    values = np.asarray(exact, dtype=float)
    if values.ndim != 2 or values.shape[1] % 3 or not np.all(np.isfinite(values)):
        raise ValueError("D011 projected expectations must be finite N x 3q values")
    if shots <= 0 or not 0.0 <= attenuation <= 1.0:
        raise ValueError("D011 shot count or attenuation is invalid")
    probabilities = np.clip((1.0 + attenuation * values) / 2.0, 0.0, 1.0)
    counts = np.random.default_rng(seed).binomial(shots, probabilities)
    return 2.0 * counts / float(shots) - 1.0


def fixed_noise_attenuation(
    layers: int, entangle: bool, noise: NoiseSensitivity
) -> float:
    """Mirror the frozen Gate 4 observable attenuation for X/Y/Z sampling."""

    one_qubit = (1.0 - 4.0 * noise.one_qubit_depolarizing_probability / 3.0) ** (
        4 * layers
    )
    two_qubit_exponent = 2 * layers if entangle else 0
    two_qubit = (
        1.0 - 16.0 * noise.two_qubit_depolarizing_probability / 15.0
    ) ** two_qubit_exponent
    readout = 1.0 - 2.0 * noise.readout_bit_flip_probability
    return float(np.clip(one_qubit * two_qubit * readout, 0.0, 1.0))


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _atomic_npz(path: Path, values: Mapping[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **values)
    temporary.replace(path)


def _signature(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _read_checkpoint(path: Path, signature: str) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("task_signature") != signature:
        raise PermissionError(f"D011 checkpoint signature mismatch: {path}")
    if payload.get("status") not in {"complete", "complete_governed_ineligible"}:
        raise PermissionError(f"D011 checkpoint is not complete: {path}")
    return payload


def _model_registry(root: Path) -> dict[str, dict[str, Any]]:
    payload = read_yaml(root / "experiments/phase1_model_registry.yaml")
    rows = {str(row["trial_id"]): dict(row) for row in payload["models"]}
    required = {
        "C01-T18",
        "C02-T02",
        "C03-T13",
        "C04-T28",
        "C05-T12",
        "C05-T17",
        "C06-T17",
        "A01-T04",
    }
    if not required <= set(rows):
        raise ValueError("D011 model registry lacks a frozen control")
    return rows


def _target(
    records: Sequence[Mapping[str, Any]], indices: np.ndarray, name: str
) -> np.ndarray:
    return np.asarray(
        [float(records[index]["outcomes"][name]) for index in indices], dtype=float
    )


def _feasibility(
    records: Sequence[Mapping[str, Any]], indices: np.ndarray, name: str
) -> np.ndarray:
    return np.asarray(
        [int(records[index]["outcomes"][name]) for index in indices], dtype=int
    )


def _low_fidelity_cost(
    records: Sequence[Mapping[str, Any]], indices: np.ndarray
) -> np.ndarray:
    return np.asarray(
        [float(records[index]["inputs"]["low_fidelity_cost_m_s"]) for index in indices],
        dtype=float,
    )


def build_fold_context(
    records: Sequence[Mapping[str, Any]],
    manifest: Sequence[Mapping[str, str]],
    phase_config: Mapping[str, Any],
    *,
    fold_id: str,
    rung_samples: int,
    qubit_dimensions: Sequence[int],
) -> FoldContext:
    """Fit all D011 transforms within one training fold/rung only."""

    if rung_samples not in RUNG_SAMPLES:
        raise ValueError("D011 rung is not frozen")
    if not set(qubit_dimensions).issubset({4, 6, 8}):
        raise ValueError("D011 qubit dimension is not authorized")
    fold_rows = fold_manifest_rows(phase_config, manifest)
    fold_by_group = {str(row["group_id"]): str(row["fold_id"]) for row in fold_rows}
    validation_indices = np.asarray(
        [
            index
            for index, record in enumerate(records)
            if fold_by_group[str(record["group_id"])] == fold_id
        ],
        dtype=int,
    )
    eligible_train = np.asarray(
        [
            index
            for index, record in enumerate(records)
            if fold_by_group[str(record["group_id"])] != fold_id
        ],
        dtype=int,
    )
    train_indices = nested_training_indices(
        records,
        eligible_train,
        rung_samples,
        int(phase_config["scenario_design"]["master_seed"]),
    )
    train_records = [records[index] for index in train_indices]
    validation_records = [records[index] for index in validation_indices]
    numeric = [
        *phase_config["features"]["numeric"],
        *phase_config["features"]["physics_derived"],
    ]
    categorical = phase_config["features"]["categorical"]
    preprocessor = FrozenFeaturePreprocessor(numeric, categorical)
    x_train_full = preprocessor.fit_transform(train_records, "development")
    x_validation_full = preprocessor.transform(validation_records, "development")
    compressed_train: dict[int, np.ndarray] = {}
    compressed_validation: dict[int, np.ndarray] = {}
    for qubits in sorted(set(qubit_dimensions)):
        projector = QuantumFeatureProjector(qubits)
        compressed_train[qubits] = projector.fit_transform(x_train_full, "development")
        compressed_validation[qubits] = projector.transform(
            x_validation_full, "development"
        )

    primary_target = str(phase_config["targets"]["primary_regression"])
    feasibility_target = str(phase_config["targets"]["feasibility"])
    y_train_raw = _target(records, train_indices, primary_target)
    y_validation = _target(records, validation_indices, primary_target)
    standardizer = TargetStandardizer.fit(y_train_raw)
    all_targets = _target(records, np.arange(len(records), dtype=int), primary_target)
    return FoldContext(
        fold_id=fold_id,
        rung_samples=rung_samples,
        train_indices=train_indices,
        validation_indices=validation_indices,
        row_ids=[str(records[index]["scenario_id"]) for index in train_indices],
        x_train_full=x_train_full,
        x_validation_full=x_validation_full,
        compressed_train=compressed_train,
        compressed_validation=compressed_validation,
        y_train_standardized=standardizer.transform(y_train_raw),
        y_validation=y_validation,
        feasible_train=_feasibility(records, train_indices, feasibility_target),
        feasible_validation=_feasibility(
            records, validation_indices, feasibility_target
        ),
        decision_set_ids=[
            str(records[index]["decision_set_id"]) for index in validation_indices
        ],
        baseline_train_standardized=standardizer.transform(
            _low_fidelity_cost(records, train_indices)
        ),
        baseline_validation_standardized=standardizer.transform(
            _low_fidelity_cost(records, validation_indices)
        ),
        target_standardizer=standardizer,
        development_scale=development_target_scale(all_targets),
    )


def _validate_prediction(values: np.ndarray, rows: int, label: str) -> np.ndarray:
    prediction = np.asarray(values, dtype=float)
    if prediction.shape != (rows,) or not np.all(np.isfinite(prediction)):
        raise ValueError(f"D011 prediction is invalid: {label}")
    return prediction


def _cost_metrics(
    context: FoldContext,
    predicted_cost: np.ndarray,
    predicted_probability: np.ndarray,
) -> dict[str, Any]:
    prediction = _validate_prediction(
        predicted_cost, context.validation_indices.size, "cost"
    )
    probability = np.clip(
        _validate_prediction(
            predicted_probability,
            context.validation_indices.size,
            "feasibility probability",
        ),
        0.0,
        1.0,
    )
    regression = regression_metrics(
        context.y_validation, prediction, context.development_scale
    )
    regret = feasibility_constrained_regret(
        context.decision_set_ids,
        prediction,
        probability,
        context.y_validation,
        context.feasible_validation,
        feasibility_threshold=0.5,
        infeasible_penalty_m_s=20.0,
    )
    errors = prediction - context.y_validation
    return {
        "validation_rows": int(errors.size),
        "development_scale": context.development_scale,
        "squared_error_sum": float(np.sum(errors * errors)),
        "absolute_error_sum": float(np.sum(np.abs(errors))),
        "rmse": regression.rmse,
        "nrmse": regression.nrmse,
        "mae": regression.mae,
        "decision_sets": regret.decision_sets,
        "regret_sum_m_s": regret.mean_regret_m_s * regret.decision_sets,
        "mean_regret_m_s": regret.mean_regret_m_s,
        "infeasible_selection_rate": regret.independently_infeasible_selection_rate,
        "no_predicted_feasible_rate": regret.no_predicted_feasible_rate,
        "no_reference_feasible_rate": regret.no_reference_feasible_rate,
    }


def _feasibility_metrics(
    context: FoldContext, predicted_probability: np.ndarray
) -> dict[str, Any]:
    probability = np.clip(
        _validate_prediction(
            predicted_probability,
            context.validation_indices.size,
            "feasibility probability",
        ),
        0.0,
        1.0,
    )
    try:
        metrics = feasibility_metrics(
            context.feasible_validation,
            probability,
            threshold=0.5,
            calibration_bins=10,
        )
    except ValueError as error:
        if str(error) == "AUROC requires both feasibility classes":
            raise GovernedIneligibleFold(
                "validation fold does not contain both feasibility classes"
            ) from error
        raise
    errors = probability - context.feasible_validation
    predicted = probability >= 0.5
    labels = context.feasible_validation == 1
    return {
        **asdict(metrics),
        "squared_error_sum": float(np.sum(errors * errors)),
        "true_positive": int(np.sum(predicted & labels)),
        "false_positive": int(np.sum(predicted & ~labels)),
        "true_negative": int(np.sum(~predicted & ~labels)),
        "false_negative": int(np.sum(~predicted & labels)),
    }


def _control_models(
    registry_row: Mapping[str, Any], seed: int, *, classifier: bool
) -> Any:
    family = str(registry_row["model_family"])
    parameters = registry_row["parameters"]
    if family == "random_fourier_ridge":
        builder = (
            build_qml_control_classifier if classifier else build_qml_control_regressor
        )
    else:
        builder = (
            build_classical_classifier if classifier else build_classical_regressor
        )
    if not classifier and family == "physics_residual":
        return builder(family, parameters, seed, low_fidelity_column=-1)
    return builder(family, parameters, seed)


def execute_control_fold(
    root: Path,
    output_dir: Path,
    context: FoldContext,
    *,
    source_commit: str,
    stage: str,
    seed_index: int,
    qubit_dimensions: Sequence[int],
    active_tracks: Sequence[str],
) -> dict[str, Any]:
    """Fit each reusable D008 control once for an identical fold context."""

    tracks = tuple(sorted(set(str(value) for value in active_tracks)))
    if not tracks or not set(tracks).issubset(TRACK_IDS):
        raise ValueError("D011 control fold has an invalid active track set")
    identity = {
        "source_commit": source_commit,
        "stage": stage,
        "rung_samples": context.rung_samples,
        "fold_id": context.fold_id,
        "seed_index": seed_index,
        "qubit_dimensions": sorted(set(int(value) for value in qubit_dimensions)),
        "active_tracks": tracks,
    }
    signature = _signature(identity)
    summary_path = output_dir / "controls.json"
    prediction_path = output_dir / "controls.npz"
    cached = _read_checkpoint(summary_path, signature)
    if cached is not None:
        if not prediction_path.is_file():
            raise PermissionError("D011 control prediction checkpoint is absent")
        return cached

    registry = _model_registry(root)
    probabilities: dict[str, np.ndarray] = {}
    costs: dict[str, np.ndarray] = {}
    metrics: dict[str, Any] = {}
    metric_status: dict[str, dict[str, Any]] = {}
    started = time.perf_counter()

    if set(np.unique(context.feasible_train)) != {0, 1}:
        _atomic_npz(
            prediction_path,
            {"validation_indices": context.validation_indices},
        )
        payload = {
            "schema_version": "0.1.0",
            "status": "complete_governed_ineligible",
            "task_signature": signature,
            **identity,
            "metrics": {},
            "metric_status": {
                track: {
                    "eligible": False,
                    "reason_code": "training_fold_single_feasibility_class",
                }
                for track in tracks
            },
            "wall_time_s": time.perf_counter() - started,
            "source_split": "development",
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
        }
        _atomic_json(summary_path, payload)
        return payload

    def record_fqk_metric(label: str, probability: np.ndarray) -> None:
        key = f"{label}_FQK"
        try:
            metrics[key] = _feasibility_metrics(context, probability)
            metric_status[key] = {"eligible": True, "reason_code": None}
        except GovernedIneligibleFold as error:
            metric_status[key] = {
                "eligible": False,
                "reason_code": "metric_undefined",
                "reason": str(error),
            }

    c06 = registry["C06-T17"]
    c06_seed = control_seed(
        stage,
        context.rung_samples,
        "C06-T17",
        context.fold_id,
        seed_index,
    )
    c06_classifier = _control_models(c06, c06_seed, classifier=True)
    c06_classifier.fit(context.x_train_full, context.feasible_train)
    probabilities["C06-T17"] = c06_classifier.predict_proba(context.x_validation_full)[
        :, 1
    ]
    if "Q01b" in tracks:
        c06_cost_model = _control_models(c06, c06_seed, classifier=False)
        c06_train = np.column_stack(
            (context.x_train_full, context.baseline_train_standardized)
        )
        c06_validation = np.column_stack(
            (context.x_validation_full, context.baseline_validation_standardized)
        )
        c06_cost_model.fit(c06_train, context.y_train_standardized)
        costs["C06-T17"] = context.target_standardizer.inverse(
            c06_cost_model.predict(c06_validation)
        )
        metrics["C06-T17_Q01b"] = _cost_metrics(
            context, costs["C06-T17"], probabilities["C06-T17"]
        )
        metric_status["C06-T17_Q01b"] = {
            "eligible": True,
            "reason_code": None,
        }
    if "FQK" in tracks:
        record_fqk_metric("C06-T17", probabilities["C06-T17"])

    if "FQK" in tracks:
        for trial_id in (
            "C01-T18",
            "C02-T02",
            "C03-T13",
            "C04-T28",
            "C05-T12",
        ):
            row = registry[trial_id]
            seed = control_seed(
                stage,
                context.rung_samples,
                trial_id,
                context.fold_id,
                seed_index,
            )
            model = _control_models(row, seed, classifier=True)
            model.fit(context.x_train_full, context.feasible_train)
            probabilities[trial_id] = model.predict_proba(context.x_validation_full)[
                :, 1
            ]
            record_fqk_metric(trial_id, probabilities[trial_id])

    for qubits in sorted(set(int(value) for value in qubit_dimensions)):
        for trial_id in ("A01-T04", "C05-T17"):
            row = registry[trial_id]
            label = f"{trial_id}-q{qubits}"
            seed = control_seed(
                stage,
                context.rung_samples,
                label,
                context.fold_id,
                seed_index,
            )
            classifier = _control_models(row, seed, classifier=True)
            classifier.fit(context.compressed_train[qubits], context.feasible_train)
            probabilities[label] = classifier.predict_proba(
                context.compressed_validation[qubits]
            )[:, 1]
            if "Q01b" in tracks:
                cost_model = _control_models(row, seed, classifier=False)
                cost_model.fit(
                    context.compressed_train[qubits],
                    context.y_train_standardized,
                )
                costs[label] = context.target_standardizer.inverse(
                    cost_model.predict(context.compressed_validation[qubits])
                )
                metrics[f"{label}_Q01b"] = _cost_metrics(
                    context, costs[label], probabilities[label]
                )
                metric_status[f"{label}_Q01b"] = {
                    "eligible": True,
                    "reason_code": None,
                }
            if "FQK" in tracks:
                record_fqk_metric(label, probabilities[label])

    arrays = {
        "validation_indices": context.validation_indices,
        **{f"cost__{key}": value for key, value in costs.items()},
        **{f"probability__{key}": value for key, value in probabilities.items()},
    }
    _atomic_npz(prediction_path, arrays)
    payload = {
        "schema_version": "0.1.0",
        "status": "complete",
        "task_signature": signature,
        **identity,
        "metrics": metrics,
        "metric_status": metric_status,
        "wall_time_s": time.perf_counter() - started,
        "source_split": "development",
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    _atomic_json(summary_path, payload)
    return payload


def _squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    distances = (
        np.sum(left * left, axis=1)[:, None]
        + np.sum(right * right, axis=1)[None, :]
        - 2.0 * (left @ right.T)
    )
    return np.maximum(distances, 0.0)


def _centered_alignment(kernel: np.ndarray, targets: np.ndarray) -> float:
    centered_features = targets - np.mean(targets)
    target_kernel = np.outer(centered_features, centered_features)
    row_mean = np.mean(kernel, axis=1, keepdims=True)
    centered_kernel = kernel - row_mean - row_mean.T + float(np.mean(kernel))
    denominator = np.linalg.norm(centered_kernel) * np.linalg.norm(target_kernel)
    if denominator <= 0.0:
        raise GovernedIneligibleFold("kernel-target alignment denominator is zero")
    return float(np.sum(centered_kernel * target_kernel) / denominator)


def _nystrom_embedding(
    training: np.ndarray,
    validation: np.ndarray,
    context: FoldContext,
    spec: ProjectionSpec,
    *,
    seed_value: int,
    projected_quantum: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    landmark_count = min(spec.landmarks, training.shape[0])
    landmark_indices = deterministic_landmark_indices(
        context.row_ids,
        spec.projection_id,
        context.fold_id,
        seed_value,
        landmark_count,
    )
    landmarks = training[landmark_indices]
    if projected_quantum:
        try:
            gamma = median_projected_kernel_gamma(training, spec.gamma_multiplier)
        except ValueError as error:
            if str(error) == "Projected-kernel median distance is zero":
                raise GovernedIneligibleFold(
                    "projected-kernel training-fold median distance is zero"
                ) from error
            raise

        def kernel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
            return projected_quantum_kernel_from_features(left, right, gamma)

    else:
        distances = _squared_distances(training, training)
        positive = distances[distances > 0.0]
        if positive.size == 0:
            raise GovernedIneligibleFold("A02 training-fold median distance is zero")
        gamma = spec.gamma_multiplier / float(np.median(positive))

        def kernel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
            return np.exp(-gamma * _squared_distances(left, right))

    landmark_kernel = kernel(landmarks, landmarks)
    clipped, clip_info = symmetrize_and_clip_psd(landmark_kernel)
    eigenvalues, eigenvectors = np.linalg.eigh(clipped)
    inverse_root = (eigenvectors * (1.0 / np.sqrt(eigenvalues))) @ eigenvectors.T
    training_embedding = kernel(training, landmarks) @ inverse_root
    validation_embedding = kernel(validation, landmarks) @ inverse_root
    approximate_kernel = training_embedding @ training_embedding.T
    off_diagonal = approximate_kernel[~np.eye(training.shape[0], dtype=bool)]
    centered_embedding = training_embedding - np.mean(
        training_embedding, axis=0, keepdims=True
    )
    singular_values = np.linalg.svd(centered_embedding, compute_uv=False)
    spectrum = singular_values * singular_values
    positive_spectrum = spectrum[spectrum > 0.0]
    probabilities = positive_spectrum / np.sum(positive_spectrum)
    effective_rank = float(np.exp(-np.sum(probabilities * np.log(probabilities))))
    regularized = training_embedding.T @ training_embedding + spec.alpha * np.eye(
        training_embedding.shape[1]
    )
    alignments: dict[str, float | None] = {}
    alignment_errors: dict[str, str] = {}
    for track_id, target in (
        ("q01b", context.y_train_standardized),
        ("fqk", context.feasible_train.astype(float)),
    ):
        try:
            alignments[track_id] = _centered_alignment(approximate_kernel, target)
        except GovernedIneligibleFold as error:
            alignments[track_id] = None
            alignment_errors[track_id] = str(error)
    diagnostics = {
        "gamma": gamma,
        "landmarks": landmark_count,
        "clipped_eigenvalues": clip_info.clipped_eigenvalues,
        "minimum_eigenvalue_before_clip": clip_info.min_eigenvalue_before_clip,
        "maximum_negative_eigenvalue": clip_info.max_negative_eigenvalue,
        "off_diagonal_mean": float(np.mean(off_diagonal)),
        "off_diagonal_std": float(np.std(off_diagonal, ddof=0)),
        "off_diagonal_q05": float(np.quantile(off_diagonal, 0.05)),
        "off_diagonal_q95": float(np.quantile(off_diagonal, 0.95)),
        "effective_rank": effective_rank,
        "regularized_condition_number": float(np.linalg.cond(regularized)),
        "kernel_target_alignment_q01b": alignments["q01b"],
        "kernel_target_alignment_fqk": alignments["fqk"],
        "alignment_errors": alignment_errors,
    }
    return training_embedding, validation_embedding, diagnostics


def _two_head_predictions(
    training: np.ndarray,
    validation: np.ndarray,
    context: FoldContext,
    alpha: float,
    *,
    include_cost: bool,
) -> tuple[np.ndarray | None, np.ndarray]:
    targets = (
        np.column_stack(
            (context.y_train_standardized, context.feasible_train.astype(float))
        )
        if include_cost
        else context.feasible_train.astype(float)[:, None]
    )
    system = training.T @ training + alpha * np.eye(training.shape[1])
    coefficients = np.linalg.solve(system, training.T @ targets)
    predictions = validation @ coefficients
    if not np.all(np.isfinite(predictions)):
        raise ValueError("D011 projected head returned non-finite predictions")
    if include_cost:
        cost = context.target_standardizer.inverse(predictions[:, 0])
        probability = np.clip(predictions[:, 1], 0.0, 1.0)
        return cost, probability
    return None, np.clip(predictions[:, 0], 0.0, 1.0)


def _conditioned_projected_features(
    values: np.ndarray,
    spec: ProjectionSpec,
    config: Mapping[str, Any],
    *,
    track_id: str,
    fold_id: str,
    seed_index: int,
    condition: str,
    partition: str,
    exact_cache: dict[tuple[Any, ...], np.ndarray] | None = None,
) -> np.ndarray:
    cache_key = (
        fold_id,
        spec.qubits,
        spec.layers,
        spec.feature_scale,
        spec.entangle,
        partition,
    )
    exact = None if exact_cache is None else exact_cache.get(cache_key)
    if exact is None:
        exact = projected_quantum_features(
            values,
            spec.qubits,
            spec.layers,
            feature_scale=spec.feature_scale,
            entangle=spec.entangle,
        )
        if exact_cache is not None:
            exact_cache[cache_key] = exact
    if condition == "exact_statevector":
        return exact
    seed = shot_seed(
        track_id,
        spec.projection_id,
        fold_id,
        seed_index,
        condition,
        partition,
    )
    if condition == "1024_shots":
        return sample_projected_expectations(exact, shots=1024, seed=seed)
    if condition == "4096_shots":
        return sample_projected_expectations(exact, shots=4096, seed=seed)
    if condition == "fixed_gate4_noise_model":
        sensitivity = config["sensitivities"]
        noise = NoiseSensitivity.from_mapping(sensitivity["fixed_noise_model"])
        attenuation = fixed_noise_attenuation(spec.layers, spec.entangle, noise)
        return sample_projected_expectations(
            exact,
            shots=int(sensitivity["fixed_noise_shots"]),
            seed=seed,
            attenuation=attenuation,
        )
    raise ValueError(f"Unexpected D011 sensitivity condition: {condition}")


def execute_projection_fold(
    output_dir: Path,
    context: FoldContext,
    spec: ProjectionSpec,
    config: Mapping[str, Any],
    *,
    source_commit: str,
    stage: str,
    seed_index: int,
    active_tracks: Sequence[str],
    condition: str = "exact_statevector",
    state_cache: dict[tuple[Any, ...], tuple[np.ndarray, np.ndarray]] | None = None,
    exact_state_cache: dict[tuple[Any, ...], np.ndarray] | None = None,
) -> dict[str, Any]:
    """Execute one shared projected-state fold under endpoint-specific authority."""

    tracks = tuple(sorted(set(str(value) for value in active_tracks)))
    if not tracks or not set(tracks).issubset(TRACK_IDS):
        raise ValueError("D011 projection fold has an invalid active track set")
    if condition != "exact_statevector" and stage != "sensitivity":
        raise PermissionError("D011 finite-shot/noise work is report-only sensitivity")
    identity = {
        "source_commit": source_commit,
        "stage": stage,
        "rung_samples": context.rung_samples,
        "fold_id": context.fold_id,
        "projection": asdict(spec),
        "seed_index": seed_index,
        "active_tracks": tracks,
        "condition": condition,
    }
    signature = _signature(identity)
    summary_path = output_dir / f"{spec.projection_id}.json"
    prediction_path = output_dir / f"{spec.projection_id}.npz"
    cached = _read_checkpoint(summary_path, signature)
    if cached is not None:
        if not prediction_path.is_file():
            raise PermissionError("D011 projection prediction checkpoint is absent")
        return cached

    started = time.perf_counter()
    seed_value = (
        tuning_landmark_seed(spec.projection_id, context.fold_id)
        if stage == "tuning"
        else seed_index
    )
    sensitivity_track = tracks[0] if stage == "sensitivity" else "shared"
    track_eligibility = {
        track: {"eligible": True, "reason_code": None, "reason": None}
        for track in tracks
    }
    metrics: dict[str, Any] = {}
    arrays: dict[str, np.ndarray] = {
        "validation_indices": context.validation_indices,
    }
    q_diagnostics: dict[str, Any] | None = None
    q_cost: np.ndarray | None = None
    q_probability: np.ndarray | None = None

    if set(np.unique(context.feasible_train)) != {0, 1}:
        for track in tracks:
            track_eligibility[track] = {
                "eligible": False,
                "reason_code": "training_fold_single_feasibility_class",
                "reason": "training fold does not contain both feasibility classes",
            }
    else:
        state_key = (
            context.fold_id,
            context.rung_samples,
            spec.qubits,
            spec.layers,
            spec.feature_scale,
            spec.entangle,
            condition,
            None if condition == "exact_statevector" else spec.projection_id,
            None if condition == "exact_statevector" else sensitivity_track,
            None if condition == "exact_statevector" else seed_index,
        )
        cached_states = None if state_cache is None else state_cache.get(state_key)
        if cached_states is None:
            projected_train = _conditioned_projected_features(
                context.compressed_train[spec.qubits],
                spec,
                config,
                track_id=sensitivity_track,
                fold_id=context.fold_id,
                seed_index=seed_index,
                condition=condition,
                partition="training",
                exact_cache=exact_state_cache,
            )
            projected_validation = _conditioned_projected_features(
                context.compressed_validation[spec.qubits],
                spec,
                config,
                track_id=sensitivity_track,
                fold_id=context.fold_id,
                seed_index=seed_index,
                condition=condition,
                partition="validation",
                exact_cache=exact_state_cache,
            )
            if state_cache is not None:
                state_cache[state_key] = (
                    projected_train,
                    projected_validation,
                )
        else:
            projected_train, projected_validation = cached_states
        try:
            q_train, q_validation, q_diagnostics = _nystrom_embedding(
                projected_train,
                projected_validation,
                context,
                spec,
                seed_value=seed_value,
                projected_quantum=True,
            )
        except GovernedIneligibleFold as error:
            for track in tracks:
                track_eligibility[track] = {
                    "eligible": False,
                    "reason_code": "projected_kernel_geometry_undefined",
                    "reason": str(error),
                }
        else:
            include_cost = "Q01b" in tracks
            q_cost, q_probability = _two_head_predictions(
                q_train,
                q_validation,
                context,
                spec.alpha,
                include_cost=include_cost,
            )
            arrays["q_probability"] = q_probability
            if "Q01b" in tracks:
                if q_cost is None:
                    raise RuntimeError("D011 Q01b cost head was not fitted")
                metrics["Q01b"] = _cost_metrics(context, q_cost, q_probability)
                arrays["q_cost"] = q_cost
            if "FQK" in tracks:
                try:
                    metrics["FQK"] = _feasibility_metrics(context, q_probability)
                except GovernedIneligibleFold as error:
                    track_eligibility["FQK"] = {
                        "eligible": False,
                        "reason_code": "metric_undefined",
                        "reason": str(error),
                    }

    a02_diagnostics: dict[str, Any] | None = None
    a02_cost: np.ndarray | None = None
    a02_probability: np.ndarray | None = None
    a02_track_eligibility: dict[str, dict[str, Any]] = {
        track: {
            "eligible": False,
            "reason_code": "not_run_for_report_only_sensitivity"
            if stage == "sensitivity"
            else "projected_kernel_not_eligible",
            "reason": None,
        }
        for track in tracks
    }
    if stage != "sensitivity" and q_probability is not None:
        try:
            a02_train, a02_validation, a02_diagnostics = _nystrom_embedding(
                context.compressed_train[spec.qubits],
                context.compressed_validation[spec.qubits],
                context,
                spec,
                seed_value=seed_value,
                projected_quantum=False,
            )
        except GovernedIneligibleFold as error:
            for track in tracks:
                a02_track_eligibility[track] = {
                    "eligible": False,
                    "reason_code": "a02_geometry_undefined",
                    "reason": str(error),
                }
        else:
            a02_cost, a02_probability = _two_head_predictions(
                a02_train,
                a02_validation,
                context,
                spec.alpha,
                include_cost="Q01b" in tracks,
            )
            arrays["a02_probability"] = a02_probability
            for track in tracks:
                a02_track_eligibility[track] = {
                    "eligible": True,
                    "reason_code": None,
                    "reason": None,
                }
            if "Q01b" in tracks:
                if a02_cost is None:
                    raise RuntimeError("D011 A02 Q01b cost head was not fitted")
                metrics["A02_Q01b"] = _cost_metrics(context, a02_cost, a02_probability)
                arrays["a02_cost"] = a02_cost
            if "FQK" in tracks:
                try:
                    metrics["A02_FQK"] = _feasibility_metrics(context, a02_probability)
                except GovernedIneligibleFold as error:
                    a02_track_eligibility["FQK"] = {
                        "eligible": False,
                        "reason_code": "metric_undefined",
                        "reason": str(error),
                    }

    _atomic_npz(prediction_path, arrays)
    eligible = all(bool(track_eligibility[track]["eligible"]) for track in tracks)
    payload = {
        "schema_version": "0.1.0",
        "status": "complete" if eligible else "complete_governed_ineligible",
        "eligible": eligible,
        "track_eligibility": track_eligibility,
        "a02_track_eligibility": a02_track_eligibility,
        "task_signature": signature,
        **identity,
        "metrics": metrics,
        "projected_kernel_diagnostics": q_diagnostics,
        "a02_kernel_diagnostics": a02_diagnostics,
        "wall_time_s": time.perf_counter() - started,
        "source_split": "development",
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    _atomic_json(summary_path, payload)
    return payload


def aggregate_projection_task(
    fold_directory: Path,
    spec: ProjectionSpec,
    records: Sequence[Mapping[str, Any]],
    *,
    track_id: str,
    fold_ids: Sequence[str],
    model_view: str = "projected",
) -> dict[str, Any]:
    """Pool one projection/track across the five authorized OOF folds."""

    if track_id not in TRACK_IDS:
        raise ValueError("D011 aggregate track is invalid")
    if model_view not in {"projected", "A02"}:
        raise ValueError("D011 projection aggregate view is invalid")
    fold_payloads: list[dict[str, Any]] = []
    probabilities: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    ineligible_folds: list[dict[str, Any]] = []
    metric_key = track_id if model_view == "projected" else f"A02_{track_id}"
    probability_key = (
        "q_probability" if model_view == "projected" else "a02_probability"
    )
    diagnostic_key = (
        "projected_kernel_diagnostics"
        if model_view == "projected"
        else "a02_kernel_diagnostics"
    )
    for fold_id in fold_ids:
        summary_path = fold_directory / fold_id / f"{spec.projection_id}.json"
        prediction_path = fold_directory / fold_id / f"{spec.projection_id}.npz"
        if not summary_path.is_file() or not prediction_path.is_file():
            raise FileNotFoundError(
                f"D011 projection checkpoint is incomplete: {spec.projection_id} {fold_id}"
            )
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        if track_id not in payload["active_tracks"]:
            raise PermissionError(
                f"D011 endpoint was not authorized: {track_id} {spec.projection_id}"
            )
        eligibility = (
            payload["track_eligibility"][track_id]
            if model_view == "projected"
            else payload["a02_track_eligibility"][track_id]
        )
        if not bool(eligibility["eligible"]):
            ineligible_folds.append(
                {
                    "fold_id": fold_id,
                    "reason_code": eligibility.get("reason_code"),
                    "reason": eligibility.get("reason"),
                }
            )
            continue
        if metric_key not in payload["metrics"]:
            raise PermissionError(
                f"D011 eligible fold lacks metrics: {metric_key} {fold_id}"
            )
        if payload.get(diagnostic_key) is None:
            raise PermissionError(
                f"D011 eligible fold lacks diagnostics: {model_view} {fold_id}"
            )
        fold_payloads.append(payload)
        if track_id == "FQK":
            with np.load(prediction_path, allow_pickle=False) as arrays:
                validation_indices = np.asarray(arrays["validation_indices"], dtype=int)
                probabilities.append(np.asarray(arrays[probability_key], dtype=float))
            labels.append(
                np.asarray(
                    [
                        int(
                            records[index]["outcomes"][
                                "independently_propagated_feasible"
                            ]
                        )
                        for index in validation_indices
                    ],
                    dtype=int,
                )
            )

    diagnostics = [row[diagnostic_key] for row in fold_payloads]
    summary: dict[str, Any] = {
        "projection_id": spec.projection_id,
        "track_id": track_id,
        "model_view": model_view,
        "qubits": spec.qubits,
        "layers": spec.layers,
        "feature_scale": spec.feature_scale,
        "entangle": spec.entangle,
        "gamma_multiplier": spec.gamma_multiplier,
        "alpha": spec.alpha,
        "landmarks": spec.landmarks,
        "fold_count": len(fold_payloads),
        "eligible": not ineligible_folds and len(fold_payloads) == len(fold_ids),
        "ineligible_folds": ineligible_folds,
        "wall_time_s": float(sum(float(row["wall_time_s"]) for row in fold_payloads)),
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    diagnostic_fields = (
        "gamma",
        "clipped_eigenvalues",
        "minimum_eigenvalue_before_clip",
        "maximum_negative_eigenvalue",
        "off_diagonal_mean",
        "off_diagonal_std",
        "off_diagonal_q05",
        "off_diagonal_q95",
        "effective_rank",
        "regularized_condition_number",
        "kernel_target_alignment_q01b",
        "kernel_target_alignment_fqk",
    )
    for field in diagnostic_fields:
        values = [
            float(row[field])
            for row in diagnostics
            if row.get(field) is not None and math.isfinite(float(row[field]))
        ]
        summary[field] = float(np.mean(values)) if values else None
    if not summary["eligible"]:
        summary["status"] = "governed_ineligible"
        return summary
    summary["status"] = "complete"
    if track_id == "Q01b":
        metrics = [row["metrics"][metric_key] for row in fold_payloads]
        squared_error = sum(float(row["squared_error_sum"]) for row in metrics)
        rows = sum(int(row["validation_rows"]) for row in metrics)
        regret_sum = sum(float(row["regret_sum_m_s"]) for row in metrics)
        decision_sets = sum(int(row["decision_sets"]) for row in metrics)
        fold_nrmse = [float(row["nrmse"]) for row in metrics]
        pooled_rmse = math.sqrt(squared_error / rows)
        scales = {float(row["development_scale"]) for row in metrics}
        if len(scales) != 1:
            raise ValueError("D011 development NRMSE scale changed across folds")
        scale = scales.pop()
        summary.update(
            {
                "pooled_oof_rmse": pooled_rmse,
                "pooled_oof_nrmse": pooled_rmse / scale,
                "mean_fold_nrmse": float(np.mean(fold_nrmse)),
                "mean_regret_m_s": regret_sum / decision_sets,
                "validation_rows": rows,
                "decision_sets": decision_sets,
            }
        )
    else:
        pooled_probability = np.concatenate(probabilities)
        pooled_labels = np.concatenate(labels)
        metrics = feasibility_metrics(
            pooled_labels,
            pooled_probability,
            threshold=0.5,
            calibration_bins=10,
        )
        summary.update(
            {
                "pooled_oof_brier": metrics.brier,
                "recall_at_0_5": metrics.recall,
                "auroc": metrics.auroc,
                "precision_at_0_5": metrics.precision,
                "expected_calibration_error": metrics.expected_calibration_error,
                "validation_rows": metrics.samples,
                "false_negative_rate": float(
                    np.mean(pooled_probability[pooled_labels == 1] < 0.5)
                ),
                "false_positive_rate": float(
                    np.mean(pooled_probability[pooled_labels == 0] >= 0.5)
                ),
                "predicted_feasible_rate": float(np.mean(pooled_probability >= 0.5)),
            }
        )
    return summary


def aggregate_control_task(
    fold_directory: Path,
    records: Sequence[Mapping[str, Any]],
    *,
    track_id: str,
    control_label: str,
    fold_ids: Sequence[str],
) -> dict[str, Any]:
    """Pool one reusable matched control across all authorized OOF folds."""

    if track_id not in TRACK_IDS:
        raise ValueError("D011 aggregate control track is invalid")
    metric_key = f"{control_label}_{track_id}"
    fold_payloads: list[dict[str, Any]] = []
    probabilities: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    ineligible_folds: list[dict[str, Any]] = []
    for fold_id in fold_ids:
        summary_path = fold_directory / fold_id / "controls.json"
        prediction_path = fold_directory / fold_id / "controls.npz"
        if not summary_path.is_file() or not prediction_path.is_file():
            raise FileNotFoundError(
                f"D011 control checkpoint is incomplete: {control_label} {fold_id}"
            )
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        if track_id not in payload["active_tracks"]:
            raise PermissionError(
                f"D011 control endpoint was not authorized: {track_id} {fold_id}"
            )
        status = payload.get("metric_status", {}).get(metric_key)
        if status is None:
            raise PermissionError(
                f"D011 control metric status is absent: {metric_key} {fold_id}"
            )
        if not bool(status["eligible"]):
            ineligible_folds.append(
                {
                    "fold_id": fold_id,
                    "reason_code": status.get("reason_code"),
                    "reason": status.get("reason"),
                }
            )
            continue
        fold_payloads.append(payload)
        if track_id == "FQK":
            with np.load(prediction_path, allow_pickle=False) as arrays:
                validation_indices = np.asarray(arrays["validation_indices"], dtype=int)
                probabilities.append(
                    np.asarray(arrays[f"probability__{control_label}"], dtype=float)
                )
            labels.append(
                np.asarray(
                    [
                        int(
                            records[index]["outcomes"][
                                "independently_propagated_feasible"
                            ]
                        )
                        for index in validation_indices
                    ],
                    dtype=int,
                )
            )

    summary: dict[str, Any] = {
        "control_id": control_label,
        "track_id": track_id,
        "model_view": "control",
        "fold_count": len(fold_payloads),
        "eligible": not ineligible_folds and len(fold_payloads) == len(fold_ids),
        "ineligible_folds": ineligible_folds,
        "wall_time_s": float(sum(float(row["wall_time_s"]) for row in fold_payloads)),
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    if not summary["eligible"]:
        summary["status"] = "governed_ineligible"
        return summary
    summary["status"] = "complete"
    if track_id == "Q01b":
        metrics = [row["metrics"][metric_key] for row in fold_payloads]
        squared_error = sum(float(row["squared_error_sum"]) for row in metrics)
        rows = sum(int(row["validation_rows"]) for row in metrics)
        regret_sum = sum(float(row["regret_sum_m_s"]) for row in metrics)
        decision_sets = sum(int(row["decision_sets"]) for row in metrics)
        scales = {float(row["development_scale"]) for row in metrics}
        if len(scales) != 1:
            raise ValueError("D011 control NRMSE scale changed across folds")
        pooled_rmse = math.sqrt(squared_error / rows)
        summary.update(
            {
                "pooled_oof_rmse": pooled_rmse,
                "pooled_oof_nrmse": pooled_rmse / scales.pop(),
                "mean_fold_nrmse": float(
                    np.mean([float(row["nrmse"]) for row in metrics])
                ),
                "mean_regret_m_s": regret_sum / decision_sets,
                "validation_rows": rows,
                "decision_sets": decision_sets,
            }
        )
    else:
        pooled_probability = np.concatenate(probabilities)
        pooled_labels = np.concatenate(labels)
        metrics = feasibility_metrics(
            pooled_labels,
            pooled_probability,
            threshold=0.5,
            calibration_bins=10,
        )
        summary.update(
            {
                "pooled_oof_brier": metrics.brier,
                "recall_at_0_5": metrics.recall,
                "auroc": metrics.auroc,
                "precision_at_0_5": metrics.precision,
                "expected_calibration_error": metrics.expected_calibration_error,
                "validation_rows": metrics.samples,
                "false_negative_rate": float(
                    np.mean(pooled_probability[pooled_labels == 1] < 0.5)
                ),
                "false_positive_rate": float(
                    np.mean(pooled_probability[pooled_labels == 0] >= 0.5)
                ),
                "predicted_feasible_rate": float(np.mean(pooled_probability >= 0.5)),
            }
        )
    return summary


def _fold_ids(config: Mapping[str, Any]) -> list[str]:
    rows = config["campaign"]["validation_rows_by_fold"]
    fold_ids = sorted(str(value) for value in rows)
    if fold_ids != ["CV01", "CV02", "CV03", "CV04", "CV05"]:
        raise ValueError("D011 fold IDs differ from the accepted manifest")
    return fold_ids


def _spec_map(specs: Sequence[ProjectionSpec]) -> dict[str, ProjectionSpec]:
    return {spec.projection_id: spec for spec in specs}


def _next_retain(config: Mapping[str, Any], rung_index: int) -> int | None:
    rungs = config["campaign"]["tuning_rungs"]
    if rung_index + 1 >= len(rungs):
        return None
    return int(rungs[rung_index + 1]["retain_per_track"])


def run_tuning_campaign(
    root: Path,
    output_root: Path,
    config: Mapping[str, Any],
    source_commit: str,
    records: Sequence[Mapping[str, Any]],
    manifest: Sequence[Mapping[str, str]],
    phase_config: Mapping[str, Any],
    specs: Sequence[ProjectionSpec],
) -> dict[str, Any]:
    """Run endpoint-specific D011 successive halving with resumable folds."""

    fold_ids = _fold_ids(config)
    spec_by_id = _spec_map(specs)
    active: dict[str, list[str]] = {
        track: [spec.projection_id for spec in specs] for track in TRACK_IDS
    }
    history: list[dict[str, Any]] = []
    selected: dict[str, str | None] = {track: None for track in TRACK_IDS}
    terminated: dict[str, dict[str, Any] | None] = {track: None for track in TRACK_IDS}

    for rung_index, rung in enumerate(config["campaign"]["tuning_rungs"]):
        rung_samples = int(rung["development_samples"])
        union_ids = sorted(set(active["Q01b"]) | set(active["FQK"]))
        if not union_ids:
            break
        dimensions = sorted({spec_by_id[value].qubits for value in union_ids})
        rung_root = output_root / "tuning" / f"rung_{rung_samples:04d}"
        print(f"D011 tuning rung {rung_samples}: {len(union_ids)} shared projections")
        for fold_id in fold_ids:
            state_cache: dict[tuple[Any, ...], tuple[np.ndarray, np.ndarray]] = {}
            context = build_fold_context(
                records,
                manifest,
                phase_config,
                fold_id=fold_id,
                rung_samples=rung_samples,
                qubit_dimensions=dimensions,
            )
            fold_root = rung_root / fold_id
            execute_control_fold(
                root,
                fold_root,
                context,
                source_commit=source_commit,
                stage="tuning",
                seed_index=0,
                qubit_dimensions=dimensions,
                active_tracks=[track for track in TRACK_IDS if active[track]],
            )
            for projection_id in union_ids:
                tracks = [
                    track for track in TRACK_IDS if projection_id in active[track]
                ]
                execute_projection_fold(
                    fold_root,
                    context,
                    spec_by_id[projection_id],
                    config,
                    source_commit=source_commit,
                    stage="tuning",
                    seed_index=0,
                    active_tracks=tracks,
                    state_cache=state_cache,
                )
            print(f"D011 tuning rung {rung_samples}: {fold_id} complete")

        rung_record: dict[str, Any] = {
            "rung_samples": rung_samples,
            "union_projection_ids": union_ids,
            "tracks": {},
        }
        next_retain = _next_retain(config, rung_index)
        for track in TRACK_IDS:
            if terminated[track] is not None:
                rung_record["tracks"][track] = {
                    "status": "not_reached_under_frozen_eligibility",
                    "authorized_projection_ids": [],
                }
                continue
            summaries = [
                aggregate_projection_task(
                    rung_root,
                    spec_by_id[projection_id],
                    records,
                    track_id=track,
                    fold_ids=fold_ids,
                )
                for projection_id in active[track]
            ]
            eligible = [row for row in summaries if bool(row["eligible"])]
            eligible = sorted(eligible, key=lambda row: endpoint_rank_key(row, track))
            ineligible = [row for row in summaries if not bool(row["eligible"])]
            summaries = [*eligible, *ineligible]
            a02_summaries = [
                aggregate_projection_task(
                    rung_root,
                    spec_by_id[projection_id],
                    records,
                    track_id=track,
                    fold_ids=fold_ids,
                    model_view="A02",
                )
                for projection_id in active[track]
            ]
            control_labels = (
                ["C06-T17"]
                if track == "Q01b"
                else [
                    "C01-T18",
                    "C02-T02",
                    "C03-T13",
                    "C04-T28",
                    "C05-T12",
                    "C06-T17",
                ]
            )
            for qubits in dimensions:
                control_labels.extend([f"A01-T04-q{qubits}", f"C05-T17-q{qubits}"])
            control_summaries = [
                aggregate_control_task(
                    rung_root,
                    records,
                    track_id=track,
                    control_label=label,
                    fold_ids=fold_ids,
                )
                for label in control_labels
            ]
            summary_path = rung_root / f"{track}_summaries.json"
            _atomic_json(
                summary_path,
                {
                    "source_commit": source_commit,
                    "track_id": track,
                    "rung_samples": rung_samples,
                    "summaries": summaries,
                    "a02_summaries": a02_summaries,
                    "control_summaries": control_summaries,
                },
            )
            if next_retain is None:
                if eligible:
                    selected[track] = str(eligible[0]["projection_id"])
                    active[track] = [str(eligible[0]["projection_id"])]
                    status = "selected"
                else:
                    terminated[track] = {
                        "rung_samples": rung_samples,
                        "eligible": 0,
                        "required": 1,
                    }
                    active[track] = []
                    status = "terminal_nonadvancement"
            elif len(eligible) < next_retain:
                terminated[track] = {
                    "rung_samples": rung_samples,
                    "eligible": len(eligible),
                    "required": next_retain,
                }
                active[track] = []
                status = "terminal_nonadvancement"
            else:
                advanced = select_with_advancement_floor(
                    eligible,
                    track_id=track,
                    retain=next_retain,
                )
                active[track] = [str(row["projection_id"]) for row in advanced]
                status = "advanced"
            rung_record["tracks"][track] = {
                "status": status,
                "eligible_count": len(eligible),
                "authorized_projection_ids": list(active[track]),
                "selected_projection_id": selected[track],
                "termination": terminated[track],
            }
        history.append(rung_record)
        _atomic_json(
            rung_root / "authorization.json",
            {
                "schema_version": "0.1.0",
                "status": "complete",
                "source_commit": source_commit,
                **rung_record,
                "calibration_rows_read": 0,
                "final_test_rows_read": 0,
            },
        )

    result = {
        "schema_version": "0.1.0",
        "status": "complete",
        "source_commit": source_commit,
        "history": history,
        "selected_projection_ids": selected,
        "terminal_nonadvancement": terminated,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    _atomic_json(output_root / "tuning" / "tuning_index.json", result)
    return result


def run_selected_seed_campaign(
    root: Path,
    output_root: Path,
    config: Mapping[str, Any],
    source_commit: str,
    records: Sequence[Mapping[str, Any]],
    manifest: Sequence[Mapping[str, str]],
    phase_config: Mapping[str, Any],
    specs: Sequence[ProjectionSpec],
    tuning: Mapping[str, Any],
) -> dict[str, Any]:
    """Run each reached selected track on the 20 frozen seed indices."""

    selected = {
        track: value
        for track, value in tuning["selected_projection_ids"].items()
        if value is not None
    }
    spec_by_id = _spec_map(specs)
    fold_ids = _fold_ids(config)
    summaries: list[dict[str, Any]] = []
    a02_summaries: list[dict[str, Any]] = []
    control_summaries: list[dict[str, Any]] = []
    if not selected:
        result = {
            "status": "not_reached_under_frozen_eligibility",
            "source_commit": source_commit,
            "summaries": [],
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
        }
        _atomic_json(output_root / "selected" / "selected_index.json", result)
        return result

    grouped: dict[str, list[str]] = {}
    for track, projection_id in selected.items():
        grouped.setdefault(str(projection_id), []).append(track)
    dimensions = sorted({spec_by_id[projection_id].qubits for projection_id in grouped})
    contexts = {
        fold_id: build_fold_context(
            records,
            manifest,
            phase_config,
            fold_id=fold_id,
            rung_samples=1024,
            qubit_dimensions=dimensions,
        )
        for fold_id in fold_ids
    }
    state_cache: dict[tuple[Any, ...], tuple[np.ndarray, np.ndarray]] = {}
    seed_indices = [int(value) for value in config["campaign"]["selected_seed_indices"]]
    for seed_index in seed_indices:
        seed_root = output_root / "selected" / f"seed_{seed_index:02d}"
        print(f"D011 selected configurations: seed {seed_index:02d}")
        for fold_id in fold_ids:
            context = contexts[fold_id]
            fold_root = seed_root / fold_id
            execute_control_fold(
                root,
                fold_root,
                context,
                source_commit=source_commit,
                stage="selected",
                seed_index=seed_index,
                qubit_dimensions=dimensions,
                active_tracks=sorted(selected),
            )
            for projection_id, tracks in grouped.items():
                execute_projection_fold(
                    fold_root,
                    context,
                    spec_by_id[projection_id],
                    config,
                    source_commit=source_commit,
                    stage="selected",
                    seed_index=seed_index,
                    active_tracks=tracks,
                    state_cache=state_cache,
                )
        for track, projection_id in selected.items():
            spec = spec_by_id[str(projection_id)]
            summary = aggregate_projection_task(
                seed_root,
                spec,
                records,
                track_id=track,
                fold_ids=fold_ids,
            )
            summary["seed_index"] = seed_index
            summaries.append(summary)
            a02_summary = aggregate_projection_task(
                seed_root,
                spec,
                records,
                track_id=track,
                fold_ids=fold_ids,
                model_view="A02",
            )
            a02_summary["seed_index"] = seed_index
            a02_summaries.append(a02_summary)
            labels = (
                ["C06-T17"]
                if track == "Q01b"
                else [
                    "C01-T18",
                    "C02-T02",
                    "C03-T13",
                    "C04-T28",
                    "C05-T12",
                    "C06-T17",
                ]
            )
            labels.extend(
                [
                    f"A01-T04-q{spec.qubits}",
                    f"C05-T17-q{spec.qubits}",
                ]
            )
            for label in labels:
                control = aggregate_control_task(
                    seed_root,
                    records,
                    track_id=track,
                    control_label=label,
                    fold_ids=fold_ids,
                )
                control["seed_index"] = seed_index
                control_summaries.append(control)
        _atomic_json(
            seed_root / "seed_summary.json",
            {
                "status": "complete",
                "source_commit": source_commit,
                "seed_index": seed_index,
                "summaries": [
                    row for row in summaries if int(row["seed_index"]) == seed_index
                ],
                "a02_summaries": [
                    row for row in a02_summaries if int(row["seed_index"]) == seed_index
                ],
                "control_summaries": [
                    row
                    for row in control_summaries
                    if int(row["seed_index"]) == seed_index
                ],
                "calibration_rows_read": 0,
                "final_test_rows_read": 0,
            },
        )

    result = {
        "schema_version": "0.1.0",
        "status": "complete",
        "source_commit": source_commit,
        "selected_projection_ids": selected,
        "seed_indices": seed_indices,
        "summaries": summaries,
        "a02_summaries": a02_summaries,
        "control_summaries": control_summaries,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    _atomic_json(output_root / "selected" / "selected_index.json", result)
    return result


def run_sensitivity_campaign(
    output_root: Path,
    config: Mapping[str, Any],
    source_commit: str,
    records: Sequence[Mapping[str, Any]],
    manifest: Sequence[Mapping[str, str]],
    phase_config: Mapping[str, Any],
    specs: Sequence[ProjectionSpec],
    selected_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Run only report-stage finite-shot/noise views of reached selections."""

    selected = selected_result.get("selected_projection_ids", {})
    spec_by_id = _spec_map(specs)
    fold_ids = _fold_ids(config)
    summaries: list[dict[str, Any]] = []
    conditions = [
        str(value)
        for value in config["sensitivities"]["conditions"]
        if str(value) != "exact_statevector"
    ]
    if selected_result.get("status") != "complete":
        result = {
            "status": "not_reached_under_frozen_eligibility",
            "source_commit": source_commit,
            "summaries": [],
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
        }
        _atomic_json(output_root / "sensitivity" / "sensitivity_index.json", result)
        return result

    dimensions = sorted(
        {spec_by_id[str(projection_id)].qubits for projection_id in selected.values()}
    )
    contexts = {
        fold_id: build_fold_context(
            records,
            manifest,
            phase_config,
            fold_id=fold_id,
            rung_samples=1024,
            qubit_dimensions=dimensions,
        )
        for fold_id in fold_ids
    }
    exact_state_cache: dict[tuple[Any, ...], np.ndarray] = {}
    for track, projection_id in selected.items():
        spec = spec_by_id[str(projection_id)]
        for condition in conditions:
            for seed_index in selected_result["seed_indices"]:
                task_root = (
                    output_root
                    / "sensitivity"
                    / track
                    / condition
                    / f"seed_{int(seed_index):02d}"
                )
                print(
                    f"D011 sensitivity {track} {condition}: seed {int(seed_index):02d}"
                )
                for fold_id in fold_ids:
                    context = contexts[fold_id]
                    execute_projection_fold(
                        task_root / fold_id,
                        context,
                        spec,
                        config,
                        source_commit=source_commit,
                        stage="sensitivity",
                        seed_index=int(seed_index),
                        active_tracks=[track],
                        condition=condition,
                        exact_state_cache=exact_state_cache,
                    )
                summary = aggregate_projection_task(
                    task_root,
                    spec,
                    records,
                    track_id=track,
                    fold_ids=fold_ids,
                )
                summary.update(
                    {
                        "seed_index": int(seed_index),
                        "condition": condition,
                    }
                )
                summaries.append(summary)

    exact = [
        {**row, "condition": "exact_statevector"}
        for row in selected_result["summaries"]
    ]
    result = {
        "schema_version": "0.1.0",
        "status": "complete",
        "source_commit": source_commit,
        "summaries": [*exact, *summaries],
        "selection_affected": False,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    _atomic_json(output_root / "sensitivity" / "sensitivity_index.json", result)
    return result


@contextmanager
def d011_campaign_lock(checkpoint_root: Path) -> Any:
    """Prevent concurrent D011 campaign writers without masking interruptions."""

    checkpoint_root.mkdir(parents=True, exist_ok=True)
    path = checkpoint_root / ".d011_campaign.lock"
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(f"created_unix_s={time.time():.6f}\n")
    except FileExistsError as error:
        raise PermissionError("A D011 campaign writer is already active") from error
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def runtime_resource_snapshot(
    root: Path,
    config: Mapping[str, Any],
    *,
    wall_seconds: float,
    cpu_seconds: float,
) -> dict[str, float]:
    """Fail closed when the active campaign reaches a D011 resource boundary."""

    ceilings = config["fold_shape_correction"]["ceilings"]
    free_gib = shutil.disk_usage(root).free / float(1024**3)
    peak_gib = process_memory_observation().peak_bytes / float(1024**3)
    checkpoint_root = root / str(config["campaign"]["checkpoint_root"])
    artifact_bytes = sum(
        path.stat().st_size for path in checkpoint_root.rglob("*") if path.is_file()
    )
    artifact_gib = artifact_bytes / float(1024**3)
    checkpoint_work_seconds = sum(
        float(payload.get("wall_time_s", 0.0))
        for path in checkpoint_root.rglob("*.json")
        for payload in [json.loads(path.read_text(encoding="utf-8"))]
        if path.name == "controls.json" or path.name.startswith("PX-")
    )
    snapshot = {
        "cpu_core_hours": max(cpu_seconds, checkpoint_work_seconds) / 3600.0,
        "wall_clock_days": max(wall_seconds, checkpoint_work_seconds) / 86400.0,
        "new_artifacts_gib": artifact_gib,
        "peak_working_set_gib": peak_gib,
        "free_disk_gib": free_gib,
    }
    failures = []
    for name in (
        "cpu_core_hours",
        "wall_clock_days",
        "new_artifacts_gib",
        "peak_working_set_gib",
    ):
        if snapshot[name] > float(ceilings[name]):
            failures.append(name)
    if free_gib < float(ceilings["minimum_free_disk_gib"]):
        failures.append("minimum_free_disk_gib")
    if failures:
        raise RuntimeError(
            "D011 runtime resource boundary reached: " + ", ".join(failures)
        )
    return snapshot


def run_d011_campaign(root: Path) -> dict[str, Any]:
    """Run or resume the one accepted development-only P001 campaign."""

    config, source_commit, branch = verify_d011_authority(
        root,
        action="development_campaign",
        require_fold_shape_pass=True,
    )
    checkpoint_root = validate_development_output_path(
        root, root / str(config["campaign"]["checkpoint_root"])
    )
    reporting_root = validate_development_output_path(
        root, root / str(config["campaign"]["output_root"])
    )
    complete_path = checkpoint_root / "campaign_index.json"
    failure_path = checkpoint_root / "campaign_failure.json"
    if complete_path.is_file():
        existing = json.loads(complete_path.read_text(encoding="utf-8"))
        if (
            existing.get("status") != "complete"
            or existing.get("source_commit") != source_commit
        ):
            raise PermissionError("D011 completed campaign index is not source-valid")
        return existing
    if failure_path.is_file():
        raise PermissionError(
            "D011 has a recorded technical failure; a new prospective decision is required"
        )

    phase_config = committed_yaml(
        root, source_commit, str(config["source_binding"]["phase1_config"])
    )
    specs = load_projection_specs(
        root / str(config["source_binding"]["trial_manifest"])
    )
    source_hashes = {
        key: git_blob_sha256(root, source_commit, str(path))
        for key, path in config["source_binding"].items()
    }
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    development_rows_read = 0

    with d011_campaign_lock(checkpoint_root):
        try:
            invocation = {
                "schema_version": "0.1.0",
                "decision_id": "D011",
                "protocol_id": "P001",
                "status": "running_or_resuming_after_interruption",
                "source_commit": source_commit,
                "branch": branch,
                "source_hash_scope": "committed Git blob bytes",
                "source_hashes": source_hashes,
                "calibration_rows_read": 0,
                "final_test_rows_read": 0,
            }
            _atomic_json(checkpoint_root / "campaign_invocation.json", invocation)
            records, manifest = load_development_records(root, phase_config)
            development_rows_read = len(records)
            audit = audit_development_records(records, manifest, phase_config)
            resources = runtime_resource_snapshot(
                root,
                config,
                wall_seconds=time.perf_counter() - wall_started,
                cpu_seconds=time.process_time() - cpu_started,
            )
            tuning = run_tuning_campaign(
                root,
                checkpoint_root,
                config,
                source_commit,
                records,
                manifest,
                phase_config,
                specs,
            )
            resources = runtime_resource_snapshot(
                root,
                config,
                wall_seconds=time.perf_counter() - wall_started,
                cpu_seconds=time.process_time() - cpu_started,
            )
            selected = run_selected_seed_campaign(
                root,
                checkpoint_root,
                config,
                source_commit,
                records,
                manifest,
                phase_config,
                specs,
                tuning,
            )
            resources = runtime_resource_snapshot(
                root,
                config,
                wall_seconds=time.perf_counter() - wall_started,
                cpu_seconds=time.process_time() - cpu_started,
            )
            sensitivity = run_sensitivity_campaign(
                checkpoint_root,
                config,
                source_commit,
                records,
                manifest,
                phase_config,
                specs,
                selected,
            )
            resources = runtime_resource_snapshot(
                root,
                config,
                wall_seconds=time.perf_counter() - wall_started,
                cpu_seconds=time.process_time() - cpu_started,
            )
            result = {
                "schema_version": "0.1.0",
                "decision_id": "D011",
                "protocol_id": "P001",
                "status": "complete",
                "source_commit": source_commit,
                "branch": branch,
                "source_hash_scope": "committed Git blob bytes",
                "source_hashes": source_hashes,
                "development_audit": audit,
                "development_rows_read": development_rows_read,
                "calibration_rows_read": 0,
                "final_test_rows_read": 0,
                "hardware_jobs_submitted": 0,
                "gate6_runs": 0,
                "tuning": tuning,
                "selected": selected,
                "sensitivity": sensitivity,
                "runtime_resources": resources,
                "claim_boundary": (
                    "Development-only exploratory model evidence; no calibration, "
                    "final-test, mission, hardware, quantum-advantage, Gate 5 "
                    "revision, or Gate 6 claim."
                ),
            }
            _atomic_json(complete_path, result)
            reporting_root.mkdir(parents=True, exist_ok=True)
            return result
        except Exception as error:
            failure = {
                "schema_version": "0.1.0",
                "decision_id": "D011",
                "protocol_id": "P001",
                "status": "technical_failure",
                "source_commit": source_commit,
                "exception_type": type(error).__name__,
                "exception_message": str(error),
                "development_rows_read": development_rows_read,
                "calibration_rows_read": 0,
                "final_test_rows_read": 0,
                "hardware_jobs_submitted": 0,
                "gate6_runs": 0,
                "retry_authorized": False,
            }
            _atomic_json(failure_path, failure)
            raise
