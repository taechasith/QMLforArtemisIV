from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d019_safety_redesign.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d019_safety_redesign.json"


def test_d019_is_discussion_only() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["decision_id"] == "D019-C"
    assert config["outcome"]["official_status"] == "DISCUSSION_ONLY"
    assert config["authority"]["discussion_authorized"] is True
    for key in (
        "experiment_authorized",
        "implementation_authorized",
        "development_data_fitting_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "refit_authorized",
        "rerank_authorized",
        "retry_authorized",
        "threshold_change_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate5_reinterpretation_authorized",
        "qml_invention_claim_authorized",
        "quantum_advantage_claim_authorized",
        "mission_loop_authorized",
        "gate6_authorized",
    ):
        assert config["authority"][key] is False


def test_d019_records_safety_objective_diagnosis_without_rescue() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["decision_id"] == "D019-C"
    assert result["official_status"] == "DISCUSSION_ONLY"
    assert result["active_frozen_selection_model"] == "class_weighted_tree"
    assert result["active_frozen_selection_mean_recall"] == 0.013889174500238285
    assert result["future_only_signal_model"] == "calibrated_logistic"
    assert result["future_only_signal_mean_recall"] == 0.8042533959907271
    assert result["calibration_rows_read"] == 0
    assert result["final_test_rows_read"] == 0
    assert result["gate6_runs"] == 0
    assert "Future-only discussion" in result["claim_boundary"]


def test_d019_docs_are_registered() -> None:
    required = {
        "docs/post_gate5_d019_safety_redesign.md": "D019-C opens a future-only",
        "research_protocol.md": "D019-C opens a future-only safety-objective",
        "README.md": "D019-C opens a future-only safety-objective",
        "docs/decision_log.md": "D019-C opened",
        "docs/research_execution_map.md": "D031-C final claim/release review READY",
        "docs/computational_methodology.md": "D019-C safety-objective redesign",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
