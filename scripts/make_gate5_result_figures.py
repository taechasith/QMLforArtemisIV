"""Generate and register the predeclared development-only Gate 5 figures."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from openqfuel.gate5 import validate_development_output_path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
REPORTING = ROOT / "data/processed/reporting"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"
INK = "#16222e"
BLUE = "#2166ac"
ORANGE = "#d6604d"
GREEN = "#1b9e77"
GRAY = "#718096"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, default=EXPERIMENTS)
    parser.add_argument("--reporting-dir", type=Path, default=REPORTING)
    return parser.parse_args()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / f"{stem}.png"
    svg = OUTPUT / f"{stem}.svg"
    fig.savefig(png, dpi=220, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png, svg


def _learning_curve() -> tuple[Path, Path]:
    trigger = json.loads(
        (EXPERIMENTS / "gate5_trigger_summary.json").read_text(encoding="utf-8")
    )
    rows = (
        _rows(EXPERIMENTS / "phase1_tuning_results.csv")
        if trigger.get("decision_available")
        else []
    )
    grouped: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    for row in rows:
        if row["status"] != "complete" or row["rung_samples"] == "":
            continue
        label = row["family_id"]
        if row["view"] == "compressed_c05":
            label = "C05 compressed"
        grouped[(label, row["view"], int(row["rung_samples"]))].append(
            float(row["pooled_oof_nrmse"])
        )
    fig, ax = plt.subplots(figsize=(9.2, 5.4), constrained_layout=True)
    colors = {
        "Q01": BLUE,
        "Q02": ORANGE,
        "Q03": GREEN,
        "A01": GRAY,
        "C05 compressed": "#7b3294",
    }
    for label in colors:
        points = sorted(
            (rung, float(np.mean(values)))
            for (candidate, _, rung), values in grouped.items()
            if candidate == label
        )
        if points:
            ax.plot(
                [point[0] for point in points],
                [point[1] for point in points],
                marker="o",
                linewidth=2,
                color=colors[label],
                label=label,
            )
    if grouped:
        ax.set_xscale("log", base=2)
        ax.set_xticks([128, 256, 512, 1024], ["128", "256", "512", "1,024"])
        ax.set_xlabel("Training rows per grouped-CV fold")
        ax.set_ylabel("Mean pooled OOF NRMSE across authorized trials")
        ax.set_title("Gate 5 development learning curves and matched controls")
        ax.grid(alpha=0.22)
        ax.legend(frameon=False, ncols=3)
    else:
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "Decision unavailable: source-bound campaign evidence is incomplete",
            ha="center",
            va="center",
            color=INK,
            fontsize=13,
        )
    return _save(fig, "gate5_development_learning_curves")


def _seed_summary() -> tuple[Path, Path]:
    trigger = json.loads(
        (EXPERIMENTS / "gate5_trigger_summary.json").read_text(encoding="utf-8")
    )
    rows = _rows(REPORTING / "gate5_model_summary.csv")
    eligible = [
        row
        for row in rows
        if trigger.get("decision_available")
        and row.get("mean_pooled_oof_nrmse")
        and row.get("all_twenty_seeds_eligible", "").lower() == "true"
    ]
    eligible.sort(key=lambda row: float(row["mean_pooled_oof_nrmse"]))
    fig, ax = plt.subplots(figsize=(9.2, 5.4), constrained_layout=True)
    labels = [row["family_id"] for row in eligible]
    values = [float(row["mean_pooled_oof_nrmse"]) for row in eligible]
    colors = [BLUE if label.startswith("C") else ORANGE for label in labels]
    bars = ax.bar(labels, values, color=colors, edgecolor="white")
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    if eligible:
        ax.set_ylabel("20-seed mean pooled OOF NRMSE")
        ax.set_title("Gate 5 selected development configurations")
        ax.grid(axis="y", alpha=0.22)
        ax.grid(axis="x", visible=False)
    else:
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "No source-validated complete 20-seed model summary is available",
            ha="center",
            va="center",
            color=INK,
            fontsize=13,
        )
    return _save(fig, "gate5_selected_model_seed_summary")


def _trigger_regime() -> tuple[Path, Path]:
    trigger = json.loads(
        (EXPERIMENTS / "gate5_trigger_summary.json").read_text(encoding="utf-8")
    )
    rows = [
        row
        for row in _rows(REPORTING / "gate5_regime_trigger.csv")
        if trigger.get("decision_available")
        and row.get("qml_mean_nrmse")
        and row.get("qualified_residual_regime", "").lower() == "true"
    ]
    fig, ax = plt.subplots(figsize=(9.2, 5.4), constrained_layout=True)
    if rows:
        row = min(
            rows,
            key=lambda item: float(item["qml_minus_classical_ci_upper"]),
        )
        labels = ["QML", "Strongest classical", "A01", "Compressed C05"]
        values = [
            float(row["qml_mean_nrmse"]),
            float(row["classical_mean_nrmse"]),
            float(row["a01_mean_nrmse"]),
            float(row["compressed_c05_mean_nrmse"]),
        ]
        ax.bar(labels, values, color=[ORANGE, BLUE, GRAY, "#7b3294"])
        ax.set_ylabel("20-seed pooled regime NRMSE")
        ax.set_title(
            f"Qualified preregistered cell: {row['dimension']} = {row['value']}"
        )
        ax.tick_params(axis="x", rotation=12)
        ax.grid(axis="y", alpha=0.22)
        ax.grid(axis="x", visible=False)
    else:
        ax.axis("off")
        ax.text(
            0.5,
            0.60,
            (
                "Decision unavailable: regime evidence is not source-valid"
                if not trigger.get("decision_available")
                else "No regime cell satisfied every preregistered condition"
            ),
            ha="center",
            va="center",
            color=INK,
            fontsize=13,
        )
    verdict = trigger.get("technical_trigger_status", "UNAVAILABLE")
    fig.text(
        0.5,
        0.01,
        "Preregistered Gate 5 trigger: "
        f"{verdict}. Calibration reads = {trigger.get('calibration_rows_read')}; "
        f"final-test reads = {trigger.get('final_test_rows_read')}.",
        ha="center",
        color=INK,
        fontsize=9,
    )
    return _save(fig, "gate5_algorithm_trigger_regime_control")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _register(paths: list[tuple[str, str, str, str, str, tuple[Path, Path]]]) -> None:
    existing = _rows(REGISTRY)
    fields = list(existing[0])
    by_id = {row["figure_id"]: row for row in existing}
    for figure_id, title, source, caption, boundary, (png, svg) in paths:
        by_id[figure_id] = {
            "figure_id": figure_id,
            "title": title,
            "phase": "Gate 5 development benchmark",
            "paper_section": "Results: preregistered algorithm trigger",
            "evidence_status": "development_only_model_evidence",
            "source_data": source,
            "generator": "scripts/make_gate5_result_figures.py",
            "png_path": str(png.relative_to(ROOT)),
            "png_sha256": _sha(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": str(svg.relative_to(ROOT)),
            "svg_sha256": _sha(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": caption,
            "claim_boundary": boundary,
        }
    ordered = sorted(
        by_id.values(), key=lambda row: int(row["figure_id"].split("-")[1])
    )
    temporary = REGISTRY.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    temporary.replace(REGISTRY)


def main() -> None:
    global EXPERIMENTS, REPORTING
    args = parse_args()
    EXPERIMENTS = args.experiment_dir.resolve()
    REPORTING = args.reporting_dir.resolve()
    validate_development_output_path(ROOT, EXPERIMENTS)
    validate_development_output_path(ROOT, REPORTING)
    validate_development_output_path(ROOT, OUTPUT)
    learning = _learning_curve()
    seeds = _seed_summary()
    regime = _trigger_regime()
    _register(
        [
            (
                "RFIG-021",
                "Gate 5 development learning curves and matched controls",
                _source_path(EXPERIMENTS / "phase1_tuning_results.csv"),
                "Pooled development-only learning curves retain identical rungs and matched PCA dimensions.",
                "Development model-selection evidence only; no calibration, final-test, mission, or hardware-advantage claim.",
                learning,
            ),
            (
                "RFIG-022",
                "Gate 5 selected model 20-seed summary",
                _source_path(REPORTING / "gate5_model_summary.csv"),
                "Selected candidate families are summarized over the 20 frozen development seed indices.",
                "Development stability evidence only; the chart cannot establish final-test or mission performance.",
                seeds,
            ),
            (
                "RFIG-023",
                "Gate 5 algorithm-trigger regime controls",
                ";".join(
                    (
                        _source_path(REPORTING / "gate5_regime_trigger.csv"),
                        _source_path(EXPERIMENTS / "gate5_trigger_summary.json"),
                    )
                ),
                "The preregistered trigger is shown beside the strongest classical and tuned dequantization controls.",
                "A passing development trigger could support human authorization of one algorithm study only; it is not quantum advantage or flight evidence.",
                regime,
            ),
        ]
    )


if __name__ == "__main__":
    main()
