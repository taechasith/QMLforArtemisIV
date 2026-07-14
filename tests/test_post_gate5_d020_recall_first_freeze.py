from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d020_recall_first_freeze.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d020_recall_first_freeze.json"


def test_d020_is_freeze_proposal_only() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["decision_id"] == "D020-C"
    assert config["outcome"]["official_status"] == "FREEZE_PROPOSAL_ONLY"
    assert config["authority"]["freeze_proposal_authorized"] is True
    for key in (
        "implementation_authorized",
        "experiment_authorized",
        "development_data_fitting_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "threshold_application_authorized",
        "refit_authorized",
        "rerank_authorized",
        "retry_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate5_reinterpretation_authorized",
        "qml_invention_claim_authorized",
        "quantum_advantage_claim_authorized",
        "mission_loop_authorized",
        "gate6_authorized",
    ):
        assert config["authority"][key] is False


def test_d020_freezes_recall_first_rule_without_data_access() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["decision_id"] == "D020-C"
    assert result["official_status"] == "FREEZE_PROPOSAL_ONLY"
    assert result["track_id"] == "CSAFE-RF"
    assert result["selection_order"][0] == "mean development unsafe-case recall"
    assert result["development_rows_read"] == 0
    assert result["calibration_rows_read"] == 0
    assert result["final_test_rows_read"] == 0
    assert result["gate6_runs"] == 0
    assert "training folds only" in result["threshold_policy"]


def test_d020_docs_are_registered() -> None:
    required = {
        "docs/post_gate5_d020_recall_first_freeze.md": "D020-C freezes a future",
        "research_protocol.md": "D020-C freezes a future CSAFE-RF",
        "README.md": "D020-C freezes a future CSAFE-RF",
        "docs/decision_log.md": "D020-C accepted",
        "docs/research_execution_map.md": "D032-C release-candidate manifest READY",
        "docs/computational_methodology.md": "D020-C recall-first safety freeze",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
