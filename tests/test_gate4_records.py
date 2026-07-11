from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from openqfuel.gate4 import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_search_log_discloses_complete_and_count_only_coverage() -> None:
    rows = read_csv(ROOT / "literature/search_log.csv")
    assert len(rows) == 14
    assert {row["search_id"] for row in rows} == {
        "S1",
        "S2",
        "S3",
        "S4",
        "S5",
        "S6",
        "S7",
    }
    openalex = [row for row in rows if row["database"] == "OpenAlex"]
    assert len(openalex) == 7
    assert sum(int(row["result_count"]) for row in openalex) == 9732
    assert all(row["records_retrieved"] == "0" for row in openalex)
    assert all("HTTP 429" in row["coverage_status"] for row in openalex)
    complete = [row for row in rows if row["database"] in {"NASA NTRS", "arXiv"}]
    assert len(complete) == 7
    assert all(row["coverage_status"].startswith("complete API") for row in complete)


def test_screening_and_extraction_flow_is_closed_and_unique() -> None:
    screening = read_csv(ROOT / "literature/screening_log.csv")
    extraction = read_csv(ROOT / "literature/extraction_matrix.csv")
    assert len(screening) == 1406
    assert Counter(row["decision"] for row in screening) == {
        "exclude": 1340,
        "defer_phase_6": 42,
        "include": 24,
    }
    assert len(extraction) == 23
    assert len({row["evidence_id"] for row in extraction}) == 23
    assert all(row["source_url"].startswith("https://") for row in extraction)
    allowed_quality = {"strong", "partial", "weak", "not_applicable", "unclear"}
    quality_fields = [field for field in extraction[0] if field.startswith("quality_")]
    assert quality_fields
    assert all(
        row[field] in allowed_quality for row in extraction for field in quality_fields
    )


def test_literature_synthesis_does_not_claim_systematic_completion() -> None:
    text = (ROOT / "docs/literature_synthesis.md").read_text(encoding="utf-8")
    assert "not a complete systematic review" in text
    assert "HTTP 429" in text
    assert "D002" in text


def test_gate4_artifact_checksums_match_files() -> None:
    directory = ROOT / "data/processed/simulator"
    rows = read_csv(directory / "gate4_freeze_checksums.csv")
    assert len(rows) == 5
    for row in rows:
        artifact = directory / row["artifact"]
        assert artifact.is_file()
        assert int(row["size_bytes"]) == artifact.stat().st_size
        assert row["sha256"] == sha256_file(artifact)
        assert row["status"] == "frozen_gate_4_accepted_final_test_separately_locked"


def test_locked_payload_root_remains_empty() -> None:
    root = ROOT / "data/locked/phase1"
    assert not root.exists() or not any(path.is_file() for path in root.rglob("*"))
