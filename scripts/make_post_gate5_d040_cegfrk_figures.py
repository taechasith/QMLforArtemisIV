"""Generate paper-ready figures for the D040 CE-GFRK negative result."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "data/processed/reporting/post_gate5_d040_cegfrk"
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
        "EC-TAP-RBF-C-SHR-q4-L010",
        "EC-TAP-RBF-C-SHR-q6-L010",
        "EC-TAP-RBF-C-SHR-q8-L010",
        "CE-GFRK-04-L010",
        "CE-GFRK-06-L010",
        "CE-GFRK-08-L010",
    ]
    labels = ["C06", "RBF-C-4", "RBF-C-6", "RBF-C-8", "CE-G-4", "CE-G-6", "CE-G-8"]
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
            axis.set_xticks([0.0064, 0.0066, 0.0068])
            axis.set_xticklabels(["0.0064", "0.0066", "0.0068"], fontsize=8)
        if field == "mean_mae":
            for index, value in enumerate(values):
                axis.text(value * 1.01, index, f"{value:.5g}", va="center", fontsize=7)
    fig.suptitle(
        "D040 CE-GFRK development-only result: centering remained below the C06 threshold",
        fontsize=14,
        fontweight="bold",
    )
    fig.text(
        0.01,
        0.01,
        "Five grouped outer folds; four inner whole-group folds; 20 seeds; 39,000 development rows. Centering means were fit on outer-training rows only.",
        fontsize=9,
    )
    fig.subplots_adjust(bottom=0.18)
    return _save(fig, "post_gate5_d040_cegfrk_result_comparison")


def _figure_audit_resources(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    paired = _read_csv(RESULT_ROOT / "paired_comparison.csv")[0]
    fidelity_audit = _read_csv(RESULT_ROOT / "fidelity_audit.csv")
    projection_audit = _read_csv(RESULT_ROOT / "projection_audit.csv")
    centering_audit = _read_csv(RESULT_ROOT / "centering_audit.csv")
    inner_audit = _read_csv(RESULT_ROOT / "inner_fold_audit.csv")
    assert len(fidelity_audit) == 300
    assert len(projection_audit) == 300
    assert len(centering_audit) == 300
    assert len(inner_audit) == 400
    assert all(row["centering_source"] == "outer_training_rows_only" for row in centering_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in fidelity_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in projection_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in centering_audit)
    assert all(int(row["group_intersection_count"]) == 0 for row in inner_audit)

    per_seed = _read_csv(RESULT_ROOT / "per_seed_metrics.csv")
    c06_by_seed = {row["seed_index"]: float(row["nrmse"]) for row in per_seed if row["model_id"] == "C06"}
    differences = np.asarray(
        [
            float(row["nrmse"]) - c06_by_seed[row["seed_index"]]
            for row in per_seed
            if row["model_id"] == "CE-GFRK-08-L010"
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
    axes[0].set_xticks([1], ["CE-GFRK-8 minus C06"])
    axes[0].set_ylabel("Seed-pooled NRMSE difference")
    axes[0].set_title("Primary paired endpoint")
    axes[0].legend(fontsize=8)

    q_values = [4, 6, 8]
    quantum_center = [
        np.mean([float(row["quantum_train_center_mean_abs"]) for row in centering_audit if int(row["q"]) == q])
        for q in q_values
    ]
    classical_center = [
        np.mean([float(row["classical_train_center_mean_abs"]) for row in centering_audit if int(row["q"]) == q])
        for q in q_values
    ]
    axes[1].bar(np.arange(3) - 0.18, quantum_center, width=0.36, color="#2a9d8f", label="fidelity")
    axes[1].bar(np.arange(3) + 0.18, classical_center, width=0.36, color="#e07a5f", label="RBF")
    axes[1].set_xticks(np.arange(3), [str(q) for q in q_values])
    axes[1].set_yscale("log")
    axes[1].set_title("Training-only centering audit")
    axes[1].set_xlabel("Qubits")
    axes[1].set_ylabel("Max absolute centered column mean")
    axes[1].legend(fontsize=8)
    axes[1].text(0.02, 0.95, "validation outcomes used: 0\ngroup overlaps: 0", transform=axes[1].transAxes, va="top", fontsize=9)
    axes[1].grid(axis="y", alpha=0.25)

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
    fig.suptitle("D040 CE-GFRK uncertainty, centering audit, and compute boundary", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Development-only evidence; calibration/final-test reads, hardware/GPU jobs, mission loops, and Gate 6 runs were zero.", fontsize=9)
    fig.subplots_adjust(wspace=0.48, bottom=0.18)
    return _save(fig, "post_gate5_d040_cegfrk_audit_resources")


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
            "data/processed/reporting/post_gate5_d040_cegfrk/campaign_result.json",
            "data/processed/reporting/post_gate5_d040_cegfrk/summary.csv",
            "data/processed/reporting/post_gate5_d040_cegfrk/per_seed_metrics.csv",
            "data/processed/reporting/post_gate5_d040_cegfrk/paired_comparison.csv",
            "data/processed/reporting/post_gate5_d040_cegfrk/inner_fold_audit.csv",
            "data/processed/reporting/post_gate5_d040_cegfrk/projection_audit.csv",
            "data/processed/reporting/post_gate5_d040_cegfrk/fidelity_audit.csv",
            "data/processed/reporting/post_gate5_d040_cegfrk/centering_audit.csv",
        ]
    )
    generator = "scripts/make_post_gate5_d040_cegfrk_figures.py"
    generator_hash = _sha256(ROOT / generator)
    definitions = [
        (
            "RFIG-066",
            "D040 CE-GFRK result comparison",
            "Results: development-only negative",
            "d040_cegfrk_result_comparison",
            "development_only_negative",
            "Training-only centered fidelity improved C06 by less than the 5% threshold and did not establish a classical-control advantage.",
            "Development-only evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage.",
        ),
        (
            "RFIG-067",
            "D040 CE-GFRK paired audit and resources",
            "Methods and Results: centering audit and compute",
            "d040_cegfrk_audit_resources",
            "development_only_negative",
            "The CE-GFRK-08-L010 paired interval is below zero, while training-only centering, PSD, projection, inner-fold, and resource audits are complete.",
            "Development-only uncertainty, centering, integrity, and compute evidence; no NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 5 revision, Gate 6, or quantum advantage.",
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
