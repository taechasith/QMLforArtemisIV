#!/usr/bin/env python3
"""Create publication-style Gate 2 figures from tracked derived CSV files.

The figures are descriptive audit outputs. They do not contain F2 or ML
results, and they must not be presented as evidence of quantum advantage.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.dates import DateFormatter  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data/processed/artemis2/two_body_baseline.csv"
REVISIONS = ROOT / "data/processed/artemis2/oem_release_revisions.csv"
DISCONTINUITIES = ROOT / "data/processed/artemis2/oem_detected_discontinuities.csv"
WINDOWS = ROOT / "data/processed/artemis2/validation_windows.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def configure() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 240,
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def save(fig: plt.Figure, output: Path, name: str) -> str:
    path = output / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return name


def baseline_bar(
    rows: list[dict[str, str]],
    value_key: str,
    ylabel: str,
    title: str,
    output: Path,
    filename: str,
) -> str:
    ordered = sorted(rows, key=lambda row: (row["role"], row["window_id"]))
    labels = [row["window_id"] for row in ordered]
    values = [float(row[value_key]) for row in ordered]
    role_colors = {"calibration": "#275d8c", "tuning": "#c47f17", "validation": "#9d3b3b"}
    colors = [role_colors[row["role"]] for row in ordered]
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.bar(labels, values, color=colors, width=0.78)
    ax.set_yscale("log")
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Frozen arc")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=color, label=role.title())
        for role, color in role_colors.items()
    ]
    ax.legend(handles=handles, frameon=False, ncol=3, loc="upper left")
    fig.text(
        0.01,
        0.01,
        "Earth point-mass-only analytical benchmark; lower is better. Log scale is used because cislunar arcs span orders of magnitude.",
        fontsize=8,
    )
    return save(fig, output, filename)


def revision_summary(
    rows: list[dict[str, str]],
    key: str,
    ylabel: str,
    title: str,
    output: Path,
    filename: str,
) -> str:
    groups: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        groups[int(row["horizon_from_newer_creation_h"])].append(float(row[key]))
    horizons = sorted(groups)
    medians = [median(groups[horizon]) for horizon in horizons]
    maxima = [max(groups[horizon]) for horizon in horizons]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.plot(horizons, medians, marker="o", linewidth=2, label="Median revision")
    ax.plot(horizons, maxima, marker="^", linestyle="--", label="Maximum revision")
    ax.set_xlabel("Forecast horizon from newer release (h)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(frameon=False)
    fig.text(
        0.01,
        0.01,
        "Adjacent-release revision; this is operational forecast robustness, not measurement error or truth residual.",
        fontsize=8,
    )
    return save(fig, output, filename)


def discontinuity_plot(rows: list[dict[str, str]], output: Path) -> str:
    ordered = sorted(
        rows,
        key=lambda row: float(row["maximum_position_loo_error_km"]),
        reverse=True,
    )[:10]
    labels = [row["discontinuity_id"] for row in reversed(ordered)]
    positions = [
        float(row["maximum_position_loo_error_km"]) for row in reversed(ordered)
    ]
    velocities = [
        float(row["maximum_velocity_loo_error_m_s"]) for row in reversed(ordered)
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8), sharey=True)
    axes[0].barh(labels, positions, color="#6c4a8f")
    axes[0].set_xlabel("Position leave-one-out error (km)")
    axes[1].barh(labels, velocities, color="#2b7a78")
    axes[1].set_xlabel("Velocity leave-one-out error (m/s)")
    fig.suptitle("Largest OEM local-curvature or state-transition flags")
    fig.text(
        0.01,
        0.01,
        "Flags are exclusion evidence for clean coast-arc selection; they are not labeled maneuvers.",
        fontsize=8,
    )
    return save(fig, output, "oem_discontinuity_flags.png")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def split_timeline(rows: list[dict[str, str]], output: Path) -> str:
    role_colors = {"calibration": "#275d8c", "tuning": "#c47f17", "validation": "#9d3b3b"}
    fig, ax = plt.subplots(figsize=(11, 4.8))
    for index, row in enumerate(rows):
        start = parse_utc(row["start_utc"])
        stop = parse_utc(row["stop_utc"])
        ax.barh(
            index,
            stop - start,
            left=start,
            height=0.62,
            color=role_colors[row["role"]],
        )
        ax.text(stop, index, f"  {row['window_id']}", va="center", fontsize=8)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(DateFormatter("%d %b\n%H:%M"))
    ax.set_xlabel("UTC")
    ax.set_title("Frozen Artemis II coast-arc split")
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=color, label=role.title())
        for role, color in role_colors.items()
    ]
    ax.legend(handles=handles, frameon=False, ncol=3, loc="upper left")
    fig.text(
        0.01,
        0.01,
        "Windows were declared before simulator fitting; each is six hours and disjoint from the others.",
        fontsize=8,
    )
    return save(fig, output, "frozen_validation_split.png")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/artemis2_gate2_figures")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    configure()
    baseline = read_csv(BASELINE)
    revisions = read_csv(REVISIONS)
    discontinuities = read_csv(DISCONTINUITIES)
    windows = read_csv(WINDOWS)
    figures = [
        baseline_bar(
            baseline,
            "position_rmse_km",
            "Position RMSE (km)",
            "Earth-only baseline: position error across frozen arcs",
            args.output,
            "earth_only_position_rmse.png",
        ),
        baseline_bar(
            baseline,
            "velocity_rmse_m_s",
            "Velocity RMSE (m/s)",
            "Earth-only baseline: velocity error across frozen arcs",
            args.output,
            "earth_only_velocity_rmse.png",
        ),
        revision_summary(
            revisions,
            "position_revision_km",
            "Position revision (km)",
            "Public OEM release revisions by forecast horizon",
            args.output,
            "oem_position_revisions.png",
        ),
        revision_summary(
            revisions,
            "velocity_revision_m_s",
            "Velocity revision (m/s)",
            "Public OEM velocity revisions by forecast horizon",
            args.output,
            "oem_velocity_revisions.png",
        ),
        discontinuity_plot(discontinuities, args.output),
        split_timeline(windows, args.output),
    ]
    manifest = args.output / "figure_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["filename", "source_data", "interpretation", "status"],
            lineterminator="\n",
        )
        writer.writeheader()
        descriptions = {
            figures[0]: ("two_body_baseline.csv", "Earth-only position RMSE by arc", "descriptive Gate 2 result"),
            figures[1]: ("two_body_baseline.csv", "Earth-only velocity RMSE by arc", "descriptive Gate 2 result"),
            figures[2]: ("oem_release_revisions.csv", "Adjacent-release position revisions", "robustness audit, not truth error"),
            figures[3]: ("oem_release_revisions.csv", "Adjacent-release velocity revisions", "robustness audit, not truth error"),
            figures[4]: ("oem_detected_discontinuities.csv", "Top local-curvature flags", "coast-arc exclusion evidence"),
            figures[5]: ("validation_windows.csv", "Predeclared calibration/tuning/validation split", "frozen design, not model performance"),
        }
        for filename in figures:
            source, interpretation, status = descriptions[filename]
            writer.writerow(
                {
                    "filename": filename,
                    "source_data": source,
                    "interpretation": interpretation,
                    "status": status,
                }
            )
    (args.output / "README.md").write_text(
        "# Artemis II Gate 2 figures\n\n"
        "These figures are generated by `scripts/make_gate2_figures.py` from tracked derived CSV files. "
        "They contain no machine-learning or quantum-model results. The Earth-only model is intentionally "
        "a weak analytical benchmark, and adjacent-release revisions are not truth residuals.\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(figures)} figures and a manifest to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
