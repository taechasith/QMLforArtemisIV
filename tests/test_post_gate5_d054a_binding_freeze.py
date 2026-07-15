from __future__ import annotations

import csv
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d054a_p018_binding_freeze.yaml"
REGISTRY = ROOT / "artifacts/research_figures/figure_registry.csv"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_d054a_is_binding_only_and_excludes_srp() -> None:
    config = _config()

    assert config["decision_id"] == "D054-A"
    assert config["status"] == "accepted_binding_freeze_no_execution"
    assert config["physical_scope"]["deterministic_srp"]["active"] is False

    authority = config["authority_boundary"]
    assert authority["binding_freeze_authorized"] is True
    assert authority["binding_figure_authorized"] is True
    for key in (
        "numerical_audit_execution_authorized",
        "source_manifest_read_authorized",
        "development_data_read_authorized",
        "dataset_generation_authorized",
        "model_fit_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "future_audit_figure_rendering_authorized",
        "gate6_authorized",
    ):
        assert authority[key] is False


def test_d054a_binds_a_small_closed_audit_representation() -> None:
    config = _config()
    algebra = config["quantum_algebra_binding"]

    assert algebra["qubit_count"] == 4
    assert algebra["dla"]["basis_dimension"] == 255
    assert len(algebra["dla"]["expected_generator_set"]["local_controls"]) == 8
    assert len(algebra["dla"]["expected_generator_set"]["entanglers"]) == 3
    assert "255" in algebra["dla"]["closure_requirement"]


def test_d054a_binds_development_only_cases_and_defect_scales() -> None:
    config = _config()
    cases = config["development_only_case_binding"]
    defects = config["defect_and_target_binding"]

    assert cases["allowed_split"] == "development"
    assert cases["source_case_count"] == 36
    assert cases["maximum_propagations"] == 936
    assert len(cases["group_ids"]) == 12
    assert defects["acceleration_floor"]["eps_a_km_s2"] == 1.0e-12
    assert defects["primary_target"]["y_scale_m_s"] == 20.0
    assert len(config["rotation_suite"]["rotations"]) == 7


def test_d054a_figure_registry_has_one_methods_figure_and_three_reservations() -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = {row["figure_id"]: row for row in csv.DictReader(handle)}

    assert rows["RFIG-086"]["evidence_status"] == "accepted_binding_freeze_no_execution"
    assert (ROOT / rows["RFIG-086"]["png_path"]).is_file()
    assert (ROOT / rows["RFIG-086"]["svg_path"]).is_file()
    for figure_id in ("RFIG-087", "RFIG-088", "RFIG-089"):
        assert rows[figure_id]["evidence_status"] == "reserved_future_authorized_audit"
        assert rows[figure_id]["png_path"] == ""
        assert rows[figure_id]["svg_path"] == ""
