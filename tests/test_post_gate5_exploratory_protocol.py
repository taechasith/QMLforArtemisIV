from __future__ import annotations

import csv
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_post_gate5_exploratory_protocol_scope_is_narrow() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/phase1_benchmark.yaml").read_text(encoding="utf-8")
    )
    protocol = config["post_gate5_exploratory_protocol"]
    assert protocol["status"] == "d011_terminal_prelaunch_technical_stop"
    assert (
        protocol["implementation_freeze_decision"] == "accepted_by_human_research_lead"
    )
    assert protocol["implementation_authorized"] is True
    assert protocol["synthetic_validation_authorized"] is True
    assert (
        protocol["implementation_status"] == "implemented_synthetic_validation_passed"
    )
    assert protocol["synthetic_validation_completed_date"] == "2026-07-13"
    assert protocol["research_data_fitting_authorized"] is False
    assert (
        "Not satisfied"
        in protocol["research_data_fitting_condition"]
    )
    assert protocol["research_data_execution_decision"] == (
        "D011 conditional authority ended in a terminal pre-launch technical STOP on 2026-07-13"
    )
    assert protocol["development_execution_decision"] == "D011"
    assert protocol["development_execution_status"] == (
        "terminal_prelaunch_technical_stop"
    )
    assert protocol["largest_fold_preflight_figure_status"] == "absent_not_reached"
    assert protocol["development_payload_rows_read"] == 0
    assert protocol["development_campaign_started"] is False
    assert protocol["d011_retry_authorized"] is False
    assert protocol["compute_preflight_decision"] == "D010"
    assert protocol["compute_preflight_status"] == "PASS_synthetic_compute_admission"
    assert protocol["compute_preflight_execution_authorized"] is False
    assert protocol["compute_preflight_telemetry_status"] == "PASS"
    assert protocol["gate5_result_unchanged"] is True
    assert protocol["calibration_access"] is False
    assert protocol["final_test_access"] is False
    assert protocol["gate6_authorized"] is False
    assert protocol["d006_refit_authorized"] is False
    assert {entry["id"] for entry in protocol["near_term_qml_tests"]} == {
        "Q01b",
        "FQK",
    }
    assert "quantum_reinforcement_learning" in protocol["appendix_future_only"]
    assert "quantum_annealing" in protocol["appendix_future_only"]
    assert "qaoa" in protocol["appendix_future_only"]


def test_post_gate5_protocol_matrix_matches_config_boundary() -> None:
    rows = read_csv(
        ROOT / "data/processed/reporting/post_gate5_exploratory_protocol_matrix.csv"
    )
    near_term = {
        row["track_id"]
        for row in rows
        if row["near_term_status"] == "near_term_qml_test"
    }
    future_only = {
        row["track_id"]
        for row in rows
        if row["near_term_status"] == "appendix_future_only"
    }
    assert near_term == {"Q01b", "FQK"}
    assert {"QRL", "QAOA", "VAR", "HW"} <= future_only
    for row in rows:
        assert (
            "final-test" in row["claim_boundary"]
            or row["authorized_data_scope"] == "No execution authorized"
        )


def test_post_gate5_protocol_doc_keeps_gate5_and_locked_splits_closed() -> None:
    text = (ROOT / "docs/post_gate5_exploratory_protocol.md").read_text(
        encoding="utf-8"
    )
    assert "Gate 5 result remains unchanged" in text
    assert (
        "Calibration rows, final-test rows, and Gate 6 mission scenarios remain" in text
    )
    assert "`Q01b`" in text
    assert "`FQK`" in text
    assert "Quantum reinforcement learning" in text
    assert "appendix or future-work topics only" in text
