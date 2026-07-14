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
    expected_ids.add("RFIG-034")
    expected_ids.add("RFIG-035")
    expected_ids.add("RFIG-036")
    expected_ids.add("RFIG-037")
    expected_ids.add("RFIG-038")
    expected_ids.add("RFIG-039")
    expected_ids.add("RFIG-040")
    expected_ids.add("RFIG-041")
    expected_ids.add("RFIG-042")
    expected_ids.add("RFIG-043")
    expected_ids.add("RFIG-044")
    expected_ids.add("RFIG-045")
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
            "development_only_classical_first_residual_cost",
            "development_only_classical_first_safety_filter",
            "a02_exact_rbf_synthetic_compute_admission",
            "development_only_interpretation_no_advance",
            "future_only_safety_objective_discussion",
            "recall_first_safety_freeze_proposal",
            "recall_first_synthetic_validation_pass",
            "recall_first_synthetic_compute_admission",
            "development_only_recall_first_selection_audit",
            "recall_first_interpretation_no_advance",
            "gate5_closure_no_qml_gate6_candidate",
            "manuscript_claim_synthesis",
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
    rfig034 = next(row for row in rows if row["figure_id"] == "RFIG-034")
    assert rfig034["evidence_status"] == (
        "development_only_classical_first_residual_cost"
    )
    assert rfig034["reporting_source_commit"] == (
        "419844a690d625502718e00b3e4dcafc6d99286c"
    )
    assert rfig034["figure_generator_sha256"] == sha256_file(
        ROOT / rfig034["generator"]
    )
    rfig035 = next(row for row in rows if row["figure_id"] == "RFIG-035")
    assert rfig035["evidence_status"] == (
        "development_only_classical_first_safety_filter"
    )
    assert rfig035["reporting_source_commit"] == (
        "419844a690d625502718e00b3e4dcafc6d99286c"
    )
    assert rfig035["figure_generator_sha256"] == sha256_file(
        ROOT / rfig035["generator"]
    )
    rfig036 = next(row for row in rows if row["figure_id"] == "RFIG-036")
    assert rfig036["source_data"] == (
        "data/processed/reporting/post_gate5_d016_c1_a02_preflight.json"
    )
    assert rfig036["evidence_status"] == (
        "a02_exact_rbf_synthetic_compute_admission"
    )
    assert rfig036["reporting_source_commit"] == (
        "a40a6687b7c68a04f355ee40e0ff6144482eaf6c"
    )
    assert rfig036["figure_generator_sha256"] == sha256_file(
        ROOT / rfig036["generator"]
    )
    rfig037 = next(row for row in rows if row["figure_id"] == "RFIG-037")
    assert rfig037["evidence_status"] == (
        "development_only_interpretation_no_advance"
    )
    assert "post_gate5_d018_interpretation.json" in rfig037["source_data"]
    assert rfig037["reporting_source_commit"] == (
        "a173b9308ac1073120475a1a13a1b79c5c5063dd"
    )
    assert rfig037["figure_generator_sha256"] == sha256_file(
        ROOT / rfig037["generator"]
    )
    rfig038 = next(row for row in rows if row["figure_id"] == "RFIG-038")
    assert rfig038["evidence_status"] == (
        "future_only_safety_objective_discussion"
    )
    assert "post_gate5_d019_safety_redesign.json" in rfig038["source_data"]
    assert rfig038["reporting_source_commit"] == (
        "06e6283d99682615c16465af0254049987113563"
    )
    assert rfig038["figure_generator_sha256"] == sha256_file(
        ROOT / rfig038["generator"]
    )
    rfig039 = next(row for row in rows if row["figure_id"] == "RFIG-039")
    assert rfig039["evidence_status"] == "recall_first_safety_freeze_proposal"
    assert "post_gate5_d020_recall_first_freeze.json" in rfig039["source_data"]
    assert rfig039["reporting_source_commit"] == (
        "cbb57389cbccb9ed78a32403d602c59b6de64c9b"
    )
    assert rfig039["figure_generator_sha256"] == sha256_file(
        ROOT / rfig039["generator"]
    )
    rfig040 = next(row for row in rows if row["figure_id"] == "RFIG-040")
    assert rfig040["evidence_status"] == "recall_first_synthetic_validation_pass"
    assert "post_gate5_d021_recall_first_synthetic.json" in rfig040["source_data"]
    assert rfig040["reporting_source_commit"] == (
        "fc0c31c49279b117f93122c9018df78574e6c035"
    )
    assert rfig040["figure_generator_sha256"] == sha256_file(
        ROOT / rfig040["generator"]
    )
    rfig041 = next(row for row in rows if row["figure_id"] == "RFIG-041")
    assert rfig041["evidence_status"] == "recall_first_synthetic_compute_admission"
    assert rfig041["source_data"] == (
        "data/processed/reporting/post_gate5_d022_recall_first_preflight.json"
    )
    assert rfig041["reporting_source_commit"] == (
        "b5263ba3876c4e66f3243b58a679e2c29419120f"
    )
    assert rfig041["figure_generator_sha256"] == sha256_file(
        ROOT / rfig041["generator"]
    )
    rfig042 = next(row for row in rows if row["figure_id"] == "RFIG-042")
    assert rfig042["evidence_status"] == (
        "development_only_recall_first_selection_audit"
    )
    assert "post_gate5_d023_recall_first_development.json" in rfig042["source_data"]
    assert rfig042["reporting_source_commit"] == (
        "419844a690d625502718e00b3e4dcafc6d99286c"
    )
    assert rfig042["figure_generator_sha256"] == sha256_file(
        ROOT / rfig042["generator"]
    )
    rfig043 = next(row for row in rows if row["figure_id"] == "RFIG-043")
    assert rfig043["evidence_status"] == "recall_first_interpretation_no_advance"
    assert "post_gate5_d024_recall_first_interpretation.json" in rfig043["source_data"]
    assert rfig043["reporting_source_commit"] == (
        "e15d7583042b574261afe7afa4904168b3d398dd"
    )
    assert rfig043["figure_generator_sha256"] == sha256_file(
        ROOT / rfig043["generator"]
    )
    rfig044 = next(row for row in rows if row["figure_id"] == "RFIG-044")
    assert rfig044["evidence_status"] == "gate5_closure_no_qml_gate6_candidate"
    assert "post_gate5_d025_gate6_recommendation.json" in rfig044["source_data"]
    assert rfig044["reporting_source_commit"] == (
        "66515b459dacebbecf78f900a4b4020021f484ce"
    )
    assert rfig044["figure_generator_sha256"] == sha256_file(
        ROOT / rfig044["generator"]
    )
    rfig045 = next(row for row in rows if row["figure_id"] == "RFIG-045")
    assert rfig045["evidence_status"] == "manuscript_claim_synthesis"
    assert "post_gate5_d026_manuscript_synthesis.json" in rfig045["source_data"]
    assert rfig045["reporting_source_commit"] == (
        "0d1576e7ed5088a7d99547be2f5f5b69d8700619"
    )
    assert rfig045["figure_generator_sha256"] == sha256_file(
        ROOT / rfig045["generator"]
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
