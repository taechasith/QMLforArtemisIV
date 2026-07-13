from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from openqfuel.gate4 import FinalTestAccessError
from openqfuel.post_gate5 import (
    assert_post_gate5_scope,
    equivalent_preflight_work_units,
    evaluate_preflight_admission,
    project_preflight_resources,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_preflight.yaml"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_d009_authorizes_only_one_synthetic_compute_preflight() -> None:
    config = _config()
    assert config["decision_id"] == "D009"
    assert config["protocol_id"] == "P001"
    assert config["status"] == "accepted_synthetic_compute_preflight_authorized"
    assert config["accepted_date"] == "2026-07-13"
    assert config["preflight_execution_authorized"] is True
    assert config["research_data_fitting_authorized"] is False
    assert config["exploratory_execution_authorized"] is False
    assert config["locks"]["allowed_data_scope"] == "synthetic"
    assert config["locks"]["development_rows_read"] == 0
    assert config["locks"]["calibration_rows_read"] == 0
    assert config["locks"]["final_test_rows_read"] == 0
    assert config["locks"]["gate6_authorized"] is False


def test_d009_scope_guard_keeps_every_research_split_locked() -> None:
    config = _config()
    assert_post_gate5_scope(
        config, action="compute_preflight", data_scope="synthetic"
    )
    with pytest.raises(PermissionError, match="research-data fitting"):
        assert_post_gate5_scope(
            config, action="preflight", data_scope="development"
        )
    with pytest.raises(FinalTestAccessError, match="final_test remains locked"):
        assert_post_gate5_scope(
            config, action="compute_preflight", data_scope="final_test"
        )
    with pytest.raises(FinalTestAccessError, match="gate6 remains locked"):
        assert_post_gate5_scope(
            config, action="compute_preflight", data_scope="gate6"
        )


def test_campaign_projection_formula_is_frozen_and_conservative() -> None:
    config = _config()
    assert equivalent_preflight_work_units(config) == pytest.approx(477.5)
    projection = config["campaign_projection"]
    assert projection["projection_margin"] == 1.25
    assert projection["artifact_bytes_per_work_unit"] == 2 * 1024 * 1024
    assert "does not assume cache reuse" in projection["accounting_rule"]


def test_resource_projection_applies_units_margin_and_sequential_memory() -> None:
    projected = project_preflight_resources(
        _config(),
        benchmark_cpu_seconds=12.0,
        benchmark_wall_seconds=10.0,
        peak_rss_gib=1.5,
        free_disk_gib=100.0,
    )
    scale = 477.5 * 1.25
    assert projected["projected_cpu_core_hours"] == pytest.approx(
        12.0 * scale / 3600.0
    )
    assert projected["projected_wall_clock_days"] == pytest.approx(
        10.0 * scale / 86400.0
    )
    assert projected["projected_new_artifacts_gib"] == pytest.approx(
        scale * 2.0 / 1024.0
    )
    assert projected["observed_peak_rss_gib"] == 1.5
    assert projected["projected_free_disk_after_artifacts_gib"] == pytest.approx(
        100.0 - scale * 2.0 / 1024.0
    )


def test_admission_passes_only_when_every_limit_passes() -> None:
    config = _config()
    admitted = evaluate_preflight_admission(
        config,
        {
            "projected_cpu_core_hours": 10.0,
            "projected_wall_clock_days": 1.0,
            "projected_new_artifacts_gib": 1.0,
            "observed_peak_rss_gib": 2.0,
            "projected_free_disk_after_artifacts_gib": 40.0,
        },
    )
    assert admitted["status"] == "PASS"
    assert all(check["passed"] for check in admitted["checks"].values())

    stopped = evaluate_preflight_admission(
        config,
        {
            "projected_cpu_core_hours": 251.0,
            "projected_wall_clock_days": 1.0,
            "projected_new_artifacts_gib": 1.0,
            "observed_peak_rss_gib": 2.0,
            "projected_free_disk_after_artifacts_gib": 40.0,
        },
    )
    assert stopped["status"] == "STOP"
    assert stopped["checks"]["cpu_core_hours"]["passed"] is False


def test_preflight_contract_covers_both_heads_and_every_frozen_control() -> None:
    benchmark = _config()["benchmark"]
    assert benchmark["training_rows"] == 1024
    assert benchmark["validation_rows"] == 256
    assert benchmark["qubits"] == 8
    assert benchmark["data_reupload_layers"] == 2
    assert benchmark["statevector_concurrency"] == 1
    assert benchmark["persist_statevectors"] is False
    assert benchmark["persist_kernel_matrices"] is False
    assert benchmark["required_projected_heads"] == [
        "Q01b_cost",
        "FQK_feasibility",
    ]
    controls = " ".join(benchmark["required_controls"])
    for identifier in (
        "C01-T18",
        "C02-T02",
        "C03-T13",
        "C04-T28",
        "C05-T12",
        "C05-T17",
        "C06-T17",
        "A01-T04",
        "A02",
    ):
        assert identifier in controls


def test_governance_records_d009_without_unlocking_research_fit() -> None:
    required = {
        "README.md": "D009",
        "research_protocol.md": "D009",
        "docs/post_gate5_compute_preflight.md": "Accepted for one synthetic preflight",
        "docs/decision_log.md": "D009 accepted",
        "docs/research_execution_map.md": "D009",
    }
    for relative, phrase in required.items():
        assert phrase in (ROOT / relative).read_text(encoding="utf-8")
