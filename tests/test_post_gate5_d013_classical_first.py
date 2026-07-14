from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d013_classical_first_protocol.yaml"
LEDGER = ROOT / "docs/qml_invention_readiness_ledger.md"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_d013c_is_planning_only_and_keeps_locked_splits_and_gate6_closed() -> None:
    config = _config()
    assert config["decision_id"] == "D013-C"
    assert config["status"] == "accepted_planning_only_no_execution"
    authority = config["authority"]
    assert authority["planning_authorized"] is True
    for key in (
        "implementation_authorized",
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
    assert "D014" in authority["next_required_decision"]


def test_d013c_records_qml_invention_goal_without_unsupported_nasa_claim() -> None:
    config = _config()
    goal = config["long_term_invention_goal"]
    assert "new QML method" in goal["objective"]
    assert "NASA-relevant" in goal["objective"]
    assert "Do not claim NASA used a specific QML method" in (
        goal["nasa_claim_discipline"]
    )
    assert "scientific correctness" in goal["scientific_correctness_priority"]
    assert "Every completed result" in goal["evidence_label_rule"]
    successor = config["selected_successor"]
    assert successor["decision_id"] == "D014-C"
    assert successor["status"] == "accepted_freeze_proposal_no_execution"
    assert successor["gate6_authorized"] is False


def test_invention_readiness_ledger_labels_useful_and_prohibited_uses() -> None:
    config = _config()
    assert config["invention_readiness_labels"]["ledger"] == (
        "docs/qml_invention_readiness_ledger.md"
    )
    text = LEDGER.read_text(encoding="utf-8")
    for phrase in (
        "Gate 5 / D007 Q01",
        "D011-R1 Q01b",
        "D011-R1 FQK",
        "Useful Signal For Invention",
        "Prohibited Use",
        "Do not claim NASA used a specific QML method",
    ):
        assert phrase in text


def test_d013c_docs_are_registered_in_project_governance() -> None:
    required = {
        "research_protocol.md": "D013-C planning accepted",
        "README.md": "D013-C is accepted as that planning-only recommended path",
        "docs/decision_log.md": "D013-C accepted - classical-first planning",
        "docs/computational_methodology.md": "D013-C classical-first planning accepted",
        "docs/research_execution_map.md": "D031-C final claim/release review READY",
        "docs/post_gate5_d013_classical_first_protocol.md": (
            "Planning-only accepted; no experiment authorized"
        ),
        "docs/post_gate5_d014_classical_first_freeze.md": (
            "Freeze proposal accepted; no implementation or experiment authorized"
        ),
    }
    for relative, phrase in required.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert phrase in text
        assert "Gate 6" in text
