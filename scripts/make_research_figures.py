#!/usr/bin/env python3
"""Generate the versioned research-paper figure registry."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/research_figures"
AUDIT = ROOT / "data/processed/simulator/scenarios/pre_d003_audit.csv"
LEDGER = ROOT / "data/processed/simulator/scenarios/generation_ledger.csv"
GATES = ROOT / "data/processed/reporting/gate_timeline.csv"
REGISTRY = OUTPUT / "figure_registry.csv"

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
MAGENTA = "#CC79A7"
GRAY = "#5B6573"
PALE = "#E8EDF2"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": "#D7DCE1",
        "grid.linewidth": 0.6,
        "legend.frameon": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-research-figures-v1",
    }
)


@dataclass(frozen=True)
class FigureSpec:
    figure_id: str
    slug: str
    title: str
    phase: str
    paper_section: str
    evidence_status: str
    source_data: str
    caption: str
    claim_boundary: str
    draw: Callable[[Path], None]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save(fig: plt.Figure, path: Path) -> None:
    svg_path = path.with_suffix(".svg")
    fig.savefig(
        path.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV make_research_figures.py"},
    )
    fig.savefig(
        svg_path,
        bbox_inches="tight",
        metadata={"Creator": "QMLforArtemisIV make_research_figures.py", "Date": None},
    )
    plt.close(fig)
    normalized = "\n".join(
        line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()
    )
    svg_path.write_text(normalized + "\n", encoding="utf-8", newline="\n")


def draw_gate_timeline(path: Path) -> None:
    rows = read_csv(GATES)
    decided = [row for row in rows if row["decision_date"]]
    fig, ax = plt.subplots(figsize=(8.2, 3.2), constrained_layout=True)
    dates = [date.fromisoformat(row["decision_date"]) for row in decided]
    y = np.arange(len(decided))
    ax.hlines(y, min(dates), dates, color=PALE, linewidth=8)
    ax.scatter(dates, y, s=95, color=GREEN, edgecolor="white", linewidth=1.5, zorder=3)
    for row, x_value, y_value in zip(decided, dates, y):
        ax.annotate(
            row["gate"],
            (x_value, y_value),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontweight="bold",
        )
    ax.set_yticks([])
    ax.set_xlabel("Human decision date\nGate 5 in progress; Gates 6-7 not opened")
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.set_title("Research governance timeline through Gate 4")
    save(fig, path)


def draw_pre_d003_conformance(path: Path) -> None:
    rows = read_csv(AUDIT)
    labels = [row["group_id"] for row in rows]
    schema_failure = [
        100.0 * int(row["schema_error_records"]) / int(row["observed_records"])
        for row in rows
    ]
    uncertainty_failure = [
        0.0 if row["uncertainty_conformance"] == "true" else 100.0 for row in rows
    ]
    x = np.arange(len(rows))
    width = 0.38
    fig, ax = plt.subplots(figsize=(9.2, 4.2), constrained_layout=True)
    ax.bar(
        x - width / 2, schema_failure, width, color=ORANGE, label="Schema-invalid rows"
    )
    ax.bar(
        x + width / 2,
        uncertainty_failure,
        width,
        color=MAGENTA,
        label="Uncertainty family nonconformant",
    )
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Affected records or group status (%)")
    ax.set_xlabel(
        "7,000/7,000 rows omit required base_trajectory; "
        "12/14 groups use non-frozen uncertainty scales",
        color="#7A2600",
        fontweight="bold",
        labelpad=10,
    )
    ax.set_title("INVALID PRE-D003 EVIDENCE: F0 payload conformance audit")
    ax.legend(ncols=2, loc="upper center")
    save(fig, path)


def draw_pre_d003_feasibility(path: Path) -> None:
    rows = read_csv(AUDIT)
    labels = [row["group_id"] for row in rows]
    feasible = [100.0 * float(row["feasibility_rate"]) for row in rows]
    no_reference = [100.0 * float(row["no_reference_feasible_rate"]) for row in rows]
    x = np.arange(len(rows))
    width = 0.4
    fig, ax = plt.subplots(figsize=(9.2, 4.4), constrained_layout=True)
    ax.bar(x - width / 2, feasible, width, color=BLUE, label="Feasible candidate rows")
    ax.bar(
        x + width / 2,
        no_reference,
        width,
        color=ORANGE,
        label="Decision sets with no feasible reference",
    )
    ax.axhline(50, color=GRAY, linewidth=0.8, linestyle="--")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Rate (%)")
    ax.set_xlabel(
        "Overall: 502/7,000 feasible rows; "
        "1,020/1,400 decision sets lack a feasible reference",
        color="#7A2600",
        fontweight="bold",
        labelpad=10,
    )
    ax.set_title("INVALID PRE-D003 EVIDENCE: candidate feasibility coverage")
    ax.legend(ncols=2, loc="upper center")
    save(fig, path)


def draw_generation_runtime(path: Path) -> None:
    rows = read_csv(LEDGER)
    f0_rows = [row for row in rows if row["fidelity"] == "F0"]
    attempts: dict[str, list[float]] = {}
    for row in f0_rows:
        attempts.setdefault(row["group_id"], []).append(float(row["elapsed_s"]))
    labels = sorted(attempts)
    latest = [attempts[label][-1] for label in labels]
    counts = [len(attempts[label]) for label in labels]
    fig, ax = plt.subplots(figsize=(9.2, 4.2), constrained_layout=True)
    bars = ax.bar(labels, latest, color=BLUE)
    ax.set_ylabel("Latest generation attempt (s per 500 rows)")
    ax.set_title("Reference-laptop F0 generation runtime before D003 repair")
    for bar, attempt_count in zip(bars, counts):
        if attempt_count > 1:
            ax.annotate(
                f"{attempt_count} attempts",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                fontsize=7,
                color=ORANGE,
            )
    total_rows = sum(int(row["records"]) for row in f0_rows)
    total_seconds = sum(float(row["elapsed_s"]) for row in f0_rows)
    ax.text(
        0.99,
        0.95,
        f"Attempt throughput: {total_rows / total_seconds:.1f} rows/s",
        transform=ax.transAxes,
        ha="right",
        color=GRAY,
    )
    save(fig, path)


def specs() -> list[FigureSpec]:
    return [
        FigureSpec(
            "RFIG-001",
            "gate_decision_timeline",
            "Research governance timeline through Gate 4",
            "governance",
            "Methods: governance",
            "accepted_decision_record",
            "data/processed/reporting/gate_timeline.csv",
            "Human decisions closed Gates 0-4 by 2026-07-12; Gate 5 remains in progress.",
            "Dates and statuses only; this figure does not imply scientific success.",
            draw_gate_timeline,
        ),
        FigureSpec(
            "RFIG-002",
            "pre_d003_payload_conformance",
            "Pre-D003 F0 payload conformance failure",
            "Gate 5 generator repair",
            "Supplement: failed methods",
            "invalid_failed_attempt",
            "data/processed/simulator/scenarios/pre_d003_audit.csv",
            "All pre-D003 F0 rows failed the frozen schema; non-U0 groups also used non-frozen uncertainty scales.",
            "Diagnostic evidence only; prohibited as model-performance evidence.",
            draw_pre_d003_conformance,
        ),
        FigureSpec(
            "RFIG-003",
            "pre_d003_feasibility_coverage",
            "Pre-D003 F0 feasibility coverage",
            "Gate 5 generator repair",
            "Supplement: failed methods",
            "invalid_failed_attempt",
            "data/processed/simulator/scenarios/pre_d003_audit.csv",
            "The invalid generator produced sparse feasible candidates and no feasible reference in most decision sets.",
            "Diagnostic evidence only; rates cannot support a benchmark claim.",
            draw_pre_d003_feasibility,
        ),
        FigureSpec(
            "RFIG-004",
            "pre_d003_generation_runtime",
            "Pre-D003 F0 generation runtime",
            "computational methodology",
            "Methods: compute",
            "invalid_workload_timing",
            "data/processed/simulator/scenarios/generation_ledger.csv",
            "Observed F0 attempt runtime by group on the reference laptop before generator repair.",
            "Hardware timing for an invalid workload; retained only for scheduling and audit.",
            draw_generation_runtime,
        ),
    ]


def write_registry(rows: list[dict[str, str]]) -> None:
    fields = list(rows[0])
    with REGISTRY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for spec in specs():
        base = OUTPUT / spec.slug
        spec.draw(base)
        png = base.with_suffix(".png")
        svg = base.with_suffix(".svg")
        rows.append(
            {
                "figure_id": spec.figure_id,
                "title": spec.title,
                "phase": spec.phase,
                "paper_section": spec.paper_section,
                "evidence_status": spec.evidence_status,
                "source_data": spec.source_data,
                "generator": "scripts/make_research_figures.py",
                "png_path": str(png.relative_to(ROOT)).replace("\\", "/"),
                "png_sha256": sha256_file(png),
                "png_bytes": str(png.stat().st_size),
                "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"),
                "svg_sha256": sha256_file(svg),
                "svg_bytes": str(svg.stat().st_size),
                "caption": spec.caption,
                "claim_boundary": spec.claim_boundary,
            }
        )
    write_registry(rows)
    print(f"Generated {len(rows)} registered figures in {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
