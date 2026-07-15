"""Generate paper-ready figures for the D044 NIFRK campaign."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "data/processed/reporting/post_gate5_d044_nifrk"
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


def _figure_comparison(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    models = [
        "C06",
        "TWO-RBF-04-NL",
        "TWO-RBF-06-NL",
        "TWO-RBF-08-NL",
        "NIFRK-04-NL",
        "NIFRK-06-NL",
        "NIFRK-08-NL",
    ]
    labels = ["C06", "2RBF q4", "2RBF q6", "2RBF q8", "NIFRK q4", "NIFRK q6", "NIFRK q8"]
    colors = [
        "#1b4965" if model == "C06" else "#e07a5f" if model.startswith("TWO-RBF") else "#2a9d8f"
        for model in models
    ]
    y = np.arange(len(models))
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    for axis, field, title, xlabel in (
        (axes[0], "mean_nrmse", "Cost prediction", "Pooled OOF NRMSE (lower is better)"),
        (axes[1], "mean_mean_regret_m_s", "Selection consequence", "Mean regret (m/s; lower is better)"),
        (axes[2], "mean_mae", "Absolute error", "Mean absolute error (standardized cost)"),
    ):
        values = [float(summary[model][field]) for model in models]
        axis.barh(y, values, color=colors, edgecolor="#202020", linewidth=0.3)
        axis.set_yticks(y, labels if axis is axes[0] else [])
        axis.invert_yaxis()
        axis.set_title(title)
        axis.set_xlabel(xlabel)
        axis.grid(axis="x", alpha=0.25)
        if field == "mean_nrmse":
            axis.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))
            axis.text(
                0.02,
                0.04,
                f"C06={float(summary['C06']['mean_nrmse']):.6f}; NIFRK q8={float(summary['NIFRK-08-NL']['mean_nrmse']):.6f}",
                transform=axis.transAxes,
                fontsize=8,
            )
        if field == "mean_mae":
            for index, value in enumerate(values):
                axis.text(value * 1.01, index, f"{value:.5g}", va="center", fontsize=7)
    fig.suptitle("D044 NIFRK development result: nonlinear interaction stacking", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "q=4/6/8; five grouped outer folds; four inner whole-group folds; 20 seeds; 39,000 development rows. The same quadratic map was used for candidate and control.", fontsize=9)
    fig.subplots_adjust(bottom=0.18)
    return _save(fig, "post_gate5_d044_nifrk_result_comparison")


def _figure_audit_resources(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    paired = _read_csv(RESULT_ROOT / "paired_comparison.csv")[0]
    channel_audit = _read_csv(RESULT_ROOT / "channel_audit.csv")
    interaction_audit = _read_csv(RESULT_ROOT / "interaction_audit.csv")
    inner_audit = _read_csv(RESULT_ROOT / "inner_fold_audit.csv")
    aggregate = [row for row in interaction_audit if row["inner_fold"] == "aggregate"]
    q8 = [row for row in channel_audit if int(row["q"]) == 8]
    assert len(channel_audit) == 300
    assert len(aggregate) == 300
    assert len(q8) == 100
    assert len(inner_audit) == 400
    assert all(int(row["validation_outcomes_used"]) == 0 for row in channel_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in interaction_audit)
    assert all(int(row["group_intersection_count"]) == 0 for row in [row for row in interaction_audit if row["inner_fold"] != "aggregate"])
    assert all(row["feature_map"] == "[1,u,v,u*v,u^2,v^2]" for row in aggregate)
    assert all(row["channel_source"] == "same_cross_fitted_c06_residual" for row in channel_audit)

    per_seed = _read_csv(RESULT_ROOT / "per_seed_metrics.csv")
    c06_by_seed = {row["seed_index"]: float(row["nrmse"]) for row in per_seed if row["model_id"] == "C06"}
    differences = np.asarray([float(row["nrmse"]) - c06_by_seed[row["seed_index"]] for row in per_seed if row["model_id"] == "NIFRK-08-NL"])
    runtime = result["runtime"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    axes[0].axhline(0.0, color="#202020", linewidth=1)
    axes[0].boxplot(differences, widths=0.35, patch_artist=True, boxprops={"facecolor": "#2a9d8f"})
    axes[0].scatter(np.ones(differences.size), differences, color="#1b4965", s=18, alpha=0.8, zorder=3)
    axes[0].axhline(float(paired["lower_95"]), color="#bc4749", linestyle=":", label="95% paired interval")
    axes[0].axhline(float(paired["upper_95"]), color="#bc4749", linestyle=":")
    axes[0].set_xlim(0.5, 1.5)
    axes[0].set_xticks([1], ["NIFRK q8 minus C06"])
    axes[0].set_ylabel("Seed-pooled NRMSE difference")
    axes[0].set_title("Primary paired endpoint")
    axes[0].legend(fontsize=8)

    candidate_norms = [float(row["candidate_interaction_norm"]) for row in q8]
    control_norms = [float(row["control_interaction_norm"]) for row in q8]
    axes[1].hist(candidate_norms, bins=10, alpha=0.75, color="#2a9d8f", edgecolor="#202020", label="fidelity/RBF25")
    axes[1].hist(control_norms, bins=10, alpha=0.65, color="#e07a5f", edgecolor="#202020", label="RBF25/RBF50")
    axes[1].set_xlabel("Interaction coefficient norm (q=8)")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Training-only interaction audit")
    axes[1].legend(fontsize=8)
    axes[1].grid(axis="y", alpha=0.25)

    labels = ["CPU h", "Wall h", "Peak GiB", "Free GiB"]
    values = [float(runtime["cpu_seconds"]) / 3600.0, float(runtime["wall_clock_seconds"]) / 3600.0, float(runtime["peak_working_set_gib"]), float(runtime["free_disk_gib"])]
    axes[2].barh(np.arange(len(labels)), values, color="#1b4965")
    axes[2].set_yticks(np.arange(len(labels)), labels)
    axes[2].set_xscale("log")
    axes[2].set_title("Reference-laptop resources")
    axes[2].set_xlabel("Observed value")
    axes[2].tick_params(axis="y", labelsize=8)
    axes[2].grid(axis="x", alpha=0.25)
    fig.suptitle("D044 NIFRK paired uncertainty, interaction isolation, and compute boundary", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Development-only evidence; outer validation labels were used only for scoring. Calibration/final-test, hardware/GPU, mission, and Gate 6 counters were zero.", fontsize=9)
    fig.subplots_adjust(wspace=0.48, bottom=0.18)
    return _save(fig, "post_gate5_d044_nifrk_audit_resources")


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
    source_data = ";".join(["data/processed/reporting/post_gate5_d044_nifrk/campaign_result.json", "data/processed/reporting/post_gate5_d044_nifrk/summary.csv", "data/processed/reporting/post_gate5_d044_nifrk/per_seed_metrics.csv", "data/processed/reporting/post_gate5_d044_nifrk/paired_comparison.csv", "data/processed/reporting/post_gate5_d044_nifrk/inner_fold_audit.csv", "data/processed/reporting/post_gate5_d044_nifrk/interaction_audit.csv", "data/processed/reporting/post_gate5_d044_nifrk/channel_audit.csv"])
    generator = "scripts/make_post_gate5_d044_nifrk_figures.py"
    generator_hash = _sha256(ROOT / generator)
    definitions = [
        ("RFIG-074", "D044 NIFRK result comparison", "Results: development-only nonlinear stack", "d044_nifrk_result_comparison", "development_only_negative", "NIFRK q=4/6/8 and matched nonlinear two-RBF stacks are compared with C06 under the frozen threshold and classical-control rules.", "Development-only evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage."),
        ("RFIG-075", "D044 NIFRK paired audit and resources", "Methods and Results: nonlinear interaction and compute", "d044_nifrk_audit_resources", "development_only_negative", "The NIFRK q=8 paired endpoint, training-only interaction norms, and reference-laptop resource boundary are reported with group separation audits.", "Development-only uncertainty, interaction, integrity, and compute evidence; no NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 5 revision, Gate 6, or quantum advantage."),
    ]
    entries: list[dict[str, str]] = []
    for definition, (png, svg) in zip(definitions, paths):
        figure_id, title, phase, section, evidence_status, caption, claim_boundary = definition
        entries.append({"figure_id": figure_id, "title": title, "phase": phase, "paper_section": section, "evidence_status": evidence_status, "source_data": source_data, "generator": generator, "png_path": str(png.relative_to(ROOT)).replace("\\", "/"), "png_sha256": _sha256(png), "png_bytes": str(png.stat().st_size), "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"), "svg_sha256": _sha256(svg), "svg_bytes": str(svg.stat().st_size), "caption": caption, "claim_boundary": claim_boundary, "campaign_source_commit": result["source_commit"], "reporting_source_commit": result["source_commit"], "accepted_d007_candidate_commit": "", "reporting_module_sha256": "", "reporting_script_sha256": "", "figure_generator_sha256": generator_hash})
    _update_registry(entries)
    print(json.dumps({"status": "complete", "figures": [entry["figure_id"] for entry in entries]}, indent=2))


if __name__ == "__main__":
    main()
