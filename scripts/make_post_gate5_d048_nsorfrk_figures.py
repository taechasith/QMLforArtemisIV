"""Generate paper-ready figures for the D048 NSORFRK campaign."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "data/processed/reporting/post_gate5_d048_nsorfrk"
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
    models = ["C06", "NSO-TWO-RBF-08", "NSORFRK-08"]
    labels = ["C06", "NSO 2RBF", "NSORFRK"]
    colors = ["#1b4965", "#e07a5f", "#2a9d8f"]
    y = np.arange(len(models))
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5))
    for axis, field, title, xlabel in (
        (axes[0], "mean_nrmse", "Cost prediction", "Pooled OOF NRMSE (lower is better)"),
        (axes[1], "mean_mean_regret_m_s", "Selection consequence", "Mean regret (m/s; lower is better)"),
        (axes[2], "mean_mae", "Absolute error", "Mean absolute error (standardized cost)"),
    ):
        values = [float(summary[model][field]) for model in models]
        axis.barh(y, values, color=colors, edgecolor="#202020", linewidth=0.3)
        axis.set_yticks(y, labels)
        axis.invert_yaxis()
        axis.set_title(title)
        axis.set_xlabel(xlabel)
        axis.grid(axis="x", alpha=0.25)
        if field == "mean_nrmse":
            axis.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))
            axis.text(0.02, 0.08, f"C06={float(summary['C06']['mean_nrmse']):.6f}; NSORFRK={float(summary['NSORFRK-08']['mean_nrmse']):.6f}", transform=axis.transAxes, fontsize=8)
        if field == "mean_mae":
            for index, value in enumerate(values):
                axis.text(value * 1.01, index, f"{value:.5g}", va="center", fontsize=8)
    fig.suptitle("D048 NSORFRK development result: nested q8 shrinkage", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Five grouped outer folds; four inner whole-group folds; 20 seeds; 39,000 development rows. Candidate and control use the same {0.05, 0.10, 0.15} grid.", fontsize=9)
    fig.subplots_adjust(bottom=0.18)
    return _save(fig, "post_gate5_d048_nsorfrk_result_comparison")


def _figure_audit_resources(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    paired = _read_csv(RESULT_ROOT / "paired_comparison.csv")[0]
    channel_audit = _read_csv(RESULT_ROOT / "channel_audit.csv")
    selection_audit = _read_csv(RESULT_ROOT / "selection_audit.csv")
    orthogonal_audit = _read_csv(RESULT_ROOT / "orthogonal_audit.csv")
    shared_audit = _read_csv(RESULT_ROOT / "shared_stage_audit.csv")
    inner_audit = _read_csv(RESULT_ROOT / "inner_fold_audit.csv")
    assert len(channel_audit) == 100
    assert len(selection_audit) == 100
    assert len(orthogonal_audit) == 400
    assert len(shared_audit) == 400
    assert len(inner_audit) == 400
    assert all(int(row["validation_outcomes_used"]) == 0 for row in channel_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in selection_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in orthogonal_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in shared_audit)
    assert all(row["stage_order"] == "shared_q8_rbf25_then_nested_shrinkage_e2" for row in channel_audit)
    candidate_lambdas = [float(row["candidate_lambda"]) for row in selection_audit]
    control_lambdas = [float(row["control_lambda"]) for row in selection_audit]
    assert set(candidate_lambdas) <= {0.05, 0.10, 0.15}
    assert set(control_lambdas) <= {0.05, 0.10, 0.15}

    per_seed = _read_csv(RESULT_ROOT / "per_seed_metrics.csv")
    c06_by_seed = {row["seed_index"]: float(row["nrmse"]) for row in per_seed if row["model_id"] == "C06"}
    differences = np.asarray([float(row["nrmse"]) - c06_by_seed[row["seed_index"]] for row in per_seed if row["model_id"] == "NSORFRK-08"])
    runtime = result["runtime"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    axes[0].axhline(0.0, color="#202020", linewidth=1)
    axes[0].boxplot(differences, widths=0.35, patch_artist=True, boxprops={"facecolor": "#2a9d8f"})
    axes[0].scatter(np.ones(differences.size), differences, color="#1b4965", s=18, alpha=0.8, zorder=3)
    axes[0].axhline(float(paired["lower_95"]), color="#bc4749", linestyle=":", label="95% paired interval")
    axes[0].axhline(float(paired["upper_95"]), color="#bc4749", linestyle=":")
    axes[0].set_xlim(0.5, 1.5)
    axes[0].set_xticks([1], ["NSORFRK minus C06"])
    axes[0].set_ylabel("Seed-pooled NRMSE difference")
    axes[0].set_title("Primary paired endpoint")
    axes[0].legend(fontsize=8)

    axes[1].bar(np.arange(3) - 0.18, [candidate_lambdas.count(value) for value in (0.05, 0.10, 0.15)], width=0.36, color="#2a9d8f", label="candidate")
    axes[1].bar(np.arange(3) + 0.18, [control_lambdas.count(value) for value in (0.05, 0.10, 0.15)], width=0.36, color="#e07a5f", label="control")
    axes[1].set_xticks(np.arange(3), ["0.05", "0.10", "0.15"])
    axes[1].set_xlabel("Selected shrinkage")
    axes[1].set_ylabel("Outer-fold/seed count")
    axes[1].set_title("Nested training-only selection")
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
    fig.suptitle("D048 NSORFRK paired uncertainty, shrinkage audit, and compute boundary", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Development-only evidence; outer validation labels were used only for scoring. Calibration/final-test, hardware/GPU, mission, and Gate 6 counters were zero.", fontsize=9)
    fig.subplots_adjust(wspace=0.48, bottom=0.18)
    return _save(fig, "post_gate5_d048_nsorfrk_audit_resources")


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
    source_data = ";".join(["data/processed/reporting/post_gate5_d048_nsorfrk/campaign_result.json", "data/processed/reporting/post_gate5_d048_nsorfrk/summary.csv", "data/processed/reporting/post_gate5_d048_nsorfrk/per_seed_metrics.csv", "data/processed/reporting/post_gate5_d048_nsorfrk/paired_comparison.csv", "data/processed/reporting/post_gate5_d048_nsorfrk/inner_fold_audit.csv", "data/processed/reporting/post_gate5_d048_nsorfrk/shared_stage_audit.csv", "data/processed/reporting/post_gate5_d048_nsorfrk/orthogonal_audit.csv", "data/processed/reporting/post_gate5_d048_nsorfrk/channel_audit.csv", "data/processed/reporting/post_gate5_d048_nsorfrk/selection_audit.csv"])
    generator = "scripts/make_post_gate5_d048_nsorfrk_figures.py"
    generator_hash = _sha256(ROOT / generator)
    definitions = [
        ("RFIG-082", "D048 NSORFRK result comparison", "Results: development-only nested q8 shrinkage", "d048_nsorfrk_result_comparison", "development_only_negative", "NSORFRK-08 and its matched q8 two-RBF control are compared with C06 under identical inner-training shrinkage selection.", "Development-only evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage."),
        ("RFIG-083", "D048 NSORFRK paired audit and resources", "Methods and Results: shrinkage selection and compute", "d048_nsorfrk_audit_resources", "development_only_negative", "The NSORFRK paired endpoint, selected-shrinkage distributions, and reference-laptop resource boundary are reported.", "Development-only uncertainty, selection, integrity, and compute evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage."),
    ]
    entries: list[dict[str, str]] = []
    for definition, (png, svg) in zip(definitions, paths):
        figure_id, title, phase, section, evidence_status, caption, claim_boundary = definition
        entries.append({"figure_id": figure_id, "title": title, "phase": phase, "paper_section": section, "evidence_status": evidence_status, "source_data": source_data, "generator": generator, "png_path": str(png.relative_to(ROOT)).replace("\\", "/"), "png_sha256": _sha256(png), "png_bytes": str(png.stat().st_size), "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"), "svg_sha256": _sha256(svg), "svg_bytes": str(svg.stat().st_size), "caption": caption, "claim_boundary": claim_boundary, "campaign_source_commit": result["source_commit"], "reporting_source_commit": result["source_commit"], "accepted_d007_candidate_commit": "", "reporting_module_sha256": "", "reporting_script_sha256": "", "figure_generator_sha256": generator_hash})
    _update_registry(entries)
    print(json.dumps({"status": "complete", "figures": [entry["figure_id"] for entry in entries]}, indent=2))


if __name__ == "__main__":
    main()
