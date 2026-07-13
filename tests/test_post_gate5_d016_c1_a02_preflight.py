from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d016_c1_a02_compute_preflight.yaml"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_d016_c1_authorizes_only_missing_a02_synthetic_preflight() -> None:
    config = _config()
    assert config["decision_id"] == "D016-C1"
    assert config["authority"]["corrected_decision"] == "D016-C"
    assert "A02 exact classical RBF" in config["authority"]["corrected_issue"]
    assert config["authority"]["authorized_preflight_attempts"] == 1
    for key in (
        "development_data_fitting_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "refit_authorized",
        "rerank_authorized",
        "retry_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate5_reinterpretation_authorized",
        "qml_invention_claim_authorized",
        "quantum_advantage_claim_authorized",
        "gate6_authorized",
    ):
        assert config["authority"][key] is False


def test_d016_c1_result_if_present_is_synthetic_only() -> None:
    path = ROOT / "data/processed/reporting/post_gate5_d016_c1_a02_preflight.json"
    if not path.is_file():
        pytest.skip("D016-C1 result not reached yet")
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["decision_id"] == "D016-C1"
    assert result["corrects_decision_id"] == "D016-C"
    assert result["status"] in {"PASS", "STOP"}
    for field in (
        "development_rows_read",
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs_submitted",
        "gate6_runs",
    ):
        assert result["integrity"][field] == 0
