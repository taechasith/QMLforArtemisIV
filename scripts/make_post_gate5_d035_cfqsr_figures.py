"""Generate paper-ready figures for the D035 CFQSR negative result."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "data/processed/reporting/post_gate5_d035_cfqsr"
FIGURE_ROOT = ROOT / "artifacts/research_figures"
REGISTRY = FIGURE_ROOT / "figure_registry.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    png = FIGURE_ROOT / f"{stem}.png"
    svg = FIGURE_ROOT / f"{stem}.svg"
    fig.savefig(png, dpi=320, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg


def _summary_map() -> dict[str, dict[str, str]]:
    return {row["model_id"]: row for row in _read_csv(RESULT_ROOT / "summary.csv")}


def _value(summary: dict[str, dict[str, str]], model: str, field: str) -> float:
    return float(summary[model][field])


def _figure_comparison(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    models = [
        "C06",
        "A02-STACK-q4",
        "A02-STACK-q6",
        "A02-STACK-q8",
        "CFQSR-04-N",
        "CFQSR-06-N",
        "CFQSR-08-N",
    ]
    labels = [model.replace("A02-STACK-", "A02-").replace("CFQSR-", "C-") for model in models]
    colors = [
        "#1b4965" if model == "C06" else "#e07a5f" if model.startswith("A02") else "#2a9d8f"
        for model in models
    ]
    y = np.arange(len(models))
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    for axis, field, title, xlabel in (
        (axes[0], "mean_nrmse", "Cost prediction", "Pooled OOF NRMSE (lower is better)"),
        (axes[1], "mean_mean_regret_m_s", "Selection consequence", "Mean regret (m/s; lower is better)"),
        (axes[2], "mean_mae", "Absolute error", "Mean absolute error (standardized cost)"),
    ):
        values = [_value(summary, model, field) for model in models]
        axis.barh(y, values, color=colors, edgecolor="#202020", linewidth=0.3)
        axis.set_yticks(y, labels if axis is axes[0] else [])
        axis.invert_yaxis()
        axis.set_title(title)
        axis.set_xlabel(xlabel)
        axis.grid(axis="x", alpha=0.25)
        if field == "mean_nrmse":
            axis.set_xscale("log")
        if field == "mean_mae":
            for index, value in enumerate(values):
                axis.text(value * (1.08 if field == "mean_nrmse" else 1.01), index, f"{value:.5g}", va="center", fontsize=7)
    fig.suptitle("D035 CFQSR development-only result: cross-fitted C06 correction did not improve C06", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Five grouped outer folds; four inner whole-group folds; 20 seeds; 39,000 development rows. A02-STACK is the identical-input classical control.", fontsize=9)
    return _save(fig, "post_gate5_d035_cfqsr_result_comparison")


def _figure_audit_resources(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    paired = _read_csv(RESULT_ROOT / "paired_comparison.csv")[0]
    audit = _read_csv(RESULT_ROOT / "inner_fold_audit.csv")
    assert all(int(row["group_intersection_count"]) == 0 for row in audit)
    assert len(audit) == 5 * 20 * 4

    per_seed = _read_csv(RESULT_ROOT / "per_seed_metrics.csv")
    c06_by_seed = {
        row["seed_index"]: float(row["nrmse"])
        for row in per_seed
        if row["model_id"] == "C06"
    }
    differences = np.asarray(
        [
            float(row["nrmse"]) - c06_by_seed[row["seed_index"]]
            for row in per_seed
            if row["model_id"] == "CFQSR-08-N"
        ]
    )
    runtime = result["runtime"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].axhline(0.0, color="#202020", linewidth=1)
    axes[0].boxplot(differences, widths=0.35, patch_artist=True, boxprops={"facecolor": "#2a9d8f"})
    axes[0].scatter(np.ones(differences.size), differences, color="#1b4965", s=18, alpha=0.8, zorder=3)
    axes[0].axhline(float(paired["lower_95"]), color="#bc4749", linestyle=":", label="95% paired interval")
    axes[0].axhline(float(paired["upper_95"]), color="#bc4749", linestyle=":")
    axes[0].set_xlim(0.5, 1.5)
    axes[0].set_xticks([1], ["CFQSR-08-N minus C06"])
    axes[0].set_ylabel("Seed-pooled NRMSE difference")
    axes[0].set_title("Paired endpoint evidence")
    axes[0].legend(fontsize=8)

    labels = ["CPU hours", "Wall hours", "Peak GiB", "Free disk GiB"]
    values = [
        float(runtime["cpu_seconds"]) / 3600.0,
        float(runtime["wall_clock_seconds"]) / 3600.0,
        float(runtime["peak_working_set_gib"]),
        float(runtime["free_disk_gib"]),
    ]
    positions = np.arange(len(labels))
    axes[1].barh(positions, values, color="#e07a5f")
    axes[1].set_yticks(positions, labels)
    axes[1].set_title("Reference-laptop resource record")
    axes[1].set_xlabel("Observed value")
    axes[1].set_xscale("log")
    axes[1].grid(axis="x", alpha=0.25)
    fig.suptitle("D035 cross-fitting audit and compute boundary", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "All 400 inner holdout audits had zero group overlap. Development-only evidence; calibration/final-test reads and Gate 6 runs were zero.", fontsize=9)
    return _save(fig, "post_gate5_d035_cfqsr_audit_resources")


def _update_registry(entries: list[dict[str, str]]) -> None:
    existing = _read_csv(REGISTRY)
    ids = {entry["figure_id"] for entry in entries}
    existing = [row for row in existing if row.get("figure_id") not in ids]
    fields = list(existing[0]) if existing else list(entries[0])
    for entry in entries:
        for field in entry:
            if field not in fields:
                fields.append(field)
    with REGISTRY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in [*existing, *entries]])


def main() -> None:
    summary = _summary_map()
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    paths = [_figure_comparison(summary), _figure_audit_resources(summary)]
    source_data = ";".join(
        [
            "data/processed/reporting/post_gate5_d035_cfqsr/campaign_result.json",
            "data/processed/reporting/post_gate5_d035_cfqsr/summary.csv",
            "data/processed/reporting/post_gate5_d035_cfqsr/per_seed_metrics.csv",
            "data/processed/reporting/post_gate5_d035_cfqsr/paired_comparison.csv",
            "data/processed/reporting/post_gate5_d035_cfqsr/inner_fold_audit.csv",
        ]
    )
    generator = "scripts/make_post_gate5_d035_cfqsr_figures.py"
    generator_hash = _sha256(ROOT / generator)
    definitions = [
        (
            "RFIG-056",
            "D035 CFQSR result comparison",
            "Results: development-only negative",
            "d035_result_comparison",
            "development_only_negative",
            "D035 CFQSR did not beat the frozen C06 predictor or provide a classical-control advantage.",
            "Development-only evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage.",
        ),
        (
            "RFIG-057",
            "D035 CFQSR paired audit and resources",
            "Methods and Results: leakage audit and compute",
            "d035_paired_audit_resources",
            "development_only_negative",
            "The paired CFQSR-08-N minus C06 interval is entirely positive and all inner folds are group-disjoint within the recorded laptop resource envelope.",
            "Development-only uncertainty and compute evidence; no NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 5 revision, Gate 6, or quantum advantage.",
        ),
    ]
    entries: list[dict[str, str]] = []
    for definition, (png, svg) in zip(definitions, paths):
        figure_id, title, phase, section, evidence_status, caption, claim_boundary = definition
        entries.append(
            {
                "figure_id": figure_id,
                "title": title,
                "phase": phase,
                "paper_section": section,
                "evidence_status": evidence_status,
                "source_data": source_data,
                "generator": generator,
                "png_path": str(png.relative_to(ROOT)).replace("\\", "/"),
                "png_sha256": _sha256(png),
                "png_bytes": str(png.stat().st_size),
                "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"),
                "svg_sha256": _sha256(svg),
                "svg_bytes": str(svg.stat().st_size),
                "caption": caption,
                "claim_boundary": claim_boundary,
                "campaign_source_commit": result["source_commit"],
                "reporting_source_commit": result["source_commit"],
                "accepted_d007_candidate_commit": "",
                "reporting_module_sha256": "",
                "reporting_script_sha256": "",
                "figure_generator_sha256": generator_hash,
            }
        )
    _update_registry(entries)
    print(json.dumps({"status": "complete", "figures": [entry["figure_id"] for entry in entries]}, indent=2))


if __name__ == "__main__":
    main()
