from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d012_future_protocol_discussion.yaml"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_d012_is_discussion_only_and_keeps_gate6_locked() -> None:
    config = _config()
    assert config["decision_id"] == "D012"
    assert config["status"] == "opened_discussion_only"
    authority = config["authority"]
    assert authority["discussion_authorized"] is True
    for key in (
        "experiment_authorized",
        "refit_authorized",
        "rerank_authorized",
        "retry_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate5_reinterpretation_authorized",
        "gate6_authorized",
    ):
        assert authority[key] is False
    assert "D013" in authority["next_required_decision"]


def test_d012_preserves_d011_negative_evidence_and_future_boundary() -> None:
    config = _config()
    assert config["locked_findings"]["gate5_result"] == "technical_FAIL_accepted"
    assert config["locked_findings"]["q01b"]["status"] == (
        "valid_exploratory_negative"
    )
    assert config["locked_findings"]["q01b"]["qualified_dequantization_regimes"] == 0
    assert config["locked_findings"]["fqk"]["status"] == (
        "valid_exploratory_negative"
    )
    assert config["locked_findings"]["fqk"]["strongest_comparator_id"] == "C02-T02"
    candidates = config["future_protocol_candidates"]
    assert [candidate["id"] for candidate in candidates] == [
        "D012-A",
        "D012-B",
        "D012-C",
    ]
    assert all(
        candidate["authorization_status"] == "discussion_only"
        for candidate in candidates
    )
    successor = config["selected_successor"]
    assert successor["decision_id"] == "D013-C"
    assert successor["selected_candidate"] == "D012-C"
    assert successor["gate6_authorized"] is False
    assert "does not authorize new experiments" in config["claim_boundary"]


def test_d012_docs_and_top_level_protocol_record_gate6_lock() -> None:
    required = {
        "docs/post_gate5_d012_future_protocol_discussion.md": (
            "Discussion-only opened; Gate 6 unauthorized"
        ),
        "research_protocol.md": "D012 future-protocol discussion opened",
        "README.md": "D012 is now open as discussion-only",
        "docs/decision_log.md": "D012 opened - future protocol discussion",
        "docs/research_execution_map.md": "D016-C accepted for one clean-source synthetic CRES/CSAFE compute preflight",
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
