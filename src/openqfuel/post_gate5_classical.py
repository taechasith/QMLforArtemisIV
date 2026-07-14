"""D015-C synthetic-only CRES/CSAFE scaffolds.

The functions in this module are intentionally array-only utilities. They do
not load project payloads, fit repository data, submit hardware jobs, or open
Gate 6. They support synthetic validation for the D014-C classical-first freeze.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from .gate4 import FinalTestAccessError


LOCKED_D015_SCOPES = {
    "development",
    "calibration",
    "uncertainty_calibration",
    "final_test",
    "in_distribution_final_test",
    "out_of_distribution_final_test",
    "gate6",
}


@dataclass(frozen=True)
class ResidualTarget:
    """Explicit high-minus-low residual target used by CRES scaffolds."""

    residual: np.ndarray
    reconstructed: np.ndarray


@dataclass(frozen=True)
class ResidualCostMetrics:
    """Synthetic residual-cost metrics for one held-out fold."""

    rmse: float
    nrmse: float
    mae: float
    tail_abs_error_q90: float
    tail_abs_error_q95: float


@dataclass(frozen=True)
class SafetyMetrics:
    """Synthetic CSAFE feasibility and safety-filter metrics."""

    brier: float
    auroc: float
    recall: float
    precision: float
    false_negative_rate: float
    false_positive_rate: float
    expected_calibration_error: float
    intervention_rate: float
    threshold: float


@dataclass(frozen=True)
class RecallFirstSafetyScore:
    """D021-C synthetic CSAFE-RF score with recall-first ranking fields."""

    model_id: str
    model_complexity: int
    metrics: SafetyMetrics
    selected: bool = False

    def as_row(self) -> dict[str, str]:
        return {
            "model_id": self.model_id,
            "model_complexity": str(self.model_complexity),
            "recall": f"{self.metrics.recall:.12g}",
            "false_negative_rate": f"{self.metrics.false_negative_rate:.12g}",
            "brier": f"{self.metrics.brier:.12g}",
            "precision": f"{self.metrics.precision:.12g}",
            "false_positive_rate": f"{self.metrics.false_positive_rate:.12g}",
            "intervention_rate": f"{self.metrics.intervention_rate:.12g}",
            "threshold": f"{self.metrics.threshold:.12g}",
            "selected": str(self.selected).lower(),
        }


@dataclass(frozen=True)
class InventionReadinessLabel:
    """Label a result for future QML invention without authorizing rescue."""

    result_id: str
    observed_result: str
    useful_signal_for_invention: str
    prohibited_use: str
    required_future_control: str
    claim_boundary: str

    def as_row(self) -> dict[str, str]:
        return {
            "result_id": self.result_id,
            "observed_result": self.observed_result,
            "useful_signal_for_invention": self.useful_signal_for_invention,
            "prohibited_use": self.prohibited_use,
            "required_future_control": self.required_future_control,
            "claim_boundary": self.claim_boundary,
        }


def assert_d015_scope(
    config: Mapping[str, Any],
    *,
    action: str,
    data_scope: str,
) -> None:
    """Enforce D015-C implementation/synthetic-validation-only authority."""

    if data_scope in LOCKED_D015_SCOPES:
        raise FinalTestAccessError(f"{data_scope} is not authorized by D015-C")
    if data_scope != "synthetic":
        raise PermissionError("D015-C allows synthetic arrays only")
    authority = config.get("authority", config)
    if action == "implementation" and authority.get("implementation_authorized"):
        return
    if action == "synthetic_validation" and authority.get(
        "synthetic_validation_authorized"
    ):
        return
    raise PermissionError(f"D015-C does not authorize {action}")


def assert_d021_scope(
    config: Mapping[str, Any],
    *,
    action: str,
    data_scope: str,
) -> None:
    """Enforce D021-C implementation/synthetic-validation-only authority."""

    if data_scope in LOCKED_D015_SCOPES:
        raise FinalTestAccessError(f"{data_scope} is not authorized by D021-C")
    if data_scope != "synthetic":
        raise PermissionError("D021-C allows synthetic arrays only")
    authority = config.get("authority", config)
    if action == "implementation" and authority.get("implementation_authorized"):
        return
    if action == "synthetic_validation" and authority.get(
        "synthetic_validation_authorized"
    ):
        return
    raise PermissionError(f"D021-C does not authorize {action}")


def _vector(values: Sequence[float], *, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def residual_target(
    high_fidelity_target: Sequence[float],
    low_fidelity_baseline: Sequence[float],
) -> ResidualTarget:
    """Return explicit high-minus-low residuals and reconstructed target."""

    high = _vector(high_fidelity_target, name="high_fidelity_target")
    low = _vector(low_fidelity_baseline, name="low_fidelity_baseline")
    if high.shape != low.shape:
        raise ValueError("Residual target arrays must have identical shape")
    residual = high - low
    return ResidualTarget(residual=residual, reconstructed=low + residual)


def residual_cost_metrics(
    truth: Sequence[float],
    prediction: Sequence[float],
    *,
    denominator: float | None = None,
) -> ResidualCostMetrics:
    """Compute D014-C residual-cost metrics on synthetic held-out arrays."""

    y_true = _vector(truth, name="truth")
    y_pred = _vector(prediction, name="prediction")
    if y_true.shape != y_pred.shape:
        raise ValueError("Residual metric arrays must have identical shape")
    errors = y_pred - y_true
    squared = errors * errors
    rmse = float(np.sqrt(np.mean(squared)))
    scale = float(np.std(y_true, ddof=1)) if denominator is None else float(denominator)
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("Residual NRMSE denominator must be positive")
    absolute = np.abs(errors)
    return ResidualCostMetrics(
        rmse=rmse,
        nrmse=rmse / scale,
        mae=float(np.mean(absolute)),
        tail_abs_error_q90=float(np.quantile(absolute, 0.90)),
        tail_abs_error_q95=float(np.quantile(absolute, 0.95)),
    )


def _binary_labels(values: Sequence[int]) -> np.ndarray:
    labels = np.asarray(values, dtype=int)
    if labels.ndim != 1 or labels.size == 0:
        raise ValueError("Binary labels must be a non-empty one-dimensional array")
    if not np.isin(labels, [0, 1]).all():
        raise ValueError("Binary labels must contain only 0/1 values")
    return labels


def _probabilities(values: Sequence[float]) -> np.ndarray:
    probabilities = _vector(values, name="probabilities")
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("Probabilities must be within [0, 1]")
    return probabilities


def select_safety_threshold(
    training_labels: Sequence[int],
    training_probabilities: Sequence[float],
    *,
    minimum_recall: float = 0.95,
    maximum_intervention_rate: float = 1.0,
) -> float:
    """Select a synthetic threshold from training arrays only.

    The rule chooses the highest threshold satisfying the requested recall and
    intervention-rate bounds, preferring less intervention after recall is met.
    """

    labels = _binary_labels(training_labels)
    probabilities = _probabilities(training_probabilities)
    if labels.shape != probabilities.shape:
        raise ValueError("Threshold-selection arrays must have identical shape")
    if not 0.0 <= minimum_recall <= 1.0:
        raise ValueError("minimum_recall must be in [0, 1]")
    if not 0.0 <= maximum_intervention_rate <= 1.0:
        raise ValueError("maximum_intervention_rate must be in [0, 1]")
    candidates = np.unique(np.r_[0.0, probabilities, 1.0])
    best: tuple[float, float, float] | None = None
    for threshold in candidates:
        predicted = probabilities >= threshold
        positives = labels == 1
        true_positive = int(np.sum(predicted & positives))
        false_negative = int(np.sum(~predicted & positives))
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        intervention_rate = float(np.mean(predicted))
        if recall >= minimum_recall and intervention_rate <= maximum_intervention_rate:
            rank = (intervention_rate, -float(threshold), -recall)
            if best is None or rank < best:
                best = rank
    if best is None:
        raise ValueError("No threshold satisfies the synthetic safety constraints")
    return float(-best[1])


def safety_metrics(
    labels: Sequence[int],
    probabilities: Sequence[float],
    *,
    threshold: float,
    calibration_bins: int = 10,
) -> SafetyMetrics:
    """Compute D014-C safety metrics on synthetic held-out arrays."""

    y_true = _binary_labels(labels)
    prob = _probabilities(probabilities)
    if y_true.shape != prob.shape:
        raise ValueError("Safety metric arrays must have identical shape")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Safety threshold must be in [0, 1]")
    if calibration_bins <= 0:
        raise ValueError("calibration_bins must be positive")
    predicted = prob >= threshold
    positives = y_true == 1
    negatives = ~positives
    tp = int(np.sum(predicted & positives))
    fp = int(np.sum(predicted & negatives))
    fn = int(np.sum(~predicted & positives))
    tn = int(np.sum(~predicted & negatives))
    recall = tp / (tp + fn) if tp + fn else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    false_negative_rate = fn / (tp + fn) if tp + fn else 0.0
    false_positive_rate = fp / (fp + tn) if fp + tn else 0.0
    return SafetyMetrics(
        brier=float(np.mean((prob - y_true) ** 2)),
        auroc=_auroc(y_true, prob),
        recall=float(recall),
        precision=float(precision),
        false_negative_rate=float(false_negative_rate),
        false_positive_rate=float(false_positive_rate),
        expected_calibration_error=_expected_calibration_error(
            y_true, prob, calibration_bins
        ),
        intervention_rate=float(np.mean(predicted)),
        threshold=float(threshold),
    )


def recall_first_safety_score(
    *,
    model_id: str,
    model_complexity: int,
    labels: Sequence[int],
    probabilities: Sequence[float],
    threshold: float,
    calibration_bins: int = 10,
) -> RecallFirstSafetyScore:
    """Score one synthetic CSAFE-RF candidate without selecting thresholds."""

    if not model_id.strip():
        raise ValueError("model_id is required")
    if model_complexity < 0:
        raise ValueError("model_complexity must be non-negative")
    metrics = safety_metrics(
        labels,
        probabilities,
        threshold=threshold,
        calibration_bins=calibration_bins,
    )
    return RecallFirstSafetyScore(
        model_id=model_id,
        model_complexity=int(model_complexity),
        metrics=metrics,
    )


def select_recall_first_candidate(
    scores: Sequence[RecallFirstSafetyScore],
) -> RecallFirstSafetyScore:
    """Select by D020-C recall-first order on synthetic candidate scores."""

    if not scores:
        raise ValueError("At least one recall-first score is required")
    selected = min(
        scores,
        key=lambda score: (
            -score.metrics.recall,
            score.metrics.false_negative_rate,
            score.metrics.brier,
            score.model_complexity,
            score.model_id,
        ),
    )
    return RecallFirstSafetyScore(
        model_id=selected.model_id,
        model_complexity=selected.model_complexity,
        metrics=selected.metrics,
        selected=True,
    )


def _auroc(labels: np.ndarray, probabilities: np.ndarray) -> float:
    positives = probabilities[labels == 1]
    negatives = probabilities[labels == 0]
    if positives.size == 0 or negatives.size == 0:
        raise ValueError("AUROC requires at least one positive and one negative")
    wins = 0.0
    for value in positives:
        wins += float(np.sum(value > negatives))
        wins += 0.5 * float(np.sum(value == negatives))
    return wins / float(positives.size * negatives.size)


def _expected_calibration_error(
    labels: np.ndarray, probabilities: np.ndarray, bins: int
) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = 0.0
    for index in range(bins):
        left = edges[index]
        right = edges[index + 1]
        if index == bins - 1:
            mask = (probabilities >= left) & (probabilities <= right)
        else:
            mask = (probabilities >= left) & (probabilities < right)
        if not np.any(mask):
            continue
        confidence = float(np.mean(probabilities[mask]))
        accuracy = float(np.mean(labels[mask]))
        total += float(np.mean(mask)) * abs(confidence - accuracy)
    return total


def invention_readiness_label(
    *,
    result_id: str,
    observed_result: str,
    useful_signal_for_invention: str,
    prohibited_use: str,
    required_future_control: str,
    claim_boundary: str,
) -> InventionReadinessLabel:
    """Create a validated future-invention label."""

    values = {
        "result_id": result_id,
        "observed_result": observed_result,
        "useful_signal_for_invention": useful_signal_for_invention,
        "prohibited_use": prohibited_use,
        "required_future_control": required_future_control,
        "claim_boundary": claim_boundary,
    }
    for key, value in values.items():
        if not str(value).strip():
            raise ValueError(f"Invention-readiness label missing {key}")
    if "rescue" not in prohibited_use.lower():
        raise ValueError("prohibited_use must explicitly block rescue use")
    return InventionReadinessLabel(**values)
