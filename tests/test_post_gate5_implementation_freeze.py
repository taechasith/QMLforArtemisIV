from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_exploratory.yaml"
MANIFEST = (
    ROOT / "data/processed/reporting/post_gate5_exploratory_trial_manifest.csv"
)
DISCUSSION = (
    ROOT / "data/processed/reporting/post_gate5_future_research_discussion.csv"
)


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_d008_is_accepted_and_research_fit_remains_locked() -> None:
    config = _config()
    assert config["decision_id"] == "D008"
    assert config["protocol_id"] == "P001"
    assert config["status"] == (
        "accepted_implementation_freeze_implementation_and_synthetic_validation_authorized"
    )
    assert config["accepted_date"] == "2026-07-13"
    assert config["implementation_authorized"] is True
    assert config["synthetic_validation_authorized"] is True
    assert config["implementation_status"] == "implemented_synthetic_validation_passed"
    assert config["synthetic_validation_completed_date"] == "2026-07-13"
    assert config["research_data_fitting_authorized"] is False
    assert config["research_data_execution_decision"] == (
        "d009_synthetic_compute_preflight_accepted_pending_execution; "
        "later_d010_required_for_any_research_fit"
    )
    assert config["execution_authorized"] is False
    assert config["acceptance"]["current_decision"] == "accepted_by_human_research_lead"
    locks = config["locks"]
    assert locks["gate5_result_unchanged"] is True
    assert locks["d006_d007_evidence_immutable"] is True
    assert locks["development_split_only"] is True
    assert locks["calibration_rows_read"] == 0
    assert locks["final_test_rows_read"] == 0
    assert locks["gate6_authorized"] is False
    assert locks["hardware_execution_authorized"] is False


def test_projected_kernel_definition_is_complete() -> None:
    config = _config()
    feature_map = config["projected_quantum_feature_map"]
    assert feature_map["qubits"] == [4, 6, 8]
    assert feature_map["data_reupload_layers"] == [1, 2]
    assert feature_map["feature_scale"] == [0.5, 1.0, 2.0]
    assert feature_map["entangle"] == [True, False]
    assert feature_map["trainable_circuit_parameters"] == 0
    assert "Pauli X, Y, and Z" in feature_map["projection"]
    kernel = config["projected_kernel"]
    assert "rho_q" in kernel["definition"]
    assert "0.5" in kernel["bloch_equivalent"]
    assert "median(D_ij>0)" in kernel["gamma_reference"]
    assert kernel["gamma_multipliers"] == [0.25, 1.0, 4.0]
    assert kernel["nystrom_landmarks"] == 256
    assert "seed index" in kernel["landmark_rule"]
    assert "share landmark IDs" in kernel["landmark_rule"]
    assert kernel["regularization_alpha"] == [0.0001, 0.01, 1.0]
    assert "ineligible" in kernel["zero_median_action"]


def test_paired_manifest_is_unique_balanced_and_unexecuted() -> None:
    rows = _rows(MANIFEST)
    assert len(rows) == 30
    assert len({row["projection_id"] for row in rows}) == 30
    assert {row["track_ids"] for row in rows} == {"Q01b;FQK"}
    assert {row["execution_status"] for row in rows} == {"frozen_not_run"}
    assert Counter(row["qubits"] for row in rows) == {"4": 10, "6": 10, "8": 10}
    assert Counter(row["data_reupload_layers"] for row in rows) == {
        "1": 15,
        "2": 15,
    }
    assert Counter(row["feature_scale"] for row in rows) == {
        "0.5": 10,
        "1.0": 10,
        "2.0": 10,
    }
    assert Counter(row["entangle"] for row in rows) == {
        "false": 15,
        "true": 15,
    }
    assert Counter(row["gamma_multiplier"] for row in rows) == {
        "0.25": 10,
        "1.0": 10,
        "4.0": 10,
    }
    assert Counter(row["regularization_alpha"] for row in rows) == {
        "0.0001": 10,
        "0.01": 10,
        "1.0": 10,
    }
    assert {row["nystrom_landmarks"] for row in rows} == {"256"}


def test_tracks_have_distinct_endpoints_and_strong_controls() -> None:
    tracks = _config()["tracks"]
    q01b = tracks["Q01b"]
    fqk = tracks["FQK"]
    assert "NRMSE" in q01b["primary_endpoint"]
    assert q01b["target"] == "robust_total_correction_delta_v_m_s"
    assert any("C06-T17" in value for value in q01b["comparators"])
    assert any("exact classical RBF" in value for value in q01b["comparators"])
    assert fqk["target"] == "independently_propagated_feasible"
    assert "Brier" in fqk["primary_endpoint"]
    assert "does not mean fidelity" in fqk["acronym_warning"]
    assert any("C01-T18" in value for value in fqk["comparators"])
    assert "cost improvement" in fqk["claim_limit"]


def test_failure_discussion_register_is_empty_and_firewalled() -> None:
    config = _config()["failure_and_stop_policy"]
    rows = _rows(DISCUSSION)
    assert rows == []
    with DISCUSSION.open(newline="", encoding="utf-8") as handle:
        fields = next(csv.reader(handle))
    assert fields == [*config["required_fields"], "reporting_commit"]
    assert config["required_boolean_values"] == {
        "new_protocol_required": True,
        "active_pipeline_change_authorized": False,
        "post_outcome_retry_authorized": False,
    }
    assert "cannot alter" in config["firewall_rule"]
    assert "no silent retry" in config["retry_rule"]


def test_compute_and_reporting_fit_the_recorded_workstation() -> None:
    config = _config()
    compute = config["compute_admission"]
    assert compute["reference_ram_gib"] == 32
    assert compute["max_concurrent_statevector_tasks"] == 1
    assert compute["max_total_project_working_set_gib"] == 24
    assert compute["max_gpu_working_set_gib"] == 6.5
    assert compute["branch_gpu_hour_ceiling"] == 0
    assert compute["minimum_free_disk_gib"] == 20
    reporting = config["reporting"]
    assert reporting["implementation_freeze_figure"] == "RFIG-025"
    assert [row["id"] for row in reporting["planned_result_figures"]] == [
        "RFIG-026",
        "RFIG-027",
        "RFIG-028",
        "RFIG-029",
    ]
    assert "failure" in reporting["planned_result_figures"][-1]["content"]


def test_governance_describes_d008_as_accepted_without_research_fit() -> None:
    required = {
        "README.md": "D008 is accepted as the implementation freeze",
        "research_protocol.md": "D008 is the accepted implementation freeze",
        "docs/post_gate5_exploratory_protocol.md": "D008 implementation and synthetic validation complete",
        "docs/post_gate5_implementation_freeze.md": "Accepted by human research lead",
        "docs/decision_log.md": "D008 accepted - post-Gate-5 exploratory implementation freeze",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
