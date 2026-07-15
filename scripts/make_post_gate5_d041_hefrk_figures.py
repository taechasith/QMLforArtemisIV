"""Generate paper-ready figures for the D041 HEFRK negative result."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import NullFormatter


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "data/processed/reporting/post_gate5_d041_hefrk"
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
        "TWO-RBF-08-E025",
        "TWO-RBF-08-E050",
        "TWO-RBF-08-E075",
        "HEFRK-08-E025",
        "HEFRK-08-E050",
        "HEFRK-08-E075",
    ]
    labels = ["C06", "2RBF E25", "2RBF E50", "2RBF E75", "HEFRK E25", "HEFRK E50", "HEFRK E75"]
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
            axis.set_xscale("log")
            axis.set_xticks([])
            axis.xaxis.set_major_formatter(NullFormatter())
            axis.xaxis.set_minor_formatter(NullFormatter())
            axis.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
            axis.text(
                0.02,
                0.04,
                "C06=.006833; HEFRK E50=.006592; HEFRK E75=.006525",
                transform=axis.transAxes,
                fontsize=8,
            )
        if field == "mean_mae":
            for index, value in enumerate(values):
                axis.text(value * 1.01, index, f"{value:.5g}", va="center", fontsize=7)
    fig.suptitle(
        "D041 HEFRK development-only result: hybrid fidelity-RBF fusion remained below the 5% rule",
        fontsize=14,
        fontweight="bold",
    )
    fig.text(
        0.01,
        0.01,
        "q=8 eta sweep; five grouped outer folds; four inner whole-group folds; 20 seeds; 39,000 development rows. Eta was fixed before fitting.",
        fontsize=9,
    )
    fig.subplots_adjust(bottom=0.18)
    return _save(fig, "post_gate5_d041_hefrk_result_comparison")


def _figure_audit_resources(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    paired = _read_csv(RESULT_ROOT / "paired_comparison.csv")[0]
    channel_audit = _read_csv(RESULT_ROOT / "channel_audit.csv")
    projection_audit = _read_csv(RESULT_ROOT / "projection_audit.csv")
    inner_audit = _read_csv(RESULT_ROOT / "inner_fold_audit.csv")
    assert len(channel_audit) == 900
    assert len(projection_audit) == 900
    assert len(inner_audit) == 400
    assert all(int(row["validation_outcomes_used"]) == 0 for row in channel_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in projection_audit)
    assert all(int(row["group_intersection_count"]) == 0 for row in inner_audit)
    assert all(row["channel_source"] == "same_cross_fitted_c06_residual" for row in channel_audit)

    per_seed = _read_csv(RESULT_ROOT / "per_seed_metrics.csv")
    c06_by_seed = {row["seed_index"]: float(row["nrmse"]) for row in per_seed if row["model_id"] == "C06"}
    differences = np.asarray(
        [
            float(row["nrmse"]) - c06_by_seed[row["seed_index"]]
            for row in per_seed
            if row["model_id"] == "HEFRK-08-E050"
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
    axes[0].set_xticks([1], ["HEFRK-8 E50 minus C06"])
    axes[0].set_ylabel("Seed-pooled NRMSE difference")
    axes[0].set_title("Primary paired endpoint")
    axes[0].legend(fontsize=8)

    q8 = [row for row in channel_audit if int(row["q"]) == 8]
    eta_values = [0.25, 0.50, 0.75]
    fidelity_norms = [np.mean([float(row["fidelity_delta_l2"]) for row in q8 if float(row["eta"]) == eta]) for eta in eta_values]
    rbf25_norms = [np.mean([float(row["rbf25_delta_l2"]) for row in q8 if float(row["eta"]) == eta]) for eta in eta_values]
    rbf50_norms = [np.mean([float(row["rbf50_delta_l2"]) for row in q8 if float(row["eta"]) == eta]) for eta in eta_values]
    x = np.arange(3)
    axes[1].plot(x, fidelity_norms, marker="o", color="#2a9d8f", label="fidelity")
    axes[1].plot(x, rbf25_norms, marker="o", color="#e07a5f", label="RBF gamma .25")
    axes[1].plot(x, rbf50_norms, marker="o", color="#1b4965", label="RBF gamma .50")
    axes[1].set_xticks(x, ["0.25", "0.50", "0.75"])
    axes[1].set_xlabel("Eta")
    axes[1].set_ylabel("Mean correction L2 norm")
    axes[1].set_title("q=8 channel audit")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.25)

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
    axes[2].tick_params(axis="y", labelsize=8)
    axes[2].grid(axis="x", alpha=0.25)
    fig.suptitle("D041 HEFRK uncertainty, channel complementarity, and compute boundary", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Development-only evidence; calibration/final-test reads, hardware/GPU jobs, mission loops, and Gate 6 runs were zero.", fontsize=9)
    fig.subplots_adjust(wspace=0.48, bottom=0.18)
    return _save(fig, "post_gate5_d041_hefrk_audit_resources")


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
            "data/processed/reporting/post_gate5_d041_hefrk/campaign_result.json",
            "data/processed/reporting/post_gate5_d041_hefrk/summary.csv",
            "data/processed/reporting/post_gate5_d041_hefrk/per_seed_metrics.csv",
            "data/processed/reporting/post_gate5_d041_hefrk/paired_comparison.csv",
            "data/processed/reporting/post_gate5_d041_hefrk/inner_fold_audit.csv",
            "data/processed/reporting/post_gate5_d041_hefrk/projection_audit.csv",
            "data/processed/reporting/post_gate5_d041_hefrk/channel_audit.csv",
        ]
    )
    generator = "scripts/make_post_gate5_d041_hefrk_figures.py"
    generator_hash = _sha256(ROOT / generator)
    definitions = [
        (
            "RFIG-068",
            "D041 HEFRK result comparison",
            "Results: development-only negative",
            "d041_hefrk_result_comparison",
            "development_only_negative",
            "The q=8 HEFRK eta sweep improved C06 at eta 0.75 but stayed below the 5% threshold and did not establish a gain over the two-RBF control.",
            "Development-only evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage.",
        ),
        (
            "RFIG-069",
            "D041 HEFRK paired audit and resources",
            "Methods and Results: channel audit and compute",
            "d041_hefrk_audit_resources",
            "development_only_negative",
            "The HEFRK-08-E050 paired interval is below zero, while channel, mixture, projection, inner-fold, and resource audits are complete.",
            "Development-only uncertainty, channel, integrity, and compute evidence; no NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 5 revision, Gate 6, or quantum advantage.",
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
