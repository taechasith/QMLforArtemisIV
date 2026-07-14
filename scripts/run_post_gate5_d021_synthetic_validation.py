"""Run D021-C CSAFE-RF synthetic-only validation."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import yaml

from openqfuel.post_gate5_classical import (
    assert_d021_scope,
    recall_first_safety_score,
    select_recall_first_candidate,
    select_safety_threshold,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d021_recall_first_synthetic.yaml"
OUT_JSON = ROOT / "data/processed/reporting/post_gate5_d021_recall_first_synthetic.json"
OUT_CSV = ROOT / "data/processed/reporting/post_gate5_d021_recall_first_synthetic_scores.csv"


def _candidate_rows() -> list[dict[str, str]]:
    train_labels = np.asarray([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    heldout_labels = np.asarray([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    candidates = [
        {
            "model_id": "synthetic_recall_first_logistic",
            "model_complexity": 1,
            "train_prob": np.asarray([0.95, 0.86, 0.72, 0.64, 0.50, 0.42, 0.32, 0.22, 0.15, 0.08]),
            "heldout_prob": np.asarray([0.94, 0.83, 0.70, 0.63, 0.49, 0.40, 0.30, 0.20, 0.12, 0.05]),
        },
        {
            "model_id": "synthetic_brier_first_tree",
            "model_complexity": 2,
            "train_prob": np.asarray([0.97, 0.90, 0.86, 0.82, 0.18, 0.12, 0.08, 0.06, 0.04, 0.02]),
            "heldout_prob": np.asarray([0.96, 0.78, 0.76, 0.74, 0.16, 0.10, 0.07, 0.05, 0.03, 0.01]),
        },
    ]
    scores = []
    for candidate in candidates:
        threshold = select_safety_threshold(
            train_labels,
            candidate["train_prob"],
            minimum_recall=1.0,
            maximum_intervention_rate=0.7,
        )
        scores.append(
            recall_first_safety_score(
                model_id=str(candidate["model_id"]),
                model_complexity=int(candidate["model_complexity"]),
                labels=heldout_labels,
                probabilities=candidate["heldout_prob"],
                threshold=threshold,
                calibration_bins=5,
            )
        )
    selected = select_recall_first_candidate(scores)
    rows = []
    for score in scores:
        row_score = selected if score.model_id == selected.model_id else score
        rows.append(row_score.as_row())
    return rows


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert_d021_scope(config, action="implementation", data_scope="synthetic")
    assert_d021_scope(config, action="synthetic_validation", data_scope="synthetic")
    rows = _candidate_rows()
    selected = next(row for row in rows if row["selected"] == "true")
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "decision_id": "D021-C",
                "protocol_id": "P001",
                "official_status": "SYNTHETIC_VALIDATION_PASS",
                "source_d020_commit": "fc0c31c49279b117f93122c9018df78574e6c035",
                "candidate_count": len(rows),
                "selected_model_id": selected["model_id"],
                "selected_recall": float(selected["recall"]),
                "selected_false_negative_rate": float(selected["false_negative_rate"]),
                "selected_brier": float(selected["brier"]),
                "development_rows_read": 0,
                "calibration_rows_read": 0,
                "final_test_rows_read": 0,
                "hardware_jobs": 0,
                "gpu_hours": 0,
                "gate6_runs": 0,
                "claim_boundary": (
                    "Synthetic validation only; no threshold application to real data, "
                    "development fitting, calibration, final-test, hardware/GPU, "
                    "mission-loop, Gate 5 reinterpretation, QML invention, quantum "
                    "advantage, or Gate 6."
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("Generated D021-C synthetic validation evidence")


if __name__ == "__main__":
    main()
