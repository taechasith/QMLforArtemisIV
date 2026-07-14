"""Generate paper-ready figures for the D039 EC-GFRK negative result."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "data/processed/reporting/post_gate5_d039_ecgfrk"
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
        "EC-TAP-RBF-SHR-q4-L010",
        "EC-TAP-RBF-SHR-q6-L010",
        "EC-TAP-RBF-SHR-q8-L010",
        "EC-GFRK-04-L010",
        "EC-GFRK-06-L010",
        "EC-GFRK-08-L010",
    ]
    labels = [
        "C06",
        "RBF-4",
        "RBF-6",
        "RBF-8",
        "EC-G-4",
        "EC-G-6",
        "EC-G-8",
    ]
    colors = [
        "#1b4965" if model == "C06" else "#e07a5f" if "RBF" in model else "#2a9d8f"
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
            axis.set_xscale("log")
            axis.set_xticks([0.0065, 0.0067, 0.0069])
            axis.set_xticklabels(["0.0065", "0.0067", "0.0069"], fontsize=8)
        if field == "mean_mae":
            for index, value in enumerate(values):
                axis.text(value * 1.01, index, f"{value:.5g}", va="center", fontsize=7)
    fig.suptitle(
        "D039 EC-GFRK development-only result: baseline conditioning passed C06 but not the classical-control rule",
        fontsize=14,
        fontweight="bold",
    )
    fig.text(
        0.01,
        0.01,
        "Five grouped outer folds; four inner whole-group folds; 20 seeds; 39,000 development rows. The C06 feature was cross-fitted for training and outer-fold training-only for validation.",
        fontsize=9,
    )
    fig.subplots_adjust(bottom=0.18)
    return _save(fig, "post_gate5_d039_ecgfrk_result_comparison")


def _figure_audit_resources(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    paired = _read_csv(RESULT_ROOT / "paired_comparison.csv")[0]
    fidelity_audit = _read_csv(RESULT_ROOT / "fidelity_audit.csv")
    projection_audit = _read_csv(RESULT_ROOT / "projection_audit.csv")
    inner_audit = _read_csv(RESULT_ROOT / "inner_fold_audit.csv")
    assert len(fidelity_audit) == 300
    assert len(projection_audit) == 300
    assert len(inner_audit) == 400
    assert all(row["conditioning_feature"] == "cross_fitted_c06_train_outer_c06_validation" for row in projection_audit)
    assert all(row["conditioning_feature"] == "cross_fitted_c06_train_outer_c06_validation" for row in fidelity_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in fidelity_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in projection_audit)
    assert all(int(row["group_intersection_count"]) == 0 for row in inner_audit)

    per_seed = _read_csv(RESULT_ROOT / "per_seed_metrics.csv")
    c06_by_seed = {row["seed_index"]: float(row["nrmse"]) for row in per_seed if row["model_id"] == "C06"}
    differences = np.asarray(
        [
            float(row["nrmse"]) - c06_by_seed[row["seed_index"]]
            for row in per_seed
            if row["model_id"] == "EC-GFRK-08-L010"
        ]
    )
    runtime = result["runtime"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    axes[0].axhline(0.0, color="#202020", linewidth=1)
    axes[0].boxplot(differences, widths=0.35, patch_artist=True, boxprops={"facecolor": "#2a9d8f"})
    axes[0].scatter(np.ones(differences.size), differences, color="#1b4965", s=18, alpha=0.8, zorder=3)
    axes[0].axhline(float(paired["lower_95"]), color="#bc4749", linestyle=":", label="95% paired interval")
    axes[0].axhline(float(paired["upper_95"]), color="#bc4749", linestyle=":")
    axes[0].set_xlim(0.5, 1.5)
    axes[0].set_xticks([1], ["EC-GFRK-8 minus C06"])
    axes[0].set_ylabel("Seed-pooled NRMSE difference")
    axes[0].set_title("Primary paired endpoint")
    axes[0].legend(fontsize=8)

    q_values = [4, 6, 8]
    clipped = [
        np.mean([float(row["psd_clipped_eigenvalues"]) for row in fidelity_audit if int(row["q"]) == q])
        for q in q_values
    ]
    widths = [int(next(row["fit_features"] for row in projection_audit if int(row["projection_components"]) == q)) for q in q_values]
    axis = axes[1]
    axis.bar([str(q) for q in q_values], clipped, color="#e07a5f", label="PSD eigenvalues clipped")
    axis.set_title("Fidelity and conditioning audit")
    axis.set_xlabel("Qubits")
    axis.set_ylabel("Mean eigenvalues clipped")
    axis.grid(axis="y", alpha=0.25)
    axis2 = axis.twinx()
    axis2.plot([str(q) for q in q_values], widths, color="#1b4965", marker="o", label="PLS input width")
    axis.text(0.02, 0.95, "validation outcomes used: 0\ngroup overlaps: 0", transform=axis.transAxes, va="top", fontsize=9)
    axis.text(0.68, 0.95, "line: PLS input columns", transform=axis.transAxes, va="top", fontsize=8, color="#1b4965")

    labels = ["CPU h", "Wall h", "Peak GiB", "Free GiB"]
    values = [
        float(runtime["cpu_seconds"]) / 3600.0,
        float(runtime["wall_clock_seconds"]) / 3600.0,
        float(runtime["peak_working_set_gib"]),
        float(runtime["free_disk_gib"]),
    ]
    axes[2].barh(np.arange(len(labels)), values, color="#1b4965")
    axes[2].set_yticks(np.arange(len(labels)), labels)
    axes[2].set_xscale("log")
    axes[2].set_title("Reference-laptop resources")
    axes[2].set_xlabel("Observed value")
    axes[2].grid(axis="x", alpha=0.25)
    axes[2].tick_params(axis="y", labelsize=8)
    fig.subplots_adjust(wspace=0.55, bottom=0.2)
    fig.suptitle("D039 EC-GFRK uncertainty, data-access audit, and compute boundary", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Development-only evidence; calibration/final-test reads, hardware/GPU jobs, mission loops, and Gate 6 runs were zero.", fontsize=9)
    return _save(fig, "post_gate5_d039_ecgfrk_audit_resources")


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
            "data/processed/reporting/post_gate5_d039_ecgfrk/campaign_result.json",
            "data/processed/reporting/post_gate5_d039_ecgfrk/summary.csv",
            "data/processed/reporting/post_gate5_d039_ecgfrk/per_seed_metrics.csv",
            "data/processed/reporting/post_gate5_d039_ecgfrk/paired_comparison.csv",
            "data/processed/reporting/post_gate5_d039_ecgfrk/inner_fold_audit.csv",
            "data/processed/reporting/post_gate5_d039_ecgfrk/projection_audit.csv",
            "data/processed/reporting/post_gate5_d039_ecgfrk/fidelity_audit.csv",
        ]
    )
    generator = "scripts/make_post_gate5_d039_ecgfrk_figures.py"
    generator_hash = _sha256(ROOT / generator)
    definitions = [
        (
            "RFIG-064",
            "D039 EC-GFRK result comparison",
            "Results: development-only negative",
            "d039_ecgfrk_result_comparison",
            "development_only_negative",
            "Error-conditioned global fidelity improved C06 by more than 5% on the development endpoint but did not beat the matched error-conditioned TAP-RBF control by 5%.",
            "Development-only evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage.",
        ),
        (
            "RFIG-065",
            "D039 EC-GFRK paired audit and resources",
            "Methods and Results: data-access audit and compute",
            "d039_ecgfrk_audit_resources",
            "development_only_negative",
            "The EC-GFRK-08-L010 paired interval is below zero, while cross-fitted conditioning, PSD, projection, inner-fold, and resource audits are complete.",
            "Development-only uncertainty, data-access, PSD, integrity, and compute evidence; no NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 5 revision, Gate 6, or quantum advantage.",
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
