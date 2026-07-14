from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d018_interpretation.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d018_interpretation.json"


def test_d018_records_no_advance_interpretation() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["decision_id"] == "D018-C"
    assert config["outcome"]["official_status"] == "NO_ADVANCE"
    assert config["interpretation"]["cres"]["status"] == (
        "development_baseline_only_not_qualifying"
    )
    assert config["interpretation"]["csafe"]["status"] == (
        "failed_safety_utility_under_frozen_selection"
    )
    assert config["authority"]["experiment_authorized"] is False
    assert config["authority"]["calibration_access_authorized"] is False
    assert config["authority"]["final_test_access_authorized"] is False
    assert config["authority"]["gate6_authorized"] is False


def test_d018_result_keeps_locked_scopes_closed() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["decision_id"] == "D018-C"
    assert result["official_status"] == "NO_ADVANCE"
    assert result["development_rows_interpreted"] == 39000
    assert result["calibration_rows_read"] == 0
    assert result["final_test_rows_read"] == 0
    assert result["gate6_runs"] == 0
    assert result["csafe_best_brier_mean_recall"] == 0.013889174500238285


def test_d018_docs_are_registered() -> None:
    required = {
        "docs/post_gate5_d018_interpretation.md": "NO_ADVANCE",
        "research_protocol.md": "D018-C interpreted D017-C",
        "README.md": "D018-C interprets D017-C",
        "docs/decision_log.md": "D018-C completed",
        "docs/research_execution_map.md": "D022-C clean-source synthetic preflight pending",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
