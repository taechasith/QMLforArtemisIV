"""Generate paper-ready figures for the D047 OMFRK campaign."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "data/processed/reporting/post_gate5_d047_omfrk"
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
    models = ["C06", "OM-TWO-RBF", "OMFRK-ALL"]
    labels = ["C06", "OM 2RBF", "OMFRK"]
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
            axis.text(0.02, 0.08, f"C06={float(summary['C06']['mean_nrmse']):.6f}; OMFRK={float(summary['OMFRK-ALL']['mean_nrmse']):.6f}", transform=axis.transAxes, fontsize=8)
        if field == "mean_mae":
            for index, value in enumerate(values):
                axis.text(value * 1.01, index, f"{value:.5g}", va="center", fontsize=8)
    fig.suptitle("D047 OMFRK development result: common-target multi-scale stack", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Five grouped outer folds; four inner whole-group folds; 20 seeds; 39,000 development rows. Candidate and control share the q=8 RBF-0.25 first stage.", fontsize=9)
    fig.subplots_adjust(bottom=0.18)
    return _save(fig, "post_gate5_d047_omfrk_result_comparison")


def _figure_audit_resources(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    paired = _read_csv(RESULT_ROOT / "paired_comparison.csv")[0]
    channel_audit = _read_csv(RESULT_ROOT / "channel_audit.csv")
    orthogonal_audit = _read_csv(RESULT_ROOT / "orthogonal_audit.csv")
    shared_audit = _read_csv(RESULT_ROOT / "shared_stage_audit.csv")
    stack_audit = _read_csv(RESULT_ROOT / "stack_audit.csv")
    inner_audit = _read_csv(RESULT_ROOT / "inner_fold_audit.csv")
    assert len(channel_audit) == 300
    assert len(orthogonal_audit) == 1200
    assert len(shared_audit) == 400
    assert len(stack_audit) == 100
    assert len(inner_audit) == 400
    assert all(int(row["validation_outcomes_used"]) == 0 for row in channel_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in orthogonal_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in shared_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in stack_audit)
    assert all(int(row["group_intersection_count"]) == 0 for row in orthogonal_audit)
    assert all(row["stage_order"] == "shared_q8_rbf25_then_common_e2_q_stack" for row in channel_audit)
    assert all(int(row["candidate_feature_columns"]) == 4 and int(row["control_feature_columns"]) == 4 for row in stack_audit)

    per_seed = _read_csv(RESULT_ROOT / "per_seed_metrics.csv")
    c06_by_seed = {row["seed_index"]: float(row["nrmse"]) for row in per_seed if row["model_id"] == "C06"}
    differences = np.asarray([float(row["nrmse"]) - c06_by_seed[row["seed_index"]] for row in per_seed if row["model_id"] == "OMFRK-ALL"])
    target_norms = np.asarray([float(row["common_target_l2"]) for row in channel_audit])
    coefficients = [float(value) for row in stack_audit for value in row["candidate_coefficients"].split(";")[1:]]
    runtime = result["runtime"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    axes[0].axhline(0.0, color="#202020", linewidth=1)
    axes[0].boxplot(differences, widths=0.35, patch_artist=True, boxprops={"facecolor": "#2a9d8f"})
    axes[0].scatter(np.ones(differences.size), differences, color="#1b4965", s=18, alpha=0.8, zorder=3)
    axes[0].axhline(float(paired["lower_95"]), color="#bc4749", linestyle=":", label="95% paired interval")
    axes[0].axhline(float(paired["upper_95"]), color="#bc4749", linestyle=":")
    axes[0].set_xlim(0.5, 1.5)
    axes[0].set_xticks([1], ["OMFRK minus C06"])
    axes[0].set_ylabel("Seed-pooled NRMSE difference")
    axes[0].set_title("Primary paired endpoint")
    axes[0].legend(fontsize=8)

    axes[1].hist(target_norms, bins=12, color="#2a9d8f", edgecolor="#202020", alpha=0.9, label="common e2 norm")
    ax2 = axes[1].twinx()
    ax2.hist(coefficients, bins=12, color="#e07a5f", edgecolor="#202020", alpha=0.35, label="candidate coefficients")
    axes[1].set_xlabel("Audit value")
    axes[1].set_ylabel("Common-target count")
    ax2.set_ylabel("Coefficient count")
    axes[1].set_title("Training-only target and stack audit")
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
    fig.suptitle("D047 OMFRK paired uncertainty, common-target audit, and compute boundary", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Development-only evidence; outer validation labels were used only for scoring. Calibration/final-test, hardware/GPU, mission, and Gate 6 counters were zero.", fontsize=9)
    fig.subplots_adjust(wspace=0.52, bottom=0.18)
    return _save(fig, "post_gate5_d047_omfrk_audit_resources")


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
    source_data = ";".join(["data/processed/reporting/post_gate5_d047_omfrk/campaign_result.json", "data/processed/reporting/post_gate5_d047_omfrk/summary.csv", "data/processed/reporting/post_gate5_d047_omfrk/per_seed_metrics.csv", "data/processed/reporting/post_gate5_d047_omfrk/paired_comparison.csv", "data/processed/reporting/post_gate5_d047_omfrk/inner_fold_audit.csv", "data/processed/reporting/post_gate5_d047_omfrk/shared_stage_audit.csv", "data/processed/reporting/post_gate5_d047_omfrk/orthogonal_audit.csv", "data/processed/reporting/post_gate5_d047_omfrk/channel_audit.csv", "data/processed/reporting/post_gate5_d047_omfrk/stack_audit.csv"])
    generator = "scripts/make_post_gate5_d047_omfrk_figures.py"
    generator_hash = _sha256(ROOT / generator)
    definitions = [
        ("RFIG-080", "D047 OMFRK result comparison", "Results: development-only common-target multi-scale stack", "d047_omfrk_result_comparison", "development_only_negative", "OMFRK-ALL and its matched q=4/6/8 two-RBF stack are compared with C06 after a shared q=8 RBF-0.25 correction.", "Development-only evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage."),
        ("RFIG-081", "D047 OMFRK paired audit and resources", "Methods and Results: common residual and compute", "d047_omfrk_audit_resources", "development_only_negative", "The OMFRK paired endpoint, common orthogonalized target, fixed stack audit, and reference-laptop resource boundary are reported.", "Development-only uncertainty, stack, integrity, and compute evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage."),
    ]
    entries: list[dict[str, str]] = []
    for definition, (png, svg) in zip(definitions, paths):
        figure_id, title, phase, section, evidence_status, caption, claim_boundary = definition
        entries.append({"figure_id": figure_id, "title": title, "phase": phase, "paper_section": section, "evidence_status": evidence_status, "source_data": source_data, "generator": generator, "png_path": str(png.relative_to(ROOT)).replace("\\", "/"), "png_sha256": _sha256(png), "png_bytes": str(png.stat().st_size), "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"), "svg_sha256": _sha256(svg), "svg_bytes": str(svg.stat().st_size), "caption": caption, "claim_boundary": claim_boundary, "campaign_source_commit": result["source_commit"], "reporting_source_commit": result["source_commit"], "accepted_d007_candidate_commit": "", "reporting_module_sha256": "", "reporting_script_sha256": "", "figure_generator_sha256": generator_hash})
    _update_registry(entries)
    print(json.dumps({"status": "complete", "figures": [entry["figure_id"] for entry in entries]}, indent=2))


if __name__ == "__main__":
    main()
