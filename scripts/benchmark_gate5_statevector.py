"""Benchmark the D006 batched statevector path on synthetic inputs only."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import statistics
import time
from pathlib import Path

import numpy as np

from openqfuel.qml import (
    _z_expectations,
    circuit_features,
    circuit_state,
    quantum_kernel_matrix,
    statevector_batch,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/processed/reporting/gate5_statevector_batch_benchmark.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _timed(callable_, repeats: int = 3) -> tuple[float, object]:
    values = []
    result = None
    for _ in range(repeats):
        started = time.perf_counter()
        result = callable_()
        values.append(time.perf_counter() - started)
    return statistics.median(values), result


def _scalar_states(
    values: np.ndarray, parameters: np.ndarray | None = None
) -> np.ndarray:
    return np.vstack(
        [
            circuit_state(
                row,
                8,
                3,
                parameters=parameters,
                feature_scale=1.0,
                entangle=True,
            )
            for row in values
        ]
    )


def main() -> None:
    rng = np.random.default_rng(20260710)
    parameters = rng.uniform(-0.05, 0.05, size=(3, 8, 2))
    records = []
    for rows in (128, 1024):
        values = rng.normal(size=(rows, 8))
        scalar_state_s, scalar_states = _timed(lambda: _scalar_states(values))
        batch_state_s, batch_states = _timed(lambda: statevector_batch(values, 8, 3))
        scalar_feature_s, scalar_features = _timed(
            lambda: np.vstack(
                [
                    _z_expectations(state, 8)
                    for state in _scalar_states(values, parameters)
                ]
            )
        )
        batch_feature_s, batch_features = _timed(
            lambda: circuit_features(values, 8, 3, parameters)
        )
        scalar_kernel_s, scalar_kernel = _timed(
            lambda: (
                np.abs(_scalar_states(values).conj() @ _scalar_states(values).T) ** 2
            )
        )
        batch_kernel_s, batch_kernel = _timed(
            lambda: quantum_kernel_matrix(values, values, 8, 3)
        )
        records.append(
            {
                "rows": rows,
                "qubits": 8,
                "layers": 3,
                "repeats": 3,
                "scalar_state_s_median": scalar_state_s,
                "batch_state_s_median": batch_state_s,
                "state_speedup": scalar_state_s / batch_state_s,
                "state_max_abs_error": float(
                    np.max(np.abs(scalar_states - batch_states))
                ),
                "scalar_feature_s_median": scalar_feature_s,
                "batch_feature_s_median": batch_feature_s,
                "feature_speedup": scalar_feature_s / batch_feature_s,
                "feature_max_abs_error": float(
                    np.max(np.abs(scalar_features - batch_features))
                ),
                "scalar_self_kernel_s_median": scalar_kernel_s,
                "batch_self_kernel_s_median": batch_kernel_s,
                "self_kernel_speedup": scalar_kernel_s / batch_kernel_s,
                "self_kernel_max_abs_error": float(
                    np.max(np.abs(scalar_kernel - batch_kernel))
                ),
            }
        )
    payload = {
        "status": "synthetic_pre_fit_performance_and_equivalence_benchmark",
        "source_scope": "deterministic synthetic normal inputs; no research rows or outcomes",
        "seed": 20260710,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "numpy": importlib.metadata.version("numpy"),
        "qml_source_sha256": _sha256(ROOT / "src/openqfuel/qml.py"),
        "uv_lock_sha256": _sha256(ROOT / "uv.lock"),
        "benchmark_script_sha256": _sha256(Path(__file__)),
        "records": records,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
