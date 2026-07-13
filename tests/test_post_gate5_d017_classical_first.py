from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d017_classical_first_development.yaml"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_d017_authorizes_development_only_campaign() -> None:
    config = _config()
    assert config["decision_id"] == "D017-C"
    assert config["status"] in {
        "accepted_development_only_classical_first_campaign_pending",
        "completed_development_only_classical_first_campaign",
        "terminal_development_only_classical_first_failure",
    }
    authority = config["authority"]
    assert authority["campaign_execution_authorized"] in {True, False}
    assert authority["authorized_campaigns"] == 1
    assert authority["development_data_fitting_authorized"] is True
    for key in (
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


def test_d017_freezes_campaign_shape_and_outputs() -> None:
    config = _config()
    campaign = config["campaign"]
    assert campaign["fold_count"] == 5
    assert campaign["seed_count"] == 20
    assert campaign["training_rows_per_fold"] == 1024
    assert campaign["figures"] == {"cres": "RFIG-034", "csafe": "RFIG-035"}
    assert "a02_exact_rbf_residual" in config["models"]["cres"]
    assert "a02_exact_rbf_feasibility" in config["models"]["csafe"]
    assert "campaign_summary.json" in ";".join(config["reporting"]["result_files"])


def test_d017_docs_are_registered() -> None:
    required = {
        "docs/post_gate5_d017_classical_first_development.md": "D017-C",
        "research_protocol.md": "D017-C",
        "docs/decision_log.md": "D017-C",
        "README.md": "D017-C",
        "docs/research_execution_map.md": "D019-C discussion opened",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text


def test_d017_result_if_present_is_development_only() -> None:
    result = (
        ROOT
        / "data/processed/reporting/post_gate5_d017_classical_first/campaign_summary.json"
    )
    if not result.is_file():
        pytest.skip("D017 result not reached yet")
    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["decision_id"] == "D017-C"
    assert payload["status"] == "complete"
    assert payload["development_rows_read"] == 39000
    assert payload["calibration_rows_read"] == 0
    assert payload["final_test_rows_read"] == 0
    assert payload["hardware_jobs_submitted"] == 0
    assert payload["gate6_runs"] == 0
    assert payload["cres_best_mean_nrmse_model"] == "ridge_residual"
    assert payload["csafe_best_mean_brier_model"] == "class_weighted_tree"
