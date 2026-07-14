"""Generate paper-ready figures for the D037 TSQR negative result."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "data/processed/reporting/post_gate5_d037_tsqr"
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


def _model_id(prefix: str, q: int, value: float) -> str:
    return f"{prefix}-{q:02d}-L{int(round(100.0 * value)):03d}"


def _figure_sensitivity(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    lambdas = [0.10, 0.25, 0.50]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    colors = {4: "#e07a5f", 6: "#2a9d8f", 8: "#1b4965"}
    for q in (4, 6, 8):
        quantum = [float(summary[_model_id("TSQR", q, value)]["mean_nrmse"]) for value in lambdas]
        classical = [float(summary[_model_id("TAP-RBF-SHR", q, value)]["mean_nrmse"]) for value in lambdas]
        axes[0].plot(lambdas, quantum, marker="o", color=colors[q], label=f"Q q={q}")
        axes[0].plot(lambdas, classical, marker="x", linestyle="--", color=colors[q], label=f"RBF q={q}")
    c06 = float(summary["C06"]["mean_nrmse"])
    axes[0].axhline(c06, color="#bc4749", linestyle=":", label="C06")
    axes[0].set_title("Correction shrinkage sensitivity")
    axes[0].set_xlabel("Fixed lambda")
    axes[0].set_ylabel("Pooled OOF NRMSE")
    axes[0].set_xticks(lambdas)
    axes[0].grid(alpha=0.25)
    axes[0].legend(fontsize=7, ncol=2)

    q = 8
    quantum_mae = [float(summary[_model_id("TSQR", q, value)]["mean_mae"]) for value in lambdas]
    classical_mae = [float(summary[_model_id("TAP-RBF-SHR", q, value)]["mean_mae"]) for value in lambdas]
    x = np.arange(len(lambdas))
    axes[1].plot(x, quantum_mae, marker="o", color="#1b4965", label="TSQR q=8")
    axes[1].plot(x, classical_mae, marker="x", linestyle="--", color="#e07a5f", label="TAP-RBF q=8")
    axes[1].axhline(float(summary["C06"]["mean_mae"]), color="#bc4749", linestyle=":", label="C06")
    axes[1].set_title("Primary q=8 absolute error")
    axes[1].set_xlabel("Fixed lambda")
    axes[1].set_ylabel("Mean absolute error")
    axes[1].set_xticks(x, [str(value) for value in lambdas])
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=8)

    quantum_regret = [float(summary[_model_id("TSQR", q, value)]["mean_mean_regret_m_s"]) for value in lambdas]
    classical_regret = [float(summary[_model_id("TAP-RBF-SHR", q, value)]["mean_mean_regret_m_s"]) for value in lambdas]
    axes[2].plot(x, quantum_regret, marker="o", color="#1b4965", label="TSQR q=8")
    axes[2].plot(x, classical_regret, marker="x", linestyle="--", color="#e07a5f", label="TAP-RBF q=8")
    axes[2].axhline(float(summary["C06"]["mean_mean_regret_m_s"]), color="#bc4749", linestyle=":", label="C06")
    axes[2].set_title("Primary q=8 selection regret")
    axes[2].set_xlabel("Fixed lambda")
    axes[2].set_ylabel("Mean regret (m/s)")
    axes[2].set_xticks(x, [str(value) for value in lambdas])
    axes[2].ticklabel_format(style="plain", axis="y", useOffset=False)
    axes[2].grid(alpha=0.25)
    axes[2].legend(fontsize=8)
    fig.suptitle("D037 TSQR development-only result: shrinkage reduced harm but did not create a QML advantage", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "All q and lambda values were fixed before fitting; q=8, lambda=0.25 was the primary endpoint. The matched RBF received identical shrinkage.", fontsize=9)
    return _save(fig, "post_gate5_d037_tsqr_shrinkage_sensitivity")


def _figure_audit_resources(summary: dict[str, dict[str, str]]) -> tuple[Path, Path]:
    result = json.loads((RESULT_ROOT / "campaign_result.json").read_text(encoding="utf-8"))
    paired = _read_csv(RESULT_ROOT / "paired_comparison.csv")[0]
    projection_audit = _read_csv(RESULT_ROOT / "projection_audit.csv")
    shrinkage_audit = _read_csv(RESULT_ROOT / "shrinkage_audit.csv")
    inner_audit = _read_csv(RESULT_ROOT / "inner_fold_audit.csv")
    assert len(projection_audit) == 300
    assert len(shrinkage_audit) == 900
    assert len(inner_audit) == 400
    assert all(int(row["validation_outcomes_used"]) == 0 for row in projection_audit)
    assert all(int(row["validation_outcomes_used"]) == 0 for row in shrinkage_audit)
    assert all(int(row["group_intersection_count"]) == 0 for row in inner_audit)

    per_seed = _read_csv(RESULT_ROOT / "per_seed_metrics.csv")
    c06_by_seed = {row["seed_index"]: float(row["nrmse"]) for row in per_seed if row["model_id"] == "C06"}
    differences = np.asarray(
        [
            float(row["nrmse"]) - c06_by_seed[row["seed_index"]]
            for row in per_seed
            if row["model_id"] == "TSQR-08-L025"
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
    axes[0].set_xticks([1], ["TSQR-08-L025 minus C06"])
    axes[0].set_ylabel("Seed-pooled NRMSE difference")
    axes[0].set_title("Primary paired endpoint")
    axes[0].legend(fontsize=8)

    axes[1].bar(["projection", "shrinkage", "inner"], [len(projection_audit), len(shrinkage_audit), len(inner_audit)], color=["#1b4965", "#e07a5f", "#2a9d8f"])
    axes[1].set_title("Integrity audit records")
    axes[1].set_ylabel("Rows recorded")
    axes[1].text(0.02, 0.95, "validation outcomes used: 0\ngroup overlaps: 0", transform=axes[1].transAxes, va="top", fontsize=9)
    axes[1].grid(axis="y", alpha=0.25)

    labels = ["CPU hours", "Wall hours", "Peak GiB", "Free disk GiB"]
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
    fig.suptitle("D037 TSQR uncertainty, audit, and compute boundary", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, "Development-only evidence; calibration/final-test reads, hardware/GPU jobs, mission loops, and Gate 6 runs were zero.", fontsize=9)
    return _save(fig, "post_gate5_d037_tsqr_audit_resources")


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
    paths = [_figure_sensitivity(summary), _figure_audit_resources(summary)]
    source_data = ";".join(
        [
            "data/processed/reporting/post_gate5_d037_tsqr/campaign_result.json",
            "data/processed/reporting/post_gate5_d037_tsqr/summary.csv",
            "data/processed/reporting/post_gate5_d037_tsqr/per_seed_metrics.csv",
            "data/processed/reporting/post_gate5_d037_tsqr/paired_comparison.csv",
            "data/processed/reporting/post_gate5_d037_tsqr/inner_fold_audit.csv",
            "data/processed/reporting/post_gate5_d037_tsqr/projection_audit.csv",
            "data/processed/reporting/post_gate5_d037_tsqr/shrinkage_audit.csv",
            "data/processed/reporting/post_gate5_d037_tsqr/technical_stop_import.json",
        ]
    )
    generator = "scripts/make_post_gate5_d037_tsqr_figures.py"
    generator_hash = _sha256(ROOT / generator)
    definitions = [
        (
            "RFIG-060",
            "D037 TSQR shrinkage sensitivity",
            "Results: development-only negative",
            "d037_shrinkage_sensitivity",
            "development_only_negative",
            "The fixed shrinkage grid reduced the C06 correction gap at low lambda but did not satisfy the preregistered primary or quantum-specific superiority rule.",
            "Development-only evidence; no Gate 5 revision, NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 6, or quantum advantage.",
        ),
        (
            "RFIG-061",
            "D037 TSQR paired audit and resources",
            "Methods and Results: uncertainty, audit, and compute",
            "d037_paired_audit_resources",
            "development_only_negative",
            "The primary TSQR-08-L025 interval is positive, while all projection, shrinkage, and inner-fold audits are complete and group-disjoint within the recorded resource envelope.",
            "Development-only uncertainty, integrity, and compute evidence; no NASA performance claim, mission claim, calibration/final-test result, hardware/GPU, Gate 5 revision, Gate 6, or quantum advantage.",
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
