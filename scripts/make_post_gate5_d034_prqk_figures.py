"""Generate paper-ready figures for the D034 PRQK negative result."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "data/processed/reporting/post_gate5_d034_prqk"
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


def _float(row: dict[str, str], field: str) -> float:
    return float(row[field])


def _figure_result_comparison(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    models = [
        "C06",
        "BASELINE",
        "A02-R-q4",
        "A02-R-q6",
        "A02-R-q8",
        "PRQK-04-N",
        "PRQK-04-E",
        "PRQK-06-N",
        "PRQK-06-E",
        "PRQK-08-N",
        "PRQK-08-E",
    ]
    labels = [value.replace("PRQK-", "P-").replace("A02-R-", "A02-") for value in models]
    colors = [
        "#1b4965" if value == "C06" else "#6c757d" if value == "BASELINE" else "#e07a5f" if value.startswith("A02") else "#2a9d8f"
        for value in models
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=True)
    y = np.arange(len(models))
    for axis, field, title, xlabel in (
        (axes[0], "mean_nrmse", "Cost error", "Pooled OOF NRMSE (lower is better)"),
        (axes[1], "mean_mean_regret_m_s", "Selection regret", "Mean regret (m/s; lower is better)"),
        (axes[2], "mean_brier", "Safety probability", "Brier score (lower is better)"),
    ):
        values = [
            _float(summary[model], field) if field in summary[model] else np.nan
            for model in models
        ]
        axis.barh(y, values, color=colors, edgecolor="#202020", linewidth=0.3)
        axis.set_title(title)
        axis.set_xlabel(xlabel)
        axis.grid(axis="x", alpha=0.25)
        axis.invert_yaxis()
        if field == "mean_nrmse":
            axis.set_xscale("log")
        for index, value in enumerate(values):
            if np.isfinite(value):
                axis.text(value * (1.08 if field == "mean_nrmse" else 1.01), index, f"{value:.4g}", va="center", fontsize=7)
            else:
                axis.text(0.02, index, "not scored", va="center", fontsize=7, color="#555555")
    axes[0].set_yticks(y, labels)
    fig.suptitle("D034 PRQK development-only result: residual anchoring did not beat C06", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Five grouped folds; 20 seeds; 39,000 development rows. C02 has no cost bar because it is the safety comparator.", fontsize=9)
    return _save(fig, "post_gate5_d034_prqk_result_comparison")


def _figure_ablation(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    configs = [
        "PRQK-04-N",
        "PRQK-04-E",
        "PRQK-06-N",
        "PRQK-06-E",
        "PRQK-08-N",
        "PRQK-08-E",
    ]
    labels = ["q4\nno ent", "q4\nent", "q6\nno ent", "q6\nent", "q8\nno ent", "q8\nent"]
    nrmse = np.asarray([_float(summary[value], "mean_nrmse") for value in configs])
    auroc = np.asarray([_float(summary[value], "mean_auroc") for value in configs])
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    x = np.arange(len(configs))
    axes[0].plot(x, nrmse, marker="o", color="#2a9d8f", linewidth=2)
    axes[0].axhline(_float(summary["C06"], "mean_nrmse"), color="#1b4965", linestyle="--", label="C06")
    axes[0].axhline(0.95 * _float(summary["C06"], "mean_nrmse"), color="#bc4749", linestyle=":", label="5% improvement target")
    axes[0].set_ylabel("Pooled OOF NRMSE")
    axes[0].set_title("Residual-cost ablation")
    axes[0].set_yscale("log")
    axes[0].legend(fontsize=8)
    axes[1].plot(x, auroc, marker="o", color="#e07a5f", linewidth=2)
    axes[1].axhline(_float(summary["C02"], "mean_auroc"), color="#1b4965", linestyle="--", label="C02")
    axes[1].set_ylabel("Pooled OOF AUROC")
    axes[1].set_title("Separate safety-head ablation")
    axes[1].legend(fontsize=8)
    for axis in axes:
        axis.set_xticks(x, labels)
        axis.grid(axis="y", alpha=0.25)
        axis.set_xlabel("Fixed PRQK configuration")
    fig.suptitle("D034 fixed ablations: entanglement and qubit count did not recover the baseline gap", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "No configuration was reranked after observing the endpoint; q and entanglement are prespecified ablations.", fontsize=9)
    return _save(fig, "post_gate5_d034_prqk_ablations")


def _figure_paired_resources(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    paired = _read_csv(RESULT_ROOT / "paired_comparison.csv")[0]
    per_seed = _read_csv(RESULT_ROOT / "per_seed_metrics.csv")
    differences = np.asarray(
        [
            float(row["nrmse"])
            - next(float(item["nrmse"]) for item in per_seed if item["model_id"] == "C06" and item["seed_index"] == row["seed_index"])
            for row in per_seed
            if row["model_id"] == "PRQK-08-N"
        ]
    )
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    runtime = result["runtime"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].axhline(0.0, color="#1b1b1b", linewidth=1)
    axes[0].boxplot(differences, vert=True, widths=0.35, patch_artist=True, boxprops={"facecolor": "#e07a5f"})
    axes[0].scatter(np.ones(differences.size), differences, color="#1b4965", s=18, alpha=0.8, zorder=3)
    axes[0].axhline(float(paired["lower_95"]), color="#bc4749", linestyle=":", label="95% interval")
    axes[0].axhline(float(paired["upper_95"]), color="#bc4749", linestyle=":")
    axes[0].set_xlim(0.5, 1.5)
    axes[0].set_xticks([1], ["PRQK-08-N - C06"])
    axes[0].set_ylabel("Seed-pooled NRMSE difference")
    axes[0].set_title("Paired seed evidence")
    axes[0].legend(fontsize=8)
    resource_labels = ["CPU hours", "Wall days", "Peak GiB", "Free disk GiB"]
    resource_values = [
        float(runtime["cpu_seconds"]) / 3600.0,
        float(runtime["wall_clock_seconds"]) / 86400.0,
        float(runtime["peak_working_set_gib"]),
        float(runtime["free_disk_gib"]),
    ]
    resource_limits = [250.0, 5.0, 24.0, 20.0]
    positions = np.arange(len(resource_labels))
    axes[1].barh(positions, resource_values, color="#2a9d8f", label="Observed")
    axes[1].plot(resource_limits, positions, "|", color="#bc4749", markersize=14, label="Protocol limit")
    axes[1].set_yticks(positions, resource_labels)
    axes[1].set_title("Reference-laptop resource record")
    axes[1].set_xlabel("Observed value; red marker is limit")
    axes[1].grid(axis="x", alpha=0.25)
    axes[1].legend(fontsize=8)
    fig.suptitle("D034 uncertainty and compute boundary", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "The paired interval is entirely positive; the valid negative is development-only and classically simulable. Two prelaunch launcher stops were corrected before this endpoint.", fontsize=9)
    return _save(fig, "post_gate5_d034_prqk_paired_resources")


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
    paths = [
        _figure_result_comparison(summary),
        _figure_ablation(summary),
        _figure_paired_resources(summary),
    ]
    source_data = ";".join(
        [
            "data/processed/reporting/post_gate5_d034_prqk/campaign_result.json",
            "data/processed/reporting/post_gate5_d034_prqk/summary.csv",
            "data/processed/reporting/post_gate5_d034_prqk/per_seed_metrics.csv",
            "data/processed/reporting/post_gate5_d034_prqk/paired_comparison.csv",
            "data/processed/reporting/post_gate5_d034_prqk/technical_stop_prelaunch.json",
            "data/processed/reporting/post_gate5_d034_prqk/technical_stop_registry_loader.json",
        ]
    )
    generator = "scripts/make_post_gate5_d034_prqk_figures.py"
    generator_hash = _sha256(ROOT / generator)
    definitions = [
        ("RFIG-053", "D034 PRQK result comparison", "Results: development-only negative", "d034_result_comparison", "development_only_negative", "D034 valid negative: PRQK did not beat the frozen physics residual or its matched classical kernel control.", "Development-only model evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage."),
        ("RFIG-054", "D034 PRQK fixed ablations", "Results: ablations", "d034_fixed_ablations", "development_only_negative", "D034 q=4/6/8 and entanglement ablations did not close the cost or safety gap.", "Development-only ablation evidence; no post-outcome reranking, Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage."),
        ("RFIG-055", "D034 PRQK paired uncertainty and resources", "Methods and Results: uncertainty and compute", "d034_paired_uncertainty_resources", "development_only_negative", "The paired PRQK-08-N minus C06 NRMSE interval is entirely positive while the reference-laptop resource record remains below protocol ceilings.", "Development-only uncertainty and compute evidence; no NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 5 revision, Gate 6, or quantum advantage."),
    ]
    entries: list[dict[str, str]] = []
    for (figure_id, title, phase, section, evidence_status, caption, claim_boundary), (png, svg) in zip(definitions, paths):
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
