from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_d033_config_accepts_release_but_preserves_boundary() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d033_release_acceptance.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D033-C"
    assert config["status"] == "completed_release_package_accepted"
    assert config["release"]["release_version"] == "0.3.0"
    assert config["release"]["release_tag"] == "v0.3.0"
    assert config["scope"]["release_authorized"] is True
    assert config["scope"]["tag_authorized"] is True
    assert config["scope"]["citation_update_authorized"] is True
    assert config["scope"]["source_archive_authorized"] is True
    assert config["scope"]["doi_minting_authorized"] is False
    assert config["scope"]["gate6_authorized"] is False
    assert config["scope"]["locked_data_access_authorized"] is False
    assert config["scope"]["qml_invention_claim_authorized"] is False
    assert config["scope"]["quantum_advantage_claim_authorized"] is False


def test_d033_outputs_release_acceptance_without_scientific_expansion() -> None:
    result = json.loads(
        (
            ROOT / "data/processed/reporting/post_gate5_d033_release_acceptance.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D033-C"
    assert result["official_status"] == "RELEASE_PACKAGE_ACCEPTED"
    assert result["human_acceptance"] is True
    assert result["release_version"] == "0.3.0"
    assert result["release_tag"] == "v0.3.0"
    assert result["release_authorized"] is True
    assert result["tag_authorized"] is True
    assert result["citation_update_authorized"] is True
    assert result["source_archive_authorized"] is True
    assert result["doi_minting_authorized"] is False
    assert result["gate6_authorized"] is False
    assert result["locked_data_access_authorized"] is False
    assert result["mission_loop_runs"] == 0
    assert result["calibration_rows_read"] == 0
    assert result["final_test_rows_read"] == 0
    assert "development-only benchmark" in result["accepted_claim"]
    assert "quantum-advantage claim" in result["claim_boundary"]

    rows = read_csv(
        ROOT / "data/processed/reporting/post_gate5_d033_release_acceptance_files.csv"
    )
    assert len(rows) == result["release_file_count"]
    assert any(row["path"] == "CITATION.cff" for row in rows)
    assert any(row["path"] == "docs/release_notes_v0.3.0.md" for row in rows)
    assert all(row["release_role"] == "accepted_release_package_member" for row in rows)


def test_d033_documentation_updates_release_position() -> None:
    required = {
        "research_protocol.md": "D033-C release package ACCEPTED",
        "README.md": "D033-C release package acceptance",
        "docs/decision_log.md": "D033-C completed",
        "docs/research_execution_map.md": "D033-C release package ACCEPTED",
        "docs/computational_methodology.md": "D033-C release package acceptance",
        "docs/release_checklist.md": "Human research lead accepted the release package",
        "docs/release_acceptance.md": "D033-C Release Acceptance",
        "docs/release_notes_v0.3.0.md": "Release Notes v0.3.0",
        "CITATION.cff": "version: 0.3.0",
    }
    for relative, phrase in required.items():
        assert phrase in (ROOT / relative).read_text(encoding="utf-8")
