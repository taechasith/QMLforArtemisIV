from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_d027_config_is_manuscript_drafting_only() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d027_manuscript_results.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D027-C"
    assert config["scope"]["manuscript_reporting_only"] is True
    for key, value in config["scope"].items():
        if key.endswith("_authorized"):
            assert value is False


def test_d027_result_and_tables_preserve_claim_boundary() -> None:
    result = json.loads(
        (
            ROOT
            / "data/processed/reporting/post_gate5_d027_manuscript_results.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D027-C"
    assert result["official_status"] == "MANUSCRIPT_RESULTS_DISCUSSION_DRAFT_READY"
    assert result["gate6_authorized"] is False
    assert result["qml_gate6_candidate"] is False
    for key in (
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "mission_loop_runs",
        "gate6_runs",
    ):
        assert result[key] == 0

    gate5_rows = read_csv(ROOT / "paper/results_tables/gate5_qml_vs_controls.csv")
    assert {row["result_block"] for row in gate5_rows} >= {
        "Preregistered Gate 5",
        "Exploratory Q01b",
        "Exploratory FQK",
        "CSAFE-RF lesson",
    }
    claim_rows = read_csv(ROOT / "paper/results_tables/claim_boundary_table.csv")
    assert any(row["claim_type"] == "Prohibited claim" for row in claim_rows)


def test_d027_docs_and_manuscript_are_registered() -> None:
    expected = {
        "docs/manuscript_results_discussion_draft.md": "D027-C turns",
        "paper/manuscript.md": "Status: D027-C",
        "research_protocol.md": "D027-C",
        "README.md": "D027-C",
        "docs/decision_log.md": "D027-C",
        "docs/research_execution_map.md": "D027-C",
        "docs/computational_methodology.md": "D027-C",
    }
    for relative, needle in expected.items():
        assert needle in (ROOT / relative).read_text(encoding="utf-8")
