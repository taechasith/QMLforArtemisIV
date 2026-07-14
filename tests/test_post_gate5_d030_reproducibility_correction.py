from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_d030_config_records_source_control_only_correction() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d030_reproducibility_correction.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D030-C"
    assert config["status"] == "completed_clean_reproducibility_audit_pass"
    assert config["scope"]["source_control_only"] is True
    assert config["scope"]["model_fitting"] is False
    assert config["scope"]["calibration_read"] is False
    assert config["scope"]["final_test_read"] is False
    assert config["scope"]["gate6_run"] is False
    assert config["outcome"]["official_status"] == "REPRODUCIBILITY_AUDIT_PASS"
    assert config["outcome"]["release_ready_for_human_decision"] is True


def test_d030_outputs_record_clean_audit_pass_without_release_authorization() -> None:
    result = json.loads(
        (
            ROOT
            / "data/processed/reporting/post_gate5_d030_reproducibility_correction.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D030-C"
    assert result["official_status"] == "REPRODUCIBILITY_AUDIT_PASS"
    assert result["release_ready_for_human_decision"] is True
    assert result["release_authorized"] is False
    assert result["gate6_authorized"] is False
    assert result["calibration_rows_read"] == 0
    assert result["final_test_rows_read"] == 0
    assert result["mission_loop_runs"] == 0

    rows = read_csv(
        ROOT
        / "data/processed/reporting/post_gate5_d030_reproducibility_correction_matrix.csv"
    )
    assert {row["audit_item"] for row in rows} == {
        "line_ending_policy",
        "pytest",
        "ruff",
        "compileall",
    }
    assert {row["status"] for row in rows} <= {"corrected", "pass"}


def test_d030_documentation_updates_current_release_position() -> None:
    required = {
        "research_protocol.md": "D030-C clean reproducibility correction PASS",
        "README.md": "D030-C clean reproducibility correction",
        "docs/decision_log.md": "D030-C completed",
        "docs/research_execution_map.md": "D030-C clean reproducibility correction PASS",
        "docs/computational_methodology.md": "D030-C clean reproducibility correction",
        "docs/release_checklist.md": "Release is eligible for human claim/release review",
        "docs/release_reproducibility_audit.md": "D030-C corrected the byte-provenance blocker",
    }
    for relative, phrase in required.items():
        assert phrase in (ROOT / relative).read_text(encoding="utf-8")
