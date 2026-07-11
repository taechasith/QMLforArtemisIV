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
POST_G01_AUDIT = ROOT / "data/processed/simulator/scenarios/post_d003_g01_audit.csv"
LEDGER = ROOT / "data/processed/simulator/scenarios/generation_ledger.csv"
V2_LEDGER = ROOT / "data/processed/simulator/scenarios/generation_ledger_v2.csv"
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


def draw_g01_pre_post_audit(path: Path) -> None:
    before = next(row for row in read_csv(AUDIT) if row["group_id"] == "G01")
    after = read_csv(POST_G01_AUDIT)[0]
    metrics = ["Schema-invalid\nrows", "Relationship-error\nrows", "No-reference\nsets"]

    def percentages(row: dict[str, str]) -> list[float]:
        return [
            100.0 * int(row["schema_error_records"]) / int(row["observed_records"]),
            100.0
            * int(row["relationship_error_records"])
            / int(row["observed_records"]),
            100.0
            * int(row["no_reference_feasible_sets"])
            / int(row["observed_decision_sets"]),
        ]

    x = np.arange(len(metrics))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8.2, 4.3), constrained_layout=True)
    ax.bar(x - width / 2, percentages(before), width, color=ORANGE, label="Pre-D003")
    after_values = percentages(after)
    ax.bar(x + width / 2, after_values, width, color=GREEN, label="D003-v1")
    ax.scatter(x + width / 2, after_values, marker="D", s=28, color=GREEN, zorder=3)
    for x_value, value in zip(x + width / 2, after_values):
        ax.annotate(
            f"{value:.0f}%",
            (x_value, value),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center",
            color=GREEN,
            fontweight="bold",
        )
    ax.set_xticks(x, metrics)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Affected rows or decision sets (%)")
    ax.set_title("F0 G01 qualification audit before and after D003 repair")
    ax.legend(ncols=2, loc="upper right")
    ax.text(
        0.99,
        0.62,
        "Post-repair: 500 rows valid\n0/100 sets lack a feasible reference",
        transform=ax.transAxes,
        ha="right",
        color=GREEN,
        fontweight="bold",
        bbox={"facecolor": "white", "edgecolor": PALE, "alpha": 0.92, "pad": 5},
    )
    save(fig, path)


def draw_g01_pre_post_runtime(path: Path) -> None:
    before_rows = [
        row
        for row in read_csv(LEDGER)
        if row["fidelity"] == "F0" and row["group_id"] == "G01"
    ]
    after_rows = [
        row
        for row in read_csv(V2_LEDGER)
        if row["fidelity"] == "F0" and row["group_id"] == "G01"
    ]
    values = [float(before_rows[-1]["elapsed_s"]), float(after_rows[-1]["elapsed_s"])]
    fig, ax = plt.subplots(figsize=(7.2, 4.2), constrained_layout=True)
    bars = ax.bar(["Pre-D003 invalid", "D003-v1 valid"], values, color=[ORANGE, GREEN])
    ax.set_ylabel("Wall time (s per 500 rows)")
    ax.set_title("F0 G01 runtime on the reference laptop")
    for bar, value in zip(bars, values):
        ax.annotate(
            f"{value:.1f} s",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontweight="bold",
        )
    ax.text(
        0.5,
        -0.18,
        "Valid run includes numerical targeting, independent propagation,\n"
        "schema/relationship checks, and lunar-constraint sampling.",
        transform=ax.transAxes,
        ha="center",
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
        FigureSpec(
            "RFIG-005",
            "d003_g01_pre_post_audit",
            "F0 G01 pre/post D003 qualification audit",
            "Gate 5 generator repair",
            "Methods: generator qualification",
            "repair_validation_development",
            "data/processed/simulator/scenarios/pre_d003_audit.csv;data/processed/simulator/scenarios/post_d003_g01_audit.csv",
            "The first D003-v1 checkpoint removed all G01 schema and relationship errors and restored a feasible reference in every decision set.",
            "Development qualification only; G01 is nominal U0 and does not establish all-family or higher-fidelity validity.",
            draw_g01_pre_post_audit,
        ),
        FigureSpec(
            "RFIG-006",
            "d003_g01_pre_post_runtime",
            "F0 G01 pre/post D003 runtime",
            "computational methodology",
            "Methods: compute",
            "repair_validation_development",
            "data/processed/simulator/scenarios/generation_ledger.csv;data/processed/simulator/scenarios/generation_ledger_v2.csv",
            "The corrected 500-row G01 run completed in 55.9 seconds on the reference laptop versus 46.2 seconds for the latest invalid attempt.",
            "Single-group wall time; the workloads differ and this is not a speed benchmark.",
            draw_g01_pre_post_runtime,
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
