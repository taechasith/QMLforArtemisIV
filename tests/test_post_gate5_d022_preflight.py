from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d022_recall_first_preflight.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d022_recall_first_preflight.json"


def test_d022_preflight_authority_is_synthetic_only() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["decision_id"] == "D022-C"
    assert config["authority"]["preflight_execution_authorized"] in {True, False}
    assert config["locks"]["allowed_data_scope"] == "synthetic"
    for key in (
        "development_data_fitting_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "threshold_application_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate5_reinterpretation_authorized",
        "qml_invention_claim_authorized",
        "quantum_advantage_claim_authorized",
        "mission_loop_authorized",
        "gate6_authorized",
    ):
        assert config["authority"][key] is False


def test_d022_result_if_present_keeps_locked_scopes_zero() -> None:
    if not RESULT.exists():
        pytest.skip("D022-C result not reached yet")
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["decision_id"] == "D022-C"
    assert result["status"] in {"PASS", "STOP"}
    assert result["integrity"]["development_rows_read"] == 0
    assert result["integrity"]["calibration_rows_read"] == 0
    assert result["integrity"]["final_test_rows_read"] == 0
    assert result["integrity"]["gate6_runs"] == 0
    assert result["admission"]["checks"]["gpu_hours"]["observed"] == 0.0


def test_d022_docs_are_registered() -> None:
    required = {
        "docs/post_gate5_d022_recall_first_preflight.md": "D022-C authorizes exactly one",
        "research_protocol.md": "D022-C",
        "README.md": "D022-C",
        "docs/decision_log.md": "D022-C",
        "docs/research_execution_map.md": "D022-C",
        "docs/computational_methodology.md": "D022-C",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
