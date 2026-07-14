from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from openqfuel.gate4 import FinalTestAccessError
from openqfuel.post_gate5_classical import (
    assert_d021_scope,
    recall_first_safety_score,
    select_recall_first_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d021_recall_first_synthetic.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d021_recall_first_synthetic.json"


def test_d021_scope_allows_only_synthetic_implementation_and_validation() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert_d021_scope(config, action="implementation", data_scope="synthetic")
    assert_d021_scope(config, action="synthetic_validation", data_scope="synthetic")
    with pytest.raises(FinalTestAccessError):
        assert_d021_scope(config, action="synthetic_validation", data_scope="development")
    with pytest.raises(FinalTestAccessError):
        assert_d021_scope(config, action="implementation", data_scope="gate6")
    with pytest.raises(PermissionError, match="does not authorize"):
        assert_d021_scope(config, action="development_fit", data_scope="synthetic")


def test_recall_first_selection_prioritizes_recall_before_brier() -> None:
    labels = np.asarray([1, 1, 1, 1, 0, 0, 0, 0])
    high_recall = recall_first_safety_score(
        model_id="high_recall",
        model_complexity=2,
        labels=labels,
        probabilities=[0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2],
        threshold=0.6,
    )
    low_brier_low_recall = recall_first_safety_score(
        model_id="low_brier_low_recall",
        model_complexity=1,
        labels=labels,
        probabilities=[0.95, 0.78, 0.76, 0.74, 0.1, 0.08, 0.05, 0.03],
        threshold=0.8,
    )
    assert low_brier_low_recall.metrics.brier < high_recall.metrics.brier
    selected = select_recall_first_candidate([low_brier_low_recall, high_recall])
    assert selected.model_id == "high_recall"
    assert selected.selected is True


def test_d021_result_records_synthetic_pass_and_zero_locked_counters() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["decision_id"] == "D021-C"
    assert result["official_status"] == "SYNTHETIC_VALIDATION_PASS"
    assert result["selected_model_id"] == "synthetic_recall_first_logistic"
    assert result["selected_recall"] > 0.0
    assert result["development_rows_read"] == 0
    assert result["calibration_rows_read"] == 0
    assert result["final_test_rows_read"] == 0
    assert result["gate6_runs"] == 0


def test_d021_docs_are_registered() -> None:
    required = {
        "docs/post_gate5_d021_recall_first_synthetic.md": "D021-C implements CSAFE-RF",
        "research_protocol.md": "D021-C implements and validates CSAFE-RF",
        "README.md": "D021-C implements and validates CSAFE-RF",
        "docs/decision_log.md": "D021-C completed",
        "docs/research_execution_map.md": "D022-C clean-source synthetic preflight pending",
        "docs/computational_methodology.md": "D021-C recall-first synthetic validation",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
