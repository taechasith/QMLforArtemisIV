"""Run the accepted D009 synthetic-only compute admission benchmark."""

from __future__ import annotations

import ctypes
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from openqfuel.models import (  # noqa: E402
    build_classical_classifier,
    build_classical_regressor,
    build_qml_control_classifier,
    build_qml_control_regressor,
)
from openqfuel.post_gate5 import (  # noqa: E402
    assert_post_gate5_scope,
    equivalent_preflight_work_units,
    evaluate_preflight_admission,
    project_preflight_resources,
)
from openqfuel.qml import (  # noqa: E402
    deterministic_landmark_indices,
    median_projected_kernel_gamma,
    projected_quantum_features,
    projected_quantum_kernel_from_features,
    symmetrize_and_clip_psd,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_preflight.yaml"
MODEL_REGISTRY = ROOT / "experiments/phase1_model_registry.yaml"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _clean_source() -> tuple[str, str]:
    dirty = _git("status", "--porcelain")
    if dirty:
        raise RuntimeError("D009 requires a clean Git worktree")
    branch = _git("branch", "--show-current")
    if branch != "main":
        raise RuntimeError("D009 is accepted only on main")
    return _git("rev-parse", "HEAD"), branch


def _peak_working_set_bytes() -> int:
    if sys.platform == "win32":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        success = ctypes.windll.psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        )
        if not success:
            raise OSError("Unable to read Windows process memory counters")
        return int(counters.PeakWorkingSetSize)

    try:
        import resource

        value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return value if sys.platform == "darwin" else value * 1024
    except (ImportError, OSError):
        return 0


def _total_physical_memory_bytes() -> int:
    if sys.platform == "win32":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError("Unable to read Windows physical memory")
        return int(status.ullTotalPhys)
    return 0


def _timed(
    records: list[dict[str, Any]], name: str, operation: Callable[[], Any]
) -> Any:
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    result = operation()
    records.append(
        {
            "step": name,
            "wall_seconds": time.perf_counter() - wall_started,
            "cpu_seconds": time.process_time() - cpu_started,
            "peak_working_set_gib": _peak_working_set_bytes() / float(1024**3),
        }
    )
    return result


def _squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    values = (
        np.sum(left * left, axis=1)[:, None]
        + np.sum(right * right, axis=1)[None, :]
        - 2.0 * (left @ right.T)
    )
    return np.maximum(values, 0.0)


def _nystrom_features(
    training: np.ndarray,
    validation: np.ndarray,
    row_ids: list[str],
    config: dict[str, Any],
    *,
    projected_quantum: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, float | int]]:
    benchmark = config["benchmark"]
    landmark_indices = deterministic_landmark_indices(
        row_ids,
        str(benchmark["projection_id"]),
        str(benchmark["fold_id"]),
        int(benchmark["seed_index"]),
        int(benchmark["nystrom_landmarks"]),
    )
    landmarks = training[landmark_indices]
    if projected_quantum:
        gamma = median_projected_kernel_gamma(
            training, float(benchmark["gamma_multiplier"])
        )
        kernel = projected_quantum_kernel_from_features
    else:
        distances = _squared_distances(training, training)
        positive = distances[distances > 0.0]
        if positive.size == 0:
            raise ValueError("Synthetic A02 median distance is zero")
        gamma = float(benchmark["gamma_multiplier"]) / float(np.median(positive))
        def kernel(
            left: np.ndarray, right: np.ndarray, active_gamma: float
        ) -> np.ndarray:
            return np.exp(-active_gamma * _squared_distances(left, right))

    landmark_kernel = kernel(landmarks, landmarks, gamma)
    clipped, clip_info = symmetrize_and_clip_psd(landmark_kernel)
    eigenvalues, eigenvectors = np.linalg.eigh(clipped)
    inverse_root = (
        eigenvectors * (1.0 / np.sqrt(eigenvalues))
    ) @ eigenvectors.T
    training_features = kernel(training, landmarks, gamma) @ inverse_root
    validation_features = kernel(validation, landmarks, gamma) @ inverse_root
    diagnostics: dict[str, float | int] = {
        "gamma": gamma,
        "landmarks": int(landmark_indices.size),
        "clipped_eigenvalues": clip_info.clipped_eigenvalues,
        "minimum_eigenvalue_before_clip": clip_info.min_eigenvalue_before_clip,
        "maximum_negative_eigenvalue": clip_info.max_negative_eigenvalue,
    }
    return training_features, validation_features, diagnostics


def _fit_two_heads(
    training_features: np.ndarray,
    validation_features: np.ndarray,
    cost_target: np.ndarray,
    feasibility_target: np.ndarray,
    alpha: float,
) -> np.ndarray:
    targets = np.column_stack((cost_target, feasibility_target))
    system = training_features.T @ training_features
    system += float(alpha) * np.eye(system.shape[0])
    coefficients = np.linalg.solve(system, training_features.T @ targets)
    predictions = validation_features @ coefficients
    predictions[:, 1] = np.clip(predictions[:, 1], 0.0, 1.0)
    if not np.all(np.isfinite(predictions)):
        raise ValueError("Synthetic projected-kernel head predictions are non-finite")
    return predictions


def _registry_models() -> dict[str, dict[str, Any]]:
    payload = yaml.safe_load(MODEL_REGISTRY.read_text(encoding="utf-8"))
    return {str(row["trial_id"]): row for row in payload["models"]}


def _control_predictions(
    trial: dict[str, Any],
    train: np.ndarray,
    validation: np.ndarray,
    target: np.ndarray,
    *,
    classifier: bool,
    seed: int,
) -> np.ndarray:
    family = str(trial["model_family"])
    parameters = trial["parameters"]
    if family == "random_fourier_ridge":
        builder = (
            build_qml_control_classifier if classifier else build_qml_control_regressor
        )
        model = builder(family, parameters, seed)
    else:
        builder = build_classical_classifier if classifier else build_classical_regressor
        model = builder(family, parameters, seed)
    model.fit(train, target)
    if classifier:
        predictions = np.asarray(model.predict_proba(validation)[:, 1], dtype=float)
    else:
        predictions = np.asarray(model.predict(validation), dtype=float)
    if predictions.shape != (validation.shape[0],) or not np.all(
        np.isfinite(predictions)
    ):
        raise ValueError(f"Synthetic control output is invalid: {trial['trial_id']}")
    return predictions


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert_post_gate5_scope(config, action="compute_preflight", data_scope="synthetic")
    source_commit, branch = _clean_source()
    expected_units = float(
        config["campaign_projection"]["expected_equivalent_1024_row_work_units"]
    )
    actual_units = equivalent_preflight_work_units(config)
    if not np.isclose(actual_units, expected_units, rtol=0.0, atol=1e-12):
        raise ValueError("D009 campaign work-unit formula differs from its frozen value")

    benchmark = config["benchmark"]
    rng = np.random.default_rng(int(benchmark["seed"]))
    training_rows = int(benchmark["training_rows"])
    validation_rows = int(benchmark["validation_rows"])
    primary_width = int(benchmark["primary_control_feature_count"])
    compressed_width = int(benchmark["compressed_feature_count"])
    raw_train = rng.normal(size=(training_rows, primary_width))
    raw_validation = rng.normal(size=(validation_rows, primary_width))
    compressed_train = np.clip(
        rng.normal(size=(training_rows, compressed_width)), -3.0, 3.0
    ) * (np.pi / 3.0)
    compressed_validation = np.clip(
        rng.normal(size=(validation_rows, compressed_width)), -3.0, 3.0
    ) * (np.pi / 3.0)
    cost_target = (
        raw_train[:, -1]
        + 0.2 * np.sin(raw_train[:, 0])
        - 0.1 * raw_train[:, 1]
        + 0.02 * rng.normal(size=training_rows)
    )
    feasibility_score = (
        raw_train[:, 0] - 0.4 * raw_train[:, 1] + 0.2 * raw_train[:, 2]
    )
    feasibility_target = (
        feasibility_score >= np.median(feasibility_score)
    ).astype(int)
    if set(np.unique(feasibility_target)) != {0, 1}:
        raise ValueError("D009 synthetic feasibility labels must contain both classes")
    row_ids = [f"d009-synthetic-{index:04d}" for index in range(training_rows)]

    records: list[dict[str, Any]] = []
    benchmark_wall_started = time.perf_counter()
    benchmark_cpu_started = time.process_time()
    projected_train = _timed(
        records,
        "Q01b_FQK_shared_training_projection",
        lambda: projected_quantum_features(
            compressed_train,
            int(benchmark["qubits"]),
            int(benchmark["data_reupload_layers"]),
            feature_scale=float(benchmark["feature_scale"]),
            entangle=bool(benchmark["entangle"]),
        ),
    )
    projected_validation = _timed(
        records,
        "Q01b_FQK_shared_validation_projection",
        lambda: projected_quantum_features(
            compressed_validation,
            int(benchmark["qubits"]),
            int(benchmark["data_reupload_layers"]),
            feature_scale=float(benchmark["feature_scale"]),
            entangle=bool(benchmark["entangle"]),
        ),
    )
    q_train, q_validation, q_diagnostics = _timed(
        records,
        "Q01b_FQK_shared_projected_kernel_geometry",
        lambda: _nystrom_features(
            projected_train,
            projected_validation,
            row_ids,
            config,
            projected_quantum=True,
        ),
    )
    _timed(
        records,
        "Q01b_FQK_two_head_fit_and_inference",
        lambda: _fit_two_heads(
            q_train,
            q_validation,
            cost_target,
            feasibility_target,
            float(benchmark["regularization_alpha"]),
        ),
    )

    a02_train, a02_validation, a02_diagnostics = _timed(
        records,
        "A02_classical_RBF_geometry",
        lambda: _nystrom_features(
            compressed_train,
            compressed_validation,
            row_ids,
            config,
            projected_quantum=False,
        ),
    )
    _timed(
        records,
        "A02_classical_RBF_two_head_fit_and_inference",
        lambda: _fit_two_heads(
            a02_train,
            a02_validation,
            cost_target,
            feasibility_target,
            float(benchmark["regularization_alpha"]),
        ),
    )

    models = _registry_models()
    seed = int(benchmark["seed"])
    regression_controls = {
        "C06-T17_cost": (models["C06-T17"], raw_train, raw_validation),
        "A01-T04_cost": (
            models["A01-T04"],
            compressed_train,
            compressed_validation,
        ),
        "C05-T17_compressed_cost": (
            models["C05-T17"],
            compressed_train,
            compressed_validation,
        ),
    }
    for name, (trial, train, validation) in regression_controls.items():
        _timed(
            records,
            name,
            lambda trial=trial, train=train, validation=validation: _control_predictions(
                trial,
                train,
                validation,
                cost_target,
                classifier=False,
                seed=seed,
            ),
        )

    classifier_specs = [
        ("C01-T18", raw_train, raw_validation),
        ("C02-T02", raw_train, raw_validation),
        ("C03-T13", raw_train, raw_validation),
        ("C04-T28", raw_train, raw_validation),
        ("C05-T12", raw_train, raw_validation),
        ("C06-T17", raw_train, raw_validation),
        ("A01-T04", compressed_train, compressed_validation),
        ("C05-T17", compressed_train, compressed_validation),
    ]
    for trial_id, train, validation in classifier_specs:
        trial = models[trial_id]
        _timed(
            records,
            f"{trial_id}_feasibility",
            lambda trial=trial, train=train, validation=validation: _control_predictions(
                trial,
                train,
                validation,
                feasibility_target,
                classifier=True,
                seed=seed,
            ),
        )

    benchmark_wall_seconds = time.perf_counter() - benchmark_wall_started
    benchmark_cpu_seconds = time.process_time() - benchmark_cpu_started
    peak_rss_gib = _peak_working_set_bytes() / float(1024**3)
    free_disk_gib = shutil.disk_usage(ROOT).free / float(1024**3)
    projected = project_preflight_resources(
        config,
        benchmark_cpu_seconds=benchmark_cpu_seconds,
        benchmark_wall_seconds=benchmark_wall_seconds,
        peak_rss_gib=peak_rss_gib,
        free_disk_gib=free_disk_gib,
    )
    admission = evaluate_preflight_admission(config, projected)

    source_paths = config["source_binding"]
    source_hashes = {
        key: _sha256(ROOT / source_paths[key])
        for key in (
            "implementation_config",
            "model_registry",
            "qml_source",
            "model_source",
            "guard_source",
            "benchmark_script",
            "lockfile",
        )
    }
    payload = {
        "schema_version": "0.1.0",
        "decision_id": "D009",
        "protocol_id": "P001",
        "status": admission["status"],
        "evidence_scope": "deterministic synthetic compute admission only",
        "source_commit": source_commit,
        "branch": branch,
        "source_hashes": source_hashes,
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"),
            "scikit_learn": importlib.metadata.version("scikit-learn"),
            "logical_processors": os.cpu_count(),
            "physical_memory_gib": _total_physical_memory_bytes()
            / float(1024**3),
            "declared_reference_cpu": config["ceilings"].get(
                "reference_cpu", "Intel Core i9-13900HX"
            ),
            "declared_reference_gpu": "NVIDIA GeForce RTX 4060 Laptop GPU; unused",
        },
        "benchmark": {
            "seed": seed,
            "training_rows": training_rows,
            "validation_rows": validation_rows,
            "primary_control_feature_count": primary_width,
            "compressed_feature_count": compressed_width,
            "qubits": int(benchmark["qubits"]),
            "data_reupload_layers": int(benchmark["data_reupload_layers"]),
            "statevector_concurrency": int(benchmark["statevector_concurrency"]),
            "gpu_hours": 0.0,
            "wall_seconds": benchmark_wall_seconds,
            "cpu_seconds": benchmark_cpu_seconds,
            "steps": records,
            "projected_kernel_diagnostics": q_diagnostics,
            "classical_rbf_diagnostics": a02_diagnostics,
        },
        "campaign_projection": projected,
        "admission": admission,
        "integrity": {
            "clean_source_verified_before_execution": True,
            "synthetic_rows_used": training_rows + validation_rows,
            "development_rows_read": 0,
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
            "hardware_jobs_submitted": 0,
            "gate6_runs": 0,
            "statevectors_persisted": 0,
            "kernel_matrices_persisted": 0,
        },
        "claim_boundary": (
            "Synthetic compute-admission evidence only; no model-performance, "
            "research-data, Gate 5 reinterpretation, hardware, or Gate 6 claim."
        ),
        "next_step": (
            "Prepare D010 development-only execution decision"
            if admission["status"] == "PASS"
            else "Record governed STOP and keep P001 execution locked"
        ),
    }
    output = ROOT / source_paths["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": payload["status"], **projected}, indent=2))
    if payload["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
