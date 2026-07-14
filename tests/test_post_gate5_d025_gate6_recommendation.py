from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_d025_config_is_closure_only() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d025_gate6_recommendation.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D025-C"
    assert config["scope"]["closure_report_only"] is True
    assert config["scope"]["gate6_authorized"] is False
    assert config["scope"]["qml_mission_experiment_authorized"] is False
    for key, value in config["scope"].items():
        if key.endswith("_authorized"):
            assert value is False


def test_d025_result_recommends_no_qml_gate6_candidate() -> None:
    result = json.loads(
        (
            ROOT
            / "data/processed/reporting/post_gate5_d025_gate6_recommendation.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D025-C"
    assert result["official_status"] == "GATE5_CLOSED_NO_QML_GATE6_CANDIDATE"
    assert result["gate6_authorized"] is False
    assert result["qml_gate6_candidate"] is False
    assert result["gate5_qualified_regimes"] == 0
    assert result["q01_mean_nrmse"] > result["c06_mean_nrmse"]
    assert result["q01b_relative_gap_vs_c06"] > 90
    assert result["fqk_mean_recall"] < 0.2
    assert result["recall_first_recall"] > 0.8
    for key in (
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "mission_loop_runs",
        "gate6_runs",
    ):
        assert result[key] == 0


def test_d025_docs_are_registered() -> None:
    expected = {
        "docs/gate5_closure_gate6_recommendation.md": "D025-C closes",
        "research_protocol.md": "D025-C",
        "README.md": "D025-C",
        "docs/decision_log.md": "D025-C",
        "docs/research_execution_map.md": "D025-C",
        "docs/computational_methodology.md": "D025-C",
        "docs/qml_invention_readiness_ledger.md": "D025-C",
    }
    for relative, needle in expected.items():
        assert needle in (ROOT / relative).read_text(encoding="utf-8")
