from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_d028_config_is_release_documentation_only() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_d028_release_support_cards.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert config["decision_id"] == "D028-C"
    assert config["scope"]["release_documentation_only"] is True
    assert config["scope"]["release_authorized"] is False
    for key, value in config["scope"].items():
        if key.endswith("_authorized"):
            assert value is False


def test_d028_result_and_cards_preserve_release_boundary() -> None:
    result = json.loads(
        (
            ROOT
            / "data/processed/reporting/post_gate5_d028_release_support_cards.json"
        ).read_text(encoding="utf-8")
    )
    assert result["decision_id"] == "D028-C"
    assert result["official_status"] == "RELEASE_SUPPORT_CARDS_READY"
    assert result["release_authorized"] is False
    assert result["gate6_authorized"] is False
    assert result["qml_gate6_candidate"] is False
    for key in (
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "mission_loop_runs",
        "gate6_runs",
    ):
        assert result[key] == 0

    rows = read_csv(
        ROOT / "data/processed/reporting/post_gate5_d028_release_support_cards.csv"
    )
    assert {row["card_id"] for row in rows} == {
        "model",
        "simulator",
        "data",
        "limitations",
    }
    for row in rows:
        assert (ROOT / row["path"]).is_file()


def test_d028_docs_are_registered() -> None:
    expected = {
        "docs/release_model_card.md": "No trained model is released",
        "docs/release_simulator_card.md": "research simulator evidence only",
        "docs/release_data_card.md": "Calibration and final-test access remain locked",
        "docs/release_limitation_card.md": "No QML Gate 6 mission candidate",
        "research_protocol.md": "D028-C",
        "README.md": "D028-C",
        "docs/decision_log.md": "D028-C",
        "docs/research_execution_map.md": "D028-C",
        "docs/computational_methodology.md": "D028-C",
    }
    for relative, needle in expected.items():
        assert needle in (ROOT / relative).read_text(encoding="utf-8")
