from __future__ import annotations

import csv
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_gate5_is_accepted_and_gate6_remains_closed() -> None:
    with (ROOT / "data/processed/reporting/gate_timeline.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = {row["gate"]: row for row in csv.DictReader(handle)}

    assert rows["Gate 5"] == {
        "gate": "Gate 5",
        "decision_date": "2026-07-13",
        "status": "accepted",
        "decision": (
            "Technical FAIL accepted for the preregistered development benchmark"
        ),
    }
    assert rows["Gate 6"]["status"] == "not_open"
    assert rows["Gate 6"]["decision_date"] == ""

    config = yaml.safe_load(
        (ROOT / "configs/phase1_benchmark.yaml").read_text(encoding="utf-8")
    )
    assert config["gate5_status"] == (
        "accepted_technical_trigger_fail_new_algorithm_rejected"
    )
    freeze = config["gate5_runner_freeze"]
    assert freeze["technical_trigger_status"] == "FAIL"
    assert freeze["technical_gate5_decision"] == "accepted_fail"
    assert freeze["technical_gate5_decision_date"] == "2026-07-13"


def test_governance_statuses_do_not_leave_gate5_pending() -> None:
    paths = (
        ROOT / "README.md",
        ROOT / "research_protocol.md",
        ROOT / "docs/decision_log.md",
        ROOT / "docs/model_registry.md",
        ROOT / "docs/phase1_analysis_plan.md",
        ROOT / "docs/research_execution_map.md",
    )
    stale_phrases = (
        "Gate 5 technical trigger FAIL pending separate human decision",
        "The separate human Gate 5 decision remains pending",
        "A separate human Gate 5 decision is still required",
    )

    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert all(phrase not in text for phrase in stale_phrases), path
        assert "Gate 6" in text, path
