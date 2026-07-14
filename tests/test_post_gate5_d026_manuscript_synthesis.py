from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_d026_config_is_manuscript_only() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d026_manuscript_synthesis.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D026-C"
    assert config["scope"]["manuscript_reporting_only"] is True
    for key, value in config["scope"].items():
        if key.endswith("_authorized"):
            assert value is False
    assert "QML improves cislunar propellant efficiency" in config["synthesis"]["prohibited_claims"]


def test_d026_result_preserves_gate6_lock_and_claim_boundary() -> None:
    result = json.loads(
        (
            ROOT
            / "data/processed/reporting/post_gate5_d026_manuscript_synthesis.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D026-C"
    assert result["official_status"] == "MANUSCRIPT_SYNTHESIS_READY"
    assert result["gate6_authorized"] is False
    assert result["qml_gate6_candidate"] is False
    assert "did not outperform" in result["allowed_main_claim"]
    assert "Quantum advantage was observed" in result["prohibited_claims"]
    for key in (
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "mission_loop_runs",
        "gate6_runs",
    ):
        assert result[key] == 0


def test_d026_docs_and_manuscript_scaffold_are_registered() -> None:
    expected = {
        "docs/manuscript_results_synthesis.md": "D026-C converts",
        "paper/manuscript.md": "Status: D027-C",
        "research_protocol.md": "D026-C",
        "README.md": "D026-C",
        "docs/decision_log.md": "D026-C",
        "docs/research_execution_map.md": "D026-C",
        "docs/computational_methodology.md": "D026-C",
    }
    for relative, needle in expected.items():
        assert needle in (ROOT / relative).read_text(encoding="utf-8")
