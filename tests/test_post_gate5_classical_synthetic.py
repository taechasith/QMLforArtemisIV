from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from openqfuel.gate4 import FinalTestAccessError
from openqfuel.post_gate5_classical import (
    assert_d015_scope,
    invention_readiness_label,
    recall_first_safety_score,
    residual_cost_metrics,
    residual_target,
    safety_metrics,
    select_recall_first_candidate,
    select_safety_threshold,
)


ROOT = Path(__file__).resolve().parents[1]


def _d015_config() -> dict:
    return yaml.safe_load(
        (
            ROOT / "configs/post_gate5_d015_implementation_synthetic_validation.yaml"
        ).read_text(encoding="utf-8")
    )


def test_d015_scope_allows_only_synthetic_implementation_and_validation() -> None:
    config = _d015_config()
    assert_d015_scope(config, action="implementation", data_scope="synthetic")
    assert_d015_scope(config, action="synthetic_validation", data_scope="synthetic")
    with pytest.raises(FinalTestAccessError):
        assert_d015_scope(config, action="synthetic_validation", data_scope="gate6")
    with pytest.raises(FinalTestAccessError):
        assert_d015_scope(config, action="implementation", data_scope="development")
    with pytest.raises(PermissionError, match="does not authorize"):
        assert_d015_scope(config, action="development_fit", data_scope="synthetic")


def test_residual_target_equation_is_explicit_and_reconstructs_truth() -> None:
    high = np.asarray([10.0, 12.5, 9.0, 14.0])
    low = np.asarray([9.5, 11.0, 9.25, 13.0])
    target = residual_target(high, low)
    np.testing.assert_allclose(target.residual, [0.5, 1.5, -0.25, 1.0])
    np.testing.assert_allclose(target.reconstructed, high)


def test_residual_cost_metrics_use_pooled_synthetic_arrays() -> None:
    truth = np.asarray([10.0, 11.0, 12.0, 13.0, 14.0])
    prediction = np.asarray([10.2, 10.8, 12.4, 12.5, 14.1])
    metrics = residual_cost_metrics(truth, prediction, denominator=2.0)
    expected_rmse = float(np.sqrt(np.mean((prediction - truth) ** 2)))
    assert metrics.rmse == pytest.approx(expected_rmse)
    assert metrics.nrmse == pytest.approx(expected_rmse / 2.0)
    assert metrics.mae == pytest.approx(float(np.mean(np.abs(prediction - truth))))
    assert metrics.tail_abs_error_q95 >= metrics.tail_abs_error_q90
    with pytest.raises(ValueError, match="denominator"):
        residual_cost_metrics(truth, prediction, denominator=0.0)


def test_safety_threshold_uses_training_arrays_then_applies_to_heldout() -> None:
    train_labels = np.asarray([1, 1, 1, 0, 0, 0])
    train_prob = np.asarray([0.95, 0.85, 0.60, 0.55, 0.30, 0.10])
    threshold = select_safety_threshold(
        train_labels,
        train_prob,
        minimum_recall=1.0,
        maximum_intervention_rate=4 / 6,
    )
    assert threshold == pytest.approx(0.60)

    heldout_labels = np.asarray([1, 1, 0, 0])
    heldout_prob = np.asarray([0.90, 0.50, 0.40, 0.20])
    metrics = safety_metrics(heldout_labels, heldout_prob, threshold=threshold)
    assert metrics.brier == pytest.approx(
        float(np.mean((heldout_prob - heldout_labels) ** 2))
    )
    assert metrics.auroc == pytest.approx(1.0)
    assert metrics.recall == pytest.approx(0.5)
    assert metrics.false_negative_rate == pytest.approx(0.5)
    assert 0.0 <= metrics.expected_calibration_error <= 1.0
    assert metrics.threshold == threshold


def test_safety_metrics_reject_invalid_or_single_class_synthetic_inputs() -> None:
    with pytest.raises(ValueError, match="0/1"):
        safety_metrics([0, 2], [0.1, 0.9], threshold=0.5)
    with pytest.raises(ValueError, match="AUROC"):
        safety_metrics([1, 1], [0.2, 0.8], threshold=0.5)


def test_invention_readiness_label_requires_prohibited_rescue_use() -> None:
    label = invention_readiness_label(
        result_id="SYN-CRES-001",
        observed_result="synthetic metric passed shape checks",
        useful_signal_for_invention="residual diagnostics can rank future controls",
        prohibited_use="Do not use this as post-outcome rescue for P001.",
        required_future_control="C06 and A02",
        claim_boundary="synthetic validation only",
    )
    assert label.as_row()["result_id"] == "SYN-CRES-001"
    with pytest.raises(ValueError, match="rescue"):
        invention_readiness_label(
            result_id="bad",
            observed_result="synthetic",
            useful_signal_for_invention="none",
            prohibited_use="do not use",
            required_future_control="C06",
            claim_boundary="synthetic validation only",
        )


def test_recall_first_candidate_tie_breaks_after_recall_and_fnr() -> None:
    labels = np.asarray([1, 1, 0, 0])
    simple = recall_first_safety_score(
        model_id="simple",
        model_complexity=1,
        labels=labels,
        probabilities=[0.9, 0.8, 0.2, 0.1],
        threshold=0.5,
    )
    complex_model = recall_first_safety_score(
        model_id="complex",
        model_complexity=3,
        labels=labels,
        probabilities=[0.9, 0.8, 0.2, 0.1],
        threshold=0.5,
    )
    selected = select_recall_first_candidate([complex_model, simple])
    assert selected.model_id == "simple"
