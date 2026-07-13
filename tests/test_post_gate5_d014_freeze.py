from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d014_classical_first_freeze.yaml"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_d014c_is_freeze_only_and_authorizes_no_execution() -> None:
    config = _config()
    assert config["decision_id"] == "D014-C"
    assert config["status"] == "accepted_freeze_proposal_no_execution"
    authority = config["authority"]
    assert authority["freeze_proposal_authorized"] is True
    for key in (
        "implementation_authorized",
        "synthetic_validation_authorized",
        "development_data_fitting_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "refit_authorized",
        "rerank_authorized",
        "retry_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate5_reinterpretation_authorized",
        "gate6_authorized",
    ):
        assert authority[key] is False
    assert "D015" in authority["next_required_decision"]


def test_d014c_locks_residual_and_safety_tracks_for_future_controls() -> None:
    config = _config()
    residual = config["locked_tracks"]["residual_cost_hardening"]
    safety = config["locked_tracks"]["safety_filter_hardening"]
    assert residual["track_id"] == "CRES"
    assert residual["primary_metric"] == "pooled out-of-fold NRMSE"
    assert "C06-T17 frozen physics residual" in residual["required_controls"]
    assert "A02 exact classical RBF on identical fold-local PCA rows" in (
        residual["required_controls"]
    )
    assert safety["track_id"] == "CSAFE"
    assert safety["primary_metric"] == "pooled out-of-fold Brier score"
    assert "C02-T02 strongest D011 feasibility comparator" in (
        safety["required_controls"]
    )
    assert "conformal or quantile safety threshold" in safety["required_controls"]


def test_d014c_requires_future_compute_admission_before_data_fitting() -> None:
    config = _config()
    compute = config["compute_admission_plan"]
    assert compute["required_before_data_fitting"] is True
    assert compute["ceilings"]["cpu_core_hours"] == 250.0
    assert compute["ceilings"]["wall_clock_days"] == 5.0
    assert compute["ceilings"]["gpu_hours"] == 0.0
    assert "do not credit cache reuse" in compute["accounting_rule"]


def test_d014c_docs_are_registered_and_gate6_locked() -> None:
    required = {
        "docs/post_gate5_d014_classical_first_freeze.md": (
            "Freeze proposal accepted; no implementation or experiment authorized"
        ),
        "configs/post_gate5_d014_classical_first_freeze.yaml": (
            "accepted_freeze_proposal_no_execution"
        ),
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
