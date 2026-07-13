from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "artifacts/research_figures"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_pre_d003_audit_is_retained_as_invalid_evidence() -> None:
    summary = json.loads(
        (
            ROOT / "data/processed/simulator/scenarios/pre_d003_audit_summary.json"
        ).read_text(encoding="utf-8")
    )
    assert summary == {
        "audit_label": "pre_d003",
        "decision_sets": 1400,
        "feasible_records": 502,
        "final_test_payloads_read": 0,
        "groups_audited": 14,
        "invalid_groups": 14,
        "no_reference_feasible_sets": 1020,
        "nonfinite_records": 0,
        "records_audited": 7000,
        "relationship_error_records": 7000,
        "schema_error_records": 7000,
        "status": "invalid",
        "valid_groups": 0,
    }


def test_figure_registry_has_unique_ids_and_matching_artifacts() -> None:
    rows = read_csv(FIGURES / "figure_registry.csv")
    assert len(rows) >= 20
    figure_ids = {row["figure_id"] for row in rows}
    assert len(figure_ids) == len(rows)
    expected_ids = {f"RFIG-{index:03d}" for index in range(1, 26)} - {
        "RFIG-010",
        "RFIG-013",
    }
    expected_ids.add("RFIG-029")
    expected_ids.add("RFIG-030")
    expected_ids.add("RFIG-031")
    expected_ids.add("RFIG-032")
    expected_ids.add("RFIG-033")
    expected_ids.update({"RFIG-026", "RFIG-027", "RFIG-028"})
    assert expected_ids <= figure_ids
    assert {"RFIG-010", "RFIG-013"}.isdisjoint(figure_ids)
    assert {row["evidence_status"] for row in rows} >= {
        "accepted_decision_record",
        "invalid_failed_attempt",
        "invalid_workload_timing",
        "repair_validation_development",
        "development_and_calibration_diagnostic",
        "pre_fit_literature_hardening",
        "pre_fit_runner_freeze",
        "post_gate5_exploratory_protocol",
        "pre_execution_implementation_freeze_accepted",
            "governed_failure_or_exploratory_negative",
            "synthetic_compute_admission_pass",
            "development_only_exploratory_model_evidence",
            "development_only_kernel_diagnostics",
            "development_only_feasibility_evidence",
            "classical_first_freeze_proposal",
            "classical_first_synthetic_compute_admission",
        }
    for row in rows:
        assert "final_test" not in row["source_data"]
        for kind in ("png", "svg"):
            path = ROOT / row[f"{kind}_path"]
            assert path.is_file()
            assert path.stat().st_size == int(row[f"{kind}_bytes"])
            assert sha256_file(path) == row[f"{kind}_sha256"]
    rfig029 = next(row for row in rows if row["figure_id"] == "RFIG-029")
    summary = json.loads(
        (
            ROOT / "data/processed/reporting/post_gate5_p001/campaign_summary.json"
        ).read_text(encoding="utf-8")
    )
    assert rfig029["reporting_source_commit"] == summary["source_commit"]
    assert "post_gate5_future_research_discussion.csv" in rfig029["source_data"]
    assert "post_gate5_p001/exploratory_decision.json" in rfig029["source_data"]
    assert rfig029["figure_generator_sha256"] == sha256_file(
        ROOT / rfig029["generator"]
    )
    rfig031 = next(row for row in rows if row["figure_id"] == "RFIG-031")
    assert rfig031["source_data"] == (
        "data/processed/reporting/post_gate5_d011_c2_fold_shape_preflight.json"
    )
    assert rfig031["reporting_source_commit"] == summary["source_commit"]
    rfig030 = next(row for row in rows if row["figure_id"] == "RFIG-030")
    assert rfig030["reporting_source_commit"] == (
        "882bfd58d1154194b011dfc6fcef974cfe96ead3"
    )
    assert rfig030["source_data"] == (
        "data/processed/reporting/post_gate5_compute_preflight_rerun.json"
    )
    assert rfig030["figure_generator_sha256"] == sha256_file(
        ROOT / rfig030["generator"]
    )
    rfig032 = next(row for row in rows if row["figure_id"] == "RFIG-032")
    assert rfig032["source_data"] == (
        "configs/post_gate5_d014_classical_first_freeze.yaml"
    )
    assert rfig032["evidence_status"] == "classical_first_freeze_proposal"
    assert rfig032["figure_generator_sha256"] == sha256_file(
        ROOT / rfig032["generator"]
    )
    rfig033 = next(row for row in rows if row["figure_id"] == "RFIG-033")
    assert rfig033["source_data"] == (
        "data/processed/reporting/post_gate5_d016_classical_preflight.json"
    )
    assert rfig033["evidence_status"] == (
        "classical_first_synthetic_compute_admission"
    )
    assert rfig033["reporting_source_commit"] == (
        "45409a86a5e450d72ba7f043715956fa5b916974"
    )
    assert rfig033["figure_generator_sha256"] == sha256_file(
        ROOT / rfig033["generator"]
    )


def test_full_f1_audit_is_valid_and_final_test_remains_unread() -> None:
    summary = json.loads(
        (
            ROOT / "data/processed/simulator/scenarios/post_d003_f1_audit_summary.json"
        ).read_text(encoding="utf-8")
    )
    assert summary == {
        "audit_label": "post_d003_f1",
        "decision_sets": 7000,
        "feasible_records": 6436,
        "final_test_payloads_read": 0,
        "groups_audited": 14,
        "invalid_groups": 0,
        "no_reference_feasible_sets": 4215,
        "nonfinite_records": 0,
        "records_audited": 35000,
        "relationship_error_records": 0,
        "schema_error_records": 0,
        "status": "valid",
        "valid_groups": 14,
    }


def test_f2_first_group_audit_is_valid_and_final_test_remains_unread() -> None:
    summary = json.loads(
        (
            ROOT
            / "data/processed/simulator/scenarios/post_d003_f2_g01_audit_summary.json"
        ).read_text(encoding="utf-8")
    )
    assert summary == {
        "audit_label": "post_d003_f2_g01",
        "decision_sets": 50,
        "feasible_records": 200,
        "final_test_payloads_read": 0,
        "groups_audited": 1,
        "invalid_groups": 0,
        "no_reference_feasible_sets": 0,
        "nonfinite_records": 0,
        "records_audited": 250,
        "relationship_error_records": 0,
        "schema_error_records": 0,
        "status": "valid",
        "valid_groups": 1,
    }


def test_full_f2_audit_is_valid_and_final_test_remains_unread() -> None:
    summary = json.loads(
        (
            ROOT / "data/processed/simulator/scenarios/post_d003_f2_audit_summary.json"
        ).read_text(encoding="utf-8")
    )
    assert summary == {
        "audit_label": "post_d003_f2",
        "decision_sets": 700,
        "feasible_records": 642,
        "final_test_payloads_read": 0,
        "groups_audited": 14,
        "invalid_groups": 0,
        "no_reference_feasible_sets": 423,
        "nonfinite_records": 0,
        "records_audited": 3500,
        "relationship_error_records": 0,
        "schema_error_records": 0,
        "status": "valid",
        "valid_groups": 14,
    }


def test_figure_policy_requires_failed_and_negative_evidence() -> None:
    policy = (ROOT / "docs/research_figure_policy.md").read_text(encoding="utf-8")
    assert "failed attempt" in policy
    assert "negative and inconclusive findings" in policy
    assert "Never plot a locked final-test value" in policy
    assert "Comparisons with only a few factors are tables" in policy
    assert "more than 100 plotted data points" in policy
    assert "Methods, decision gates, protocols, and timelines are diagrams" in policy
