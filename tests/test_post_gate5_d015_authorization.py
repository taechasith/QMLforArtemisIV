from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d015_implementation_synthetic_validation.yaml"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_d015c_authorizes_only_implementation_and_synthetic_validation() -> None:
    config = _config()
    assert config["decision_id"] == "D015-C"
    assert config["status"] == "accepted_implementation_and_synthetic_validation_only"
    authority = config["authority"]
    assert authority["implementation_authorized"] is True
    assert authority["synthetic_validation_authorized"] is True
    for key in (
        "development_data_fitting_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "refit_authorized",
        "rerank_authorized",
        "retry_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate5_reinterpretation_authorized",
        "qml_invention_claim_authorized",
        "gate6_authorized",
    ):
        assert authority[key] is False
    assert "D016" in authority["next_required_decision"]


def test_d015c_limits_validation_to_synthetic_arrays() -> None:
    config = _config()
    assert config["authorized_scope"]["synthetic_validation"]["allowed_rows"] == (
        "synthetic arrays only"
    )
    checks = config["authorized_scope"]["synthetic_validation"]["required_checks"]
    assert "fold-local preprocessing does not fit on validation rows" in checks
    assert "locked splits and Gate 6 guards fail closed" in checks
    assert "new QML architecture implementation" in config["prohibited_scope"]


def test_d015c_docs_are_registered() -> None:
    required = {
        "docs/post_gate5_d015_implementation_synthetic_validation.md": (
            "Implementation and synthetic validation authorized; no data fitting"
        ),
        "configs/post_gate5_d015_implementation_synthetic_validation.yaml": (
            "accepted_implementation_and_synthetic_validation_only"
        ),
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
