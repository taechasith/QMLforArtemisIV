"""Generate D023-C CSAFE-RF development-only audit evidence and RFIG-042."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d023_recall_first_development.yaml"
D017_SUMMARY = ROOT / "data/processed/reporting/post_gate5_d017_classical_first/campaign_summary.json"
D017_CSAFE = ROOT / "data/processed/reporting/post_gate5_d017_classical_first/csafe_summary.csv"
RESULT = ROOT / "data/processed/reporting/post_gate5_d023_recall_first_development.json"
SCORES = ROOT / "data/processed/reporting/post_gate5_d023_recall_first_development_scores.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GOLD = "#E69F00"
RED = "#B24A3B"
GRAY = "#68737D"
LIGHT = "#D9E1E8"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d023-development-audit-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _audit_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    complexity = config["audit_rule"]["model_complexity"]
    eligible = set(config["audit_rule"]["eligible_models"])
    rows = []
    for row in _read_csv(D017_CSAFE):
        model_id = row["model_id"]
        if model_id not in eligible:
            continue
        rows.append(
            {
                "model_id": model_id,
                "mean_recall": float(row["mean_recall"]),
                "mean_false_negative_rate": float(row["mean_false_negative_rate"]),
                "mean_brier": float(row["mean_brier"]),
                "mean_auroc": float(row["mean_auroc"]),
                "mean_intervention_rate": float(row["mean_intervention_rate"]),
                "model_complexity": int(complexity[model_id]),
                "selected": "false",
            }
        )
    selected = min(
        rows,
        key=lambda item: (
            -float(item["mean_recall"]),
            float(item["mean_false_negative_rate"]),
            float(item["mean_brier"]),
            int(item["model_complexity"]),
            str(item["model_id"]),
        ),
    )
    for row in rows:
        if row["model_id"] == selected["model_id"]:
            row["selected"] = "true"
    return sorted(rows, key=lambda item: item["model_complexity"])


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d023_recall_first_development_audit.png"
    svg = OUTPUT / "post_gate5_d023_recall_first_development_audit.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return png, svg


def _draw(rows: list[dict[str, Any]], selected_model: str) -> tuple[Path, Path]:
    labels = [str(row["model_id"]).replace("_", "\n") for row in rows]
    recall = np.asarray([float(row["mean_recall"]) for row in rows])
    fnr = np.asarray([float(row["mean_false_negative_rate"]) for row in rows])
    brier = np.asarray([float(row["mean_brier"]) for row in rows])
    x = np.arange(len(rows))
    width = 0.23
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    fig.subplots_adjust(top=0.80, bottom=0.24)
    fig.text(
        0.08,
        0.96,
        "D023-C CSAFE-RF development-only recall-first audit",
        ha="left",
        va="top",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.08,
        0.91,
        "Uses committed D017 development metrics only; this is post-D017-informed and cannot rescue D017 or open Gate 6.",
        ha="left",
        va="top",
        fontsize=9,
        color=GRAY,
    )
    ax.bar(x - width, recall, width, label="Mean recall", color=BLUE)
    ax.bar(x, fnr, width, label="Mean false-negative rate", color=RED)
    ax.bar(x + width, brier, width, label="Mean Brier", color=GOLD)
    ax.set_ylim(0.0, 1.05)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Mean development metric")
    selected_index = next(index for index, row in enumerate(rows) if row["model_id"] == selected_model)
    ax.annotate(
        f"Selected by recall-first rule:\n{selected_model}",
        xy=(selected_index - width, recall[selected_index]),
        xytext=(selected_index - 0.55, 0.97),
        arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.1},
        ha="left",
        va="top",
        fontsize=8.5,
        color=INK,
    )
    for bars in ax.containers:
        ax.bar_label(bars, fmt="%.3f", padding=2, fontsize=7.5)
    ax.legend(loc="upper right", frameon=False)
    ax.grid(axis="y", color=LIGHT, linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    fig.text(
        0.08,
        0.03,
        "Counters: no refit, no new threshold application, calibration/final-test/Gate 6 reads = 0.",
        ha="left",
        va="bottom",
        fontsize=8.5,
        color=GRAY,
    )
    return _save(fig)


def _register(png: Path, svg: Path, source_commit: str) -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_id = {row["figure_id"]: row for row in rows}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-042",
            "title": "D023-C CSAFE-RF development-only recall-first audit",
            "phase": "Post-Gate-5 CSAFE-RF development audit",
            "paper_section": "Discussion: future safety objective",
            "evidence_status": "development_only_recall_first_selection_audit",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{SCORES.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d023_development_audit.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D023-C applies the frozen CSAFE-RF recall-first rule to committed D017 development metrics without refitting.",
            "claim_boundary": "Development-only post-D017-informed audit; no refit, no threshold application to real data, no calibration, final-test, hardware/GPU, mission, Gate 5 reinterpretation, QML invention, quantum advantage, or Gate 6.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-042"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D023-C":
        raise ValueError("D023-C config required")
    d017 = json.loads(D017_SUMMARY.read_text(encoding="utf-8"))
    for field in ("calibration_rows_read", "final_test_rows_read", "hardware_jobs_submitted", "gate6_runs"):
        if int(d017[field]) != 0:
            raise PermissionError(f"D017 source violates {field}")
    rows = _audit_rows(config)
    selected = next(row for row in rows if row["selected"] == "true")
    _write_csv(SCORES, rows)
    result = {
        "decision_id": "D023-C",
        "protocol_id": "P001",
        "official_status": "DEVELOPMENT_AUDIT_COMPLETE",
        "source_d017_commit": d017["source_commit"],
        "selected_model_id": selected["model_id"],
        "selected_mean_recall": selected["mean_recall"],
        "selected_mean_false_negative_rate": selected["mean_false_negative_rate"],
        "selected_mean_brier": selected["mean_brier"],
        "candidate_count": len(rows),
        "development_metric_rows_read": len(_read_csv(D017_CSAFE)),
        "new_model_fits": 0,
        "threshold_applications_to_real_data": 0,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs": 0,
        "gpu_hours": 0,
        "gate6_runs": 0,
        "claim_boundary": config["outcome"]["claim_boundary"],
    }
    _write_json(RESULT, result)
    png, svg = _draw(rows, str(selected["model_id"]))
    _register(png, svg, d017["source_commit"])
    print("Generated D023-C development-only recall-first audit")


if __name__ == "__main__":
    main()
