from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d023_recall_first_development.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d023_recall_first_development.json"


def test_d023_authority_is_reporting_audit_only() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["decision_id"] == "D023-C"
    assert config["authority"]["reporting_audit_authorized"] is True
    for key in (
        "development_data_fitting_authorized",
        "new_model_fit_authorized",
        "threshold_application_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate5_reinterpretation_authorized",
        "qml_invention_claim_authorized",
        "quantum_advantage_claim_authorized",
        "mission_loop_authorized",
        "gate6_authorized",
    ):
        assert config["authority"][key] is False


def test_d023_result_records_recall_first_selection_without_refit() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["decision_id"] == "D023-C"
    assert result["official_status"] == "DEVELOPMENT_AUDIT_COMPLETE"
    assert result["selected_model_id"] == "calibrated_logistic"
    assert result["selected_mean_recall"] > 0.8
    assert result["new_model_fits"] == 0
    assert result["threshold_applications_to_real_data"] == 0
    assert result["calibration_rows_read"] == 0
    assert result["final_test_rows_read"] == 0
    assert result["gate6_runs"] == 0


def test_d023_docs_are_registered() -> None:
    required = {
        "docs/post_gate5_d023_recall_first_development.md": "D023-C applies the frozen",
        "research_protocol.md": "D023-C",
        "README.md": "D023-C",
        "docs/decision_log.md": "D023-C",
        "docs/research_execution_map.md": "D032-C release-candidate manifest READY",
        "docs/computational_methodology.md": "D023-C",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
