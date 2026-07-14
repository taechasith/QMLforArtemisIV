from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_d029_config_is_failed_release_audit_only() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d029_reproducibility_audit.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D029-C"
    assert config["scope"]["reproducibility_audit_only"] is True
    assert config["scope"]["release_authorized"] is False
    assert config["scope"]["correction_authorized"] is False
    assert config["audit_commands"]["pytest"]["exit_code"] == 1
    assert config["audit_commands"]["ruff"]["exit_code"] == 0
    assert config["audit_commands"]["compileall"]["exit_code"] == 0


def test_d029_result_records_stop_without_new_authority() -> None:
    result = json.loads(
        (
            ROOT
            / "data/processed/reporting/post_gate5_d029_reproducibility_audit.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D029-C"
    assert result["official_status"] == "REPRODUCIBILITY_AUDIT_STOP"
    assert result["release_ready"] is False
    assert result["release_authorized"] is False
    assert result["correction_authorized"] is False
    assert result["failure_count"] == 3
    for key in (
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "mission_loop_runs",
        "gate6_runs",
    ):
        assert result[key] == 0

    rows = read_csv(
        ROOT / "data/processed/reporting/post_gate5_d029_reproducibility_audit_matrix.csv"
    )
    assert any(row["audit_item"] == "pytest" and row["status"] == "failed" for row in rows)
    assert any("scenario_manifest.csv" in row["evidence"] for row in rows)


def test_d029_docs_are_registered() -> None:
    expected = {
        "docs/release_reproducibility_audit.md": "Clean reproducibility audit STOP",
        "docs/release_checklist.md": "Blocked by clean reproducibility audit STOP",
        "research_protocol.md": "D029-C",
        "README.md": "D029-C",
        "docs/decision_log.md": "D029-C",
        "docs/research_execution_map.md": "D029-C",
        "docs/computational_methodology.md": "D029-C",
    }
    for relative, needle in expected.items():
        assert needle in (ROOT / relative).read_text(encoding="utf-8")
