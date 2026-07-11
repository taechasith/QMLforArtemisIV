"""Frozen, label-agnostic statistical functions for the Phase 1 benchmark."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Hashable, Sequence

import numpy as np
from sklearn.metrics import (
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass(frozen=True)
class RegressionMetrics:
    samples: int
    rmse: float
    nrmse: float
    mae: float


@dataclass(frozen=True)
class FeasibilityMetrics:
    samples: int
    precision: float
    recall: float
    auroc: float
    brier: float
    expected_calibration_error: float


@dataclass(frozen=True)
class RegretMetrics:
    decision_sets: int
    mean_regret_m_s: float
    median_regret_m_s: float
    independently_infeasible_selection_rate: float
    no_predicted_feasible_rate: float
    no_reference_feasible_rate: float


@dataclass(frozen=True)
class ConfidenceInterval:
    estimate: float
    lower: float
    upper: float
    confidence_level: float


def _one_dimensional(values: Sequence[float], name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional sequence")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def development_target_scale(values: Sequence[float]) -> float:
    """Return the frozen NRMSE denominator from development labels only."""

    array = _one_dimensional(values, "development targets")
    if array.size < 2:
        raise ValueError("At least two development targets are required")
    scale = float(np.std(array, ddof=1))
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("Development target standard deviation must be positive")
    return scale


def regression_metrics(
    observed: Sequence[float],
    predicted: Sequence[float],
    development_scale: float,
) -> RegressionMetrics:
    truth = _one_dimensional(observed, "observed values")
    estimate = _one_dimensional(predicted, "predicted values")
    if truth.shape != estimate.shape:
        raise ValueError("Observed and predicted values must align")
    if not math.isfinite(development_scale) or development_scale <= 0.0:
        raise ValueError("development_scale must be positive and finite")
    errors = estimate - truth
    rmse = float(np.sqrt(np.mean(errors * errors)))
    return RegressionMetrics(
        truth.size,
        rmse,
        rmse / development_scale,
        float(np.mean(np.abs(errors))),
    )


def expected_calibration_error(
    observed: Sequence[int], probabilities: Sequence[float], bins: int = 10
) -> float:
    labels = _one_dimensional(observed, "feasibility labels")
    probability = _one_dimensional(probabilities, "feasibility probabilities")
    if labels.shape != probability.shape:
        raise ValueError("Labels and probabilities must align")
    if not set(np.unique(labels)).issubset({0.0, 1.0}):
        raise ValueError("Feasibility labels must be binary")
    if np.any((probability < 0.0) | (probability > 1.0)):
        raise ValueError("Feasibility probabilities must lie in [0, 1]")
    if bins <= 1:
        raise ValueError("At least two calibration bins are required")
    edges = np.linspace(0.0, 1.0, bins + 1)
    assignments = np.minimum(np.digitize(probability, edges[1:-1]), bins - 1)
    error = 0.0
    for index in range(bins):
        selected = assignments == index
        if not np.any(selected):
            continue
        weight = float(np.mean(selected))
        error += weight * abs(
            float(np.mean(labels[selected])) - float(np.mean(probability[selected]))
        )
    return error


def feasibility_metrics(
    observed: Sequence[int],
    probabilities: Sequence[float],
    threshold: float = 0.5,
    calibration_bins: int = 10,
) -> FeasibilityMetrics:
    labels = _one_dimensional(observed, "feasibility labels")
    probability = _one_dimensional(probabilities, "feasibility probabilities")
    if labels.shape != probability.shape:
        raise ValueError("Labels and probabilities must align")
    if not set(np.unique(labels)).issubset({0.0, 1.0}):
        raise ValueError("Feasibility labels must be binary")
    if len(np.unique(labels)) != 2:
        raise ValueError("AUROC requires both feasibility classes")
    if np.any((probability < 0.0) | (probability > 1.0)):
        raise ValueError("Feasibility probabilities must lie in [0, 1]")
    if not 0.0 < threshold < 1.0:
        raise ValueError("Feasibility threshold must lie strictly inside (0, 1)")
    predicted = probability >= threshold
    return FeasibilityMetrics(
        labels.size,
        float(precision_score(labels, predicted, zero_division=0)),
        float(recall_score(labels, predicted, zero_division=0)),
        float(roc_auc_score(labels, probability)),
        float(brier_score_loss(labels, probability)),
        expected_calibration_error(labels, probability, calibration_bins),
    )


def feasibility_constrained_regret(
    decision_set_ids: Sequence[Hashable],
    predicted_cost_m_s: Sequence[float],
    predicted_feasibility_probability: Sequence[float],
    observed_cost_m_s: Sequence[float],
    observed_feasible: Sequence[int],
    feasibility_threshold: float = 0.5,
    infeasible_penalty_m_s: float = 20.0,
) -> RegretMetrics:
    """Score plan selection against the best independently feasible candidate."""

    group_ids = np.asarray(decision_set_ids, dtype=object)
    predicted_cost = _one_dimensional(predicted_cost_m_s, "predicted costs")
    probability = _one_dimensional(
        predicted_feasibility_probability, "predicted feasibility"
    )
    observed_cost = _one_dimensional(observed_cost_m_s, "observed costs")
    feasible = _one_dimensional(observed_feasible, "observed feasibility")
    size = predicted_cost.size
    if any(
        array.shape != (size,)
        for array in (group_ids, probability, observed_cost, feasible)
    ):
        raise ValueError("Decision-set arrays must align")
    if not set(np.unique(feasible)).issubset({0.0, 1.0}):
        raise ValueError("Observed feasibility must be binary")
    if np.any((probability < 0.0) | (probability > 1.0)):
        raise ValueError("Predicted feasibility must lie in [0, 1]")
    if infeasible_penalty_m_s <= 0.0:
        raise ValueError("Infeasible regret penalty must be positive")

    regrets: list[float] = []
    infeasible_selections = 0
    no_predicted_feasible = 0
    no_reference_feasible = 0
    unique_ids = list(dict.fromkeys(group_ids.tolist()))
    for group_id in unique_ids:
        selected = group_ids == group_id
        true_candidates = np.flatnonzero(selected & (feasible == 1.0))
        if true_candidates.size == 0:
            no_reference_feasible += 1
            regrets.append(infeasible_penalty_m_s)
            continue
        oracle_cost = float(np.min(observed_cost[true_candidates]))
        eligible = np.flatnonzero(selected & (probability >= feasibility_threshold))
        if eligible.size == 0:
            no_predicted_feasible += 1
            regrets.append(infeasible_penalty_m_s)
            continue
        chosen = int(eligible[np.argmin(predicted_cost[eligible])])
        if feasible[chosen] != 1.0:
            infeasible_selections += 1
            regrets.append(infeasible_penalty_m_s)
            continue
        regrets.append(max(0.0, float(observed_cost[chosen]) - oracle_cost))

    regret_array = np.asarray(regrets)
    count = len(unique_ids)
    return RegretMetrics(
        count,
        float(np.mean(regret_array)),
        float(np.median(regret_array)),
        infeasible_selections / count,
        no_predicted_feasible / count,
        no_reference_feasible / count,
    )


def burn_vector_errors(
    observed: Sequence[Sequence[float]], predicted: Sequence[Sequence[float]]
) -> tuple[np.ndarray, np.ndarray]:
    truth = np.asarray(observed, dtype=float)
    estimate = np.asarray(predicted, dtype=float)
    if truth.ndim != 2 or truth.shape[1] != 3 or truth.shape != estimate.shape:
        raise ValueError("Burn vectors must be aligned N x 3 arrays")
    if not np.all(np.isfinite(truth)) or not np.all(np.isfinite(estimate)):
        raise ValueError("Burn vectors must be finite")
    truth_norm = np.linalg.norm(truth, axis=1)
    estimate_norm = np.linalg.norm(estimate, axis=1)
    magnitude_error = np.abs(estimate_norm - truth_norm)
    denominator = truth_norm * estimate_norm
    angle = np.zeros(truth.shape[0], dtype=float)
    one_zero = (denominator == 0.0) & ((truth_norm + estimate_norm) > 0.0)
    angle[one_zero] = 180.0
    valid = denominator > 0.0
    cosine = np.clip(
        np.sum(truth[valid] * estimate[valid], axis=1) / denominator[valid],
        -1.0,
        1.0,
    )
    angle[valid] = np.degrees(np.arccos(cosine))
    return magnitude_error, angle


def paired_bootstrap_mean_interval(
    paired_differences: Sequence[float],
    confidence_level: float = 0.95,
    replicates: int = 10000,
    seed: int = 0,
) -> ConfidenceInterval:
    differences = _one_dimensional(paired_differences, "paired differences")
    if not 0.0 < confidence_level < 1.0 or replicates <= 0:
        raise ValueError("Invalid bootstrap settings")
    rng = np.random.default_rng(seed)
    means = np.empty(replicates, dtype=float)
    for start in range(0, replicates, 1000):
        stop = min(start + 1000, replicates)
        indices = rng.integers(
            0, differences.size, size=(stop - start, differences.size)
        )
        means[start:stop] = np.mean(differences[indices], axis=1)
    alpha = 1.0 - confidence_level
    lower, upper = np.quantile(means, [alpha / 2.0, 1.0 - alpha / 2.0])
    return ConfidenceInterval(
        float(np.mean(differences)), float(lower), float(upper), confidence_level
    )


def paired_sign_permutation_pvalue(
    paired_differences: Sequence[float], replicates: int = 10000, seed: int = 0
) -> float:
    differences = _one_dimensional(paired_differences, "paired differences")
    if replicates <= 0:
        raise ValueError("Permutation replicates must be positive")
    observed = abs(float(np.mean(differences)))
    rng = np.random.default_rng(seed)
    extreme = 0
    for start in range(0, replicates, 1000):
        count = min(1000, replicates - start)
        signs = rng.choice((-1.0, 1.0), size=(count, differences.size))
        permuted = np.abs(np.mean(signs * differences, axis=1))
        extreme += int(np.sum(permuted >= observed - 1e-15))
    return (extreme + 1.0) / (replicates + 1.0)


def holm_adjust(p_values: Sequence[float]) -> np.ndarray:
    values = _one_dimensional(p_values, "p-values")
    if np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("p-values must lie in [0, 1]")
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    count = values.size
    for rank, index in enumerate(order):
        candidate = min(1.0, (count - rank) * values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted
