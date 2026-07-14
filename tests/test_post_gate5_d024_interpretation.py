from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_d024_config_is_interpretation_only() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d024_recall_first_interpretation.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D024-C"
    assert config["scope"]["interpretation_only"] is True
    assert config["scope"]["reporting_only"] is True
    for key, value in config["scope"].items():
        if key.endswith("_authorized"):
            assert value is False
    assert "Gate 6" in config["claim_boundary"]


def test_d024_result_closes_recall_first_branch_without_new_authority() -> None:
    result = json.loads(
        (
            ROOT
            / "data/processed/reporting/post_gate5_d024_recall_first_interpretation.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D024-C"
    assert result["official_status"] == "INTERPRETATION_COMPLETE_NO_ADVANCE"
    assert result["selected_model_id"] == "calibrated_logistic"
    assert result["selected_mean_recall"] > 0.8
    assert "future-useful recall signal" in result["core_result"]
    assert "future-work" in result["qml_lesson"]
    for key in (
        "new_model_fits",
        "threshold_applications_to_real_data",
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "gate6_runs",
    ):
        assert result[key] == 0


def test_d024_docs_are_registered() -> None:
    expected = {
        "docs/post_gate5_d024_recall_first_interpretation.md": "D024-C interprets",
        "research_protocol.md": "D024-C",
        "README.md": "D024-C",
        "docs/decision_log.md": "D024-C",
        "docs/research_execution_map.md": "D024-C",
        "docs/computational_methodology.md": "D024-C",
    }
    for relative, needle in expected.items():
        assert needle in (ROOT / relative).read_text(encoding="utf-8")
