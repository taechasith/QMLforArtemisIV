from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_d031_config_is_review_only_and_not_release() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d031_claim_release_review.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D031-C"
    assert config["status"] == "completed_claim_release_review_ready_for_human_decision"
    assert config["scope"]["claim_review_only"] is True
    for key, value in config["scope"].items():
        if key.endswith("_authorized"):
            assert value is False
    assert config["review"]["official_status"] == "CLAIM_RELEASE_REVIEW_READY"


def test_d031_outputs_prepare_human_decision_without_authorization() -> None:
    result = json.loads(
        (
            ROOT / "data/processed/reporting/post_gate5_d031_claim_release_review.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D031-C"
    assert result["official_status"] == "CLAIM_RELEASE_REVIEW_READY"
    assert result["release_ready_for_human_decision"] is True
    assert result["release_authorized"] is False
    assert result["gate6_authorized"] is False
    assert result["calibration_rows_read"] == 0
    assert result["final_test_rows_read"] == 0
    assert result["mission_loop_runs"] == 0
    assert result["prohibited_claim_count"] >= 6

    rows = read_csv(
        ROOT / "data/processed/reporting/post_gate5_d031_claim_release_review_matrix.csv"
    )
    assert any(row["review_item"] == "allowed_claim" for row in rows)
    assert any(row["review_item"] == "human_decision" for row in rows)
    assert any(row["status"] == "prohibited" for row in rows)


def test_d031_documentation_updates_release_decision_point() -> None:
    required = {
        "research_protocol.md": "D031-C final claim/release review READY",
        "README.md": "D031-C final claim/release review",
        "docs/decision_log.md": "D031-C completed",
        "docs/research_execution_map.md": "D031-C completes final claim/release review preparation",
        "docs/computational_methodology.md": "D031-C final claim/release review",
        "docs/release_checklist.md": "final claim review is complete",
        "docs/final_claim_release_review.md": "D031-C Final Claim/Release Review",
        "paper/manuscript.md": "Status: D031-C claim-reviewed draft",
    }
    for relative, phrase in required.items():
        assert phrase in (ROOT / relative).read_text(encoding="utf-8")
