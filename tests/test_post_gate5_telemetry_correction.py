from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

import pytest
import yaml

from openqfuel.gate4 import FinalTestAccessError
from openqfuel.post_gate5 import (
    ProcessMemoryObservation,
    assert_post_gate5_scope,
    equivalent_preflight_work_units,
    process_memory_observation,
    validate_memory_telemetry,
)


ROOT = Path(__file__).resolve().parents[1]
CORRECTION_CONFIG = ROOT / "configs/post_gate5_telemetry_correction.yaml"
BASE_CONFIG = ROOT / "configs/post_gate5_preflight.yaml"


def _correction() -> dict:
    return yaml.safe_load(CORRECTION_CONFIG.read_text(encoding="utf-8"))


def _base() -> dict:
    return yaml.safe_load(BASE_CONFIG.read_text(encoding="utf-8"))


def test_d010_authorizes_only_telemetry_and_one_synthetic_rerun() -> None:
    config = _correction()
    assert config["decision_id"] == "D010"
    assert config["protocol_id"] == "P001"
    assert config["authority"]["corrected_decision"] == "D009"
    assert config["authority"]["authorized_rerun_attempt"] == 2
    assert config["locks"]["rerun_limit"] == 1
    assert config["preflight_execution_authorized"] is True
    assert config["research_data_fitting_authorized"] is False
    assert config["exploratory_execution_authorized"] is False
    assert config["locks"]["d009_failure_evidence_immutable"] is True
    assert config["locks"]["development_rows_read"] == 0
    assert config["locks"]["calibration_rows_read"] == 0
    assert config["locks"]["final_test_rows_read"] == 0
    assert config["locks"]["gpu_execution_authorized"] is False
    assert config["locks"]["gate6_authorized"] is False


def test_d010_scope_guard_allows_only_synthetic_preflight() -> None:
    config = _correction()
    assert_post_gate5_scope(
        config, action="compute_preflight", data_scope="synthetic"
    )
    with pytest.raises(PermissionError, match="research-data fitting"):
        assert_post_gate5_scope(
            config, action="preflight", data_scope="development"
        )
    with pytest.raises(FinalTestAccessError, match="calibration remains locked"):
        assert_post_gate5_scope(
            config, action="compute_preflight", data_scope="calibration"
        )
    with pytest.raises(FinalTestAccessError, match="final_test remains locked"):
        assert_post_gate5_scope(
            config, action="compute_preflight", data_scope="final_test"
        )
    with pytest.raises(FinalTestAccessError, match="gate6 remains locked"):
        assert_post_gate5_scope(
            config, action="compute_preflight", data_scope="gate6"
        )


def test_d010_pins_the_unchanged_d009_contract_blob() -> None:
    correction = _correction()
    binding = correction["base_preflight_contract"]
    blob = subprocess.run(
        ["git", "show", f"{binding['source_commit']}:{binding['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert hashlib.sha256(blob).hexdigest() == binding["git_blob_sha256"]
    assert binding["inherited_unchanged_sections"] == [
        "benchmark",
        "campaign_projection",
        "ceilings",
    ]
    assert equivalent_preflight_work_units(_base()) == pytest.approx(477.5)


def test_typed_process_memory_observation_is_positive_and_consistent() -> None:
    observation = process_memory_observation()
    assert observation.current_bytes > 0
    assert observation.peak_bytes >= observation.current_bytes
    assert observation.backend in {
        "windows_psapi_typed",
        "posix_getrusage_peak",
    }


def test_memory_validation_passes_within_frozen_tolerance() -> None:
    result = validate_memory_telemetry(
        ProcessMemoryObservation(
            current_bytes=100 * 1024**2,
            peak_bytes=120 * 1024**2,
            backend="test",
        ),
        independent_current_bytes=110 * 1024**2,
        absolute_tolerance_bytes=64 * 1024**2,
        relative_tolerance=0.25,
    )
    assert result["status"] == "PASS"
    assert result["counters_consistent"] is True
    assert result["allowed_difference_bytes"] == 64 * 1024**2


def test_memory_validation_stops_on_large_difference_or_bad_peak() -> None:
    different = validate_memory_telemetry(
        ProcessMemoryObservation(
            current_bytes=10 * 1024**2,
            peak_bytes=12 * 1024**2,
            backend="test",
        ),
        independent_current_bytes=200 * 1024**2,
        absolute_tolerance_bytes=64 * 1024**2,
        relative_tolerance=0.25,
    )
    inconsistent = validate_memory_telemetry(
        ProcessMemoryObservation(
            current_bytes=100 * 1024**2,
            peak_bytes=90 * 1024**2,
            backend="test",
        ),
        independent_current_bytes=100 * 1024**2,
        absolute_tolerance_bytes=64 * 1024**2,
        relative_tolerance=0.25,
    )
    assert different["status"] == "STOP"
    assert inconsistent["status"] == "STOP"
    assert inconsistent["counters_consistent"] is False


def test_d010_governance_keeps_research_fit_locked() -> None:
    required = {
        "README.md": "D010 is now accepted",
        "research_protocol.md": "D010 is accepted prospectively",
        "docs/post_gate5_telemetry_correction.md": "one unchanged synthetic",
        "docs/decision_log.md": "D010 accepted - telemetry-only",
        "docs/research_execution_map.md": "D010 changes telemetry",
        "docs/computational_methodology.md": "D010 telemetry correction freeze",
    }
    for relative, phrase in required.items():
        assert phrase in (ROOT / relative).read_text(encoding="utf-8")
