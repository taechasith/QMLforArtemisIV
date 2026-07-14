from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_d032_config_is_manifest_only() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d032_release_candidate_manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D032-C"
    assert config["status"] == "completed_release_candidate_manifest_ready"
    assert config["scope"]["release_candidate_manifest_only"] is True
    for key, value in config["scope"].items():
        if key.endswith("_authorized"):
            assert value is False
    assert config["candidate"]["release_tag_authority"] == "human_acceptance_required"


def test_d032_outputs_manifest_without_release_authorization() -> None:
    result = json.loads(
        (
            ROOT
            / "data/processed/reporting/post_gate5_d032_release_candidate_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D032-C"
    assert result["official_status"] == "RELEASE_CANDIDATE_MANIFEST_READY"
    assert result["release_ready_for_human_decision"] is True
    assert result["release_authorized"] is False
    assert result["tag_authorized"] is False
    assert result["archive_authorized"] is False
    assert result["doi_authorized"] is False
    assert result["citation_update_authorized"] is False
    assert result["gate6_authorized"] is False
    assert result["calibration_rows_read"] == 0
    assert result["final_test_rows_read"] == 0
    assert result["mission_loop_runs"] == 0

    rows = read_csv(
        ROOT / "data/processed/reporting/post_gate5_d032_release_candidate_files.csv"
    )
    assert len(rows) == result["manifest_file_count"]
    assert any(row["path"] == "README.md" for row in rows)
    assert any(row["path"] == "paper/manuscript.md" for row in rows)
    assert all(row["release_role"] == "candidate_manifest_member" for row in rows)


def test_d032_documentation_updates_release_candidate_position() -> None:
    required = {
        "research_protocol.md": "D032-C release-candidate manifest READY",
        "README.md": "D032-C release-candidate manifest",
        "docs/decision_log.md": "D032-C completed",
        "docs/research_execution_map.md": "D032-C release-candidate manifest READY",
        "docs/computational_methodology.md": "D032-C release-candidate manifest",
        "docs/release_checklist.md": "release-candidate manifest is ready",
        "docs/release_candidate_manifest.md": "D032-C Release-Candidate Manifest",
    }
    for relative, phrase in required.items():
        assert phrase in (ROOT / relative).read_text(encoding="utf-8")
