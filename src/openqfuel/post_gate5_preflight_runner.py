"""Shared synthetic preflight helpers for post-Gate-5 compute checks."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import yaml

from .models import (
    build_classical_classifier,
    build_classical_regressor,
    build_qml_control_classifier,
    build_qml_control_regressor,
)
from .post_gate5 import process_memory_observation
from .qml import (
    deterministic_landmark_indices,
    median_projected_kernel_gamma,
    projected_quantum_kernel_from_features,
    symmetrize_and_clip_psd,
)


ROOT = Path(__file__).resolve().parents[2]
MODEL_REGISTRY = ROOT / "experiments/phase1_model_registry.yaml"


def timed(
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
            "peak_working_set_gib": process_memory_observation().peak_bytes
            / float(1024**3),
        }
    )
    return result


def squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    values = (
        np.sum(left * left, axis=1)[:, None]
        + np.sum(right * right, axis=1)[None, :]
        - 2.0 * (left @ right.T)
    )
    return np.maximum(values, 0.0)


def nystrom_features(
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
        distances = squared_distances(training, training)
        positive = distances[distances > 0.0]
        if positive.size == 0:
            raise ValueError("Synthetic A02 median distance is zero")
        gamma = float(benchmark["gamma_multiplier"]) / float(np.median(positive))

        def kernel(
            left: np.ndarray, right: np.ndarray, active_gamma: float
        ) -> np.ndarray:
            return np.exp(-active_gamma * squared_distances(left, right))

    landmark_kernel = kernel(landmarks, landmarks, gamma)
    clipped, clip_info = symmetrize_and_clip_psd(landmark_kernel)
    eigenvalues, eigenvectors = np.linalg.eigh(clipped)
    inverse_root = (eigenvectors * (1.0 / np.sqrt(eigenvalues))) @ eigenvectors.T
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


def fit_two_heads(
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


def registry_models() -> dict[str, dict[str, Any]]:
    payload = yaml.safe_load(MODEL_REGISTRY.read_text(encoding="utf-8"))
    return {str(row["trial_id"]): row for row in payload["models"]}


def control_predictions(
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
