from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d016_classical_compute_preflight.yaml"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_d016_authorizes_one_synthetic_preflight_only() -> None:
    config = _config()
    assert config["decision_id"] == "D016-C"
    assert config["status"] in {
        "accepted_clean_source_synthetic_preflight_pending",
        "completed_synthetic_compute_admission_pass",
        "terminal_synthetic_compute_admission_stop",
    }
    authority = config["authority"]
    assert authority["preflight_execution_authorized"] in {True, False}
    assert authority["authorized_preflight_attempts"] == 1
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
        assert authority[key] is False


def test_d016_locks_local_compute_and_reporting_boundary() -> None:
    config = _config()
    assert config["locks"]["allowed_data_scope"] == "synthetic"
    assert config["locks"]["development_rows_read"] == 0
    assert config["locks"]["calibration_rows_read"] == 0
    assert config["locks"]["final_test_rows_read"] == 0
    assert config["locks"]["gate6_runs"] == 0
    assert config["ceilings"]["branch_cpu_core_hours"] == 250.0
    assert config["ceilings"]["branch_wall_clock_days"] == 5.0
    assert config["ceilings"]["max_gpu_hours"] == 0.0
    assert config["reporting"]["preflight_figure"] == "RFIG-033"
    assert "Synthetic compute-admission evidence only" in config["reporting"]["claim_boundary"]


def test_d016_docs_are_registered() -> None:
    required = {
        "docs/post_gate5_d016_classical_compute_preflight.md": "D016-C",
        "research_protocol.md": "D016-C",
        "docs/decision_log.md": "D016-C",
        "README.md": "D016-C",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text


def test_d016_result_if_present_is_synthetic_only() -> None:
    result_path = ROOT / "data/processed/reporting/post_gate5_d016_classical_preflight.json"
    if not result_path.is_file():
        pytest.skip("D016 preflight result not reached yet")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["decision_id"] == "D016-C"
    assert result["status"] in {"PASS", "STOP"}
    integrity = result["integrity"]
    for field in (
        "development_rows_read",
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs_submitted",
        "gate6_runs",
    ):
        assert integrity[field] == 0
    assert result["benchmark"]["gpu_hours"] == 0.0
    assert result["admission"]["checks"]["gpu_hours"]["observed"] == 0.0
