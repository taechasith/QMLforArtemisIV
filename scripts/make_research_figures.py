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
from matplotlib import colors as mpl_colors, patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/research_figures"
AUDIT = ROOT / "data/processed/simulator/scenarios/pre_d003_audit.csv"
POST_G01_AUDIT = ROOT / "data/processed/simulator/scenarios/post_d003_g01_audit.csv"
POST_F0_AUDIT = ROOT / "data/processed/simulator/scenarios/post_d003_f0_audit.csv"
POST_F1_G01_AUDIT = (
    ROOT / "data/processed/simulator/scenarios/post_d003_f1_g01_audit.csv"
)
POST_F1_AUDIT = ROOT / "data/processed/simulator/scenarios/post_d003_f1_audit.csv"
F1_RUNTIME = ROOT / "data/processed/reporting/gate5_f1_campaign_runtime.csv"
POST_F2_G01_AUDIT = (
    ROOT / "data/processed/simulator/scenarios/post_d003_f2_g01_audit.csv"
)
POST_F2_AUDIT = ROOT / "data/processed/simulator/scenarios/post_d003_f2_audit.csv"
F2_RUNTIME = ROOT / "data/processed/reporting/gate5_f2_campaign_runtime.csv"
GATE5_HARDENING = ROOT / "data/processed/reporting/gate5_literature_hardening_matrix.csv"
GATE5_FOLDS = ROOT / "data/processed/reporting/gate5_cv_fold_manifest.csv"
SEARCH_LOG = ROOT / "literature/search_log.csv"
SCREENING_LOG = ROOT / "literature/screening_log.csv"
EXTRACTION_MATRIX = ROOT / "literature/extraction_matrix.csv"
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
INK = "#1F2937"
GOOD_PALE = "#EAF7F1"
WARNING_PALE = "#FFF0E6"


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


def draw_table_figure(
    path: Path,
    title: str,
    columns: list[str],
    rows: list[list[str]],
    footer: str,
    *,
    figsize: tuple[float, float] = (8.8, 3.8),
    col_widths: list[float] | None = None,
    row_facecolors: list[str] | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    ax.set_axis_off()
    ax.text(
        0.0,
        0.98,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )
    table = ax.table(
        cellText=rows,
        colLabels=columns,
        cellLoc="left",
        colLoc="left",
        bbox=[0.0, 0.18, 1.0, 0.66],
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    for (row_index, _column_index), cell in table.get_celld().items():
        cell.set_edgecolor("#C8D0D8")
        cell.set_linewidth(0.6)
        cell.PAD = 0.04
        text = cell.get_text()
        text.set_color(INK)
        text.set_wrap(True)
        if row_index == 0:
            cell.set_facecolor(PALE)
            text.set_fontweight("bold")
        else:
            color_index = row_index - 1
            if row_facecolors and color_index < len(row_facecolors):
                cell.set_facecolor(row_facecolors[color_index])
            else:
                cell.set_facecolor("white")
    ax.text(
        0.0,
        0.06,
        footer,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8,
        color=GRAY,
    )
    save(fig, path)


def draw_gate_timeline(path: Path) -> None:
    rows = read_csv(GATES)
    fig, ax = plt.subplots(figsize=(9.0, 4.0), constrained_layout=True)
    ax.set_axis_off()
    ax.text(
        0.0,
        0.98,
        "Research governance decision diagram through Gate 4",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )
    labels = {
        "Gate 0": "Governance",
        "Gate 1": "NASA-first scope",
        "Gate 2": "Data/numeric freeze",
        "Gate 3": "Simulator credibility",
        "Gate 4": "Phase 1 freeze",
        "Gate 5": "Development generation",
        "Gate 6": "Mission experiment",
        "Gate 7": "Claims and release",
    }
    positions = [
        (0.02, 0.62),
        (0.22, 0.62),
        (0.42, 0.62),
        (0.62, 0.62),
        (0.82, 0.62),
        (0.30, 0.28),
        (0.52, 0.28),
        (0.74, 0.28),
    ]
    box_w = 0.16
    box_h = 0.18
    rows_by_gate = {row["gate"]: row for row in rows}
    for index, (gate, (x_value, y_value)) in enumerate(zip(labels, positions)):
        row = rows_by_gate[gate]
        status = row["status"].replace("_", " ")
        if row["status"] == "accepted":
            facecolor = GOOD_PALE
            edgecolor = GREEN
        elif row["status"] == "in_progress":
            facecolor = "#FFF8E5"
            edgecolor = ORANGE
        else:
            facecolor = PALE
            edgecolor = GRAY
        card = patches.FancyBboxPatch(
            (x_value, y_value),
            box_w,
            box_h,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            transform=ax.transAxes,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.1,
        )
        ax.add_patch(card)
        date_text = (
            date.fromisoformat(row["decision_date"]).isoformat()
            if row["decision_date"]
            else status
        )
        ax.text(
            x_value + 0.012,
            y_value + box_h - 0.035,
            gate,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            fontweight="bold",
            color=INK,
        )
        ax.text(
            x_value + 0.012,
            y_value + box_h - 0.078,
            labels[gate],
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8,
            color=INK,
        )
        ax.text(
            x_value + 0.012,
            y_value + 0.024,
            date_text,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=7.5,
            color=GRAY,
        )
        if index < len(positions) - 1:
            next_x, next_y = positions[index + 1]
            if gate == "Gate 4":
                x_start = x_value + box_w / 2
                y_start = y_value - 0.006
                x_end = next_x + box_w / 2
                y_end = next_y + box_h + 0.006
                mid_y = (y_start + y_end) / 2
                ax.plot(
                    [x_start, x_start, x_end],
                    [y_start, mid_y, mid_y],
                    transform=ax.transAxes,
                    color=GRAY,
                    linewidth=0.9,
                )
                arrow = patches.FancyArrowPatch(
                    (x_end, mid_y),
                    (x_end, y_end),
                    transform=ax.transAxes,
                    arrowstyle="-|>",
                    mutation_scale=10,
                    linewidth=0.9,
                    color=GRAY,
                )
                ax.add_patch(arrow)
                continue
            else:
                x_start = x_value + box_w + 0.005
                y_start = y_value + box_h / 2
                x_end = next_x - 0.005
                y_end = next_y + box_h / 2
                connectionstyle = "arc3,rad=0.0"
            arrow = patches.FancyArrowPatch(
                (x_start, y_start),
                (x_end, y_end),
                transform=ax.transAxes,
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=0.9,
                color=GRAY,
                connectionstyle=connectionstyle,
            )
            ax.add_patch(arrow)
    ax.text(
        0.0,
        0.08,
        "Diagram only: dates and decision states do not imply scientific success.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8,
        color=GRAY,
    )
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

    def record_pct(row: dict[str, str], key: str) -> str:
        count = int(row[key])
        total = int(row["observed_records"])
        return f"{count}/{total} ({100.0 * count / total:.0f}%)"

    def set_pct(row: dict[str, str]) -> str:
        count = int(row["no_reference_feasible_sets"])
        total = int(row["observed_decision_sets"])
        return f"{count}/{total} ({100.0 * count / total:.0f}%)"

    rows = [
        [
            "Schema-invalid rows",
            record_pct(before, "schema_error_records"),
            record_pct(after, "schema_error_records"),
            "Cleared by D003-v1",
        ],
        [
            "Relationship-error rows",
            record_pct(before, "relationship_error_records"),
            record_pct(after, "relationship_error_records"),
            "Cleared by D003-v1",
        ],
        [
            "Decision sets without feasible reference",
            set_pct(before),
            set_pct(after),
            "Feasible reference restored",
        ],
    ]
    draw_table_figure(
        path,
        "F0 G01 qualification audit before and after D003 repair",
        ["Audit measure", "Pre-D003", "D003-v1", "Interpretation"],
        rows,
        "Exact small-factor audit table: 500 post-repair rows are valid and 0/100 decision sets lack a feasible reference.",
        figsize=(9.2, 3.7),
        col_widths=[0.32, 0.18, 0.18, 0.32],
    )


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
    before = before_rows[-1]
    after = after_rows[-1]
    before_elapsed = float(before["elapsed_s"])
    after_elapsed = float(after["elapsed_s"])
    delta = after_elapsed - before_elapsed
    rows = [
        [
            "Pre-D003 invalid",
            before["records"],
            f"{before_elapsed:.1f} s",
            "Schema-invalid workload; retained for audit only",
        ],
        [
            "D003-v1 valid",
            after["records"],
            f"{after_elapsed:.1f} s",
            "Valid workload with targeting, propagation, and checks",
        ],
        [
            "Difference",
            "500-row group",
            f"{delta:+.1f} s ({after_elapsed / before_elapsed:.2f}x)",
            "Not a speed benchmark because the workloads differ",
        ],
    ]
    draw_table_figure(
        path,
        "F0 G01 runtime on the reference laptop",
        ["Workload", "Records", "Wall time", "Use in paper"],
        rows,
        "Exact small comparison table; values support scheduling context only, not a performance claim.",
        figsize=(8.8, 3.6),
        col_widths=[0.22, 0.16, 0.18, 0.44],
        row_facecolors=[WARNING_PALE, GOOD_PALE, "white"],
    )


def draw_f0_pre_post_conformance(path: Path) -> None:
    before = read_csv(AUDIT)
    after = read_csv(POST_F0_AUDIT)

    def aggregate_counts(rows: list[dict[str, str]]) -> tuple[int, int, int, int, int]:
        records = sum(int(row["observed_records"]) for row in rows)
        groups = len(rows)
        schema = sum(int(row["schema_error_records"]) for row in rows)
        relationship = sum(int(row["relationship_error_records"]) for row in rows)
        uncertainty = sum(row["uncertainty_conformance"] != "true" for row in rows)
        return records, groups, schema, relationship, uncertainty

    before_records, before_groups, before_schema, before_relationship, before_unc = (
        aggregate_counts(before)
    )
    after_records, after_groups, after_schema, after_relationship, after_unc = (
        aggregate_counts(after)
    )
    rows = [
        [
            "Schema-invalid rows",
            f"{before_schema}/{before_records} ({100.0 * before_schema / before_records:.0f}%)",
            f"{after_schema}/{after_records} ({100.0 * after_schema / after_records:.0f}%)",
            "All recorded schema failures removed",
        ],
        [
            "Relationship-error rows",
            f"{before_relationship}/{before_records} ({100.0 * before_relationship / before_records:.0f}%)",
            f"{after_relationship}/{after_records} ({100.0 * after_relationship / after_records:.0f}%)",
            "All relationship failures removed",
        ],
        [
            "Uncertainty-nonconformant groups",
            f"{before_unc}/{before_groups} ({100.0 * before_unc / before_groups:.0f}%)",
            f"{after_unc}/{after_groups} ({100.0 * after_unc / after_groups:.0f}%)",
            "All groups conform to frozen uncertainty scales",
        ],
    ]
    draw_table_figure(
        path,
        "All unlocked F0 payloads before and after D003 repair",
        ["Audit measure", "Pre-D003", "D003-v1", "Interpretation"],
        rows,
        "Exact small-factor conformance table; this establishes payload repair only, not model performance.",
        figsize=(9.4, 3.7),
        col_widths=[0.33, 0.18, 0.18, 0.31],
    )


def draw_f0_feasibility(path: Path) -> None:
    rows = read_csv(POST_F0_AUDIT)
    labels = [row["group_id"] for row in rows]
    feasible = [100.0 * float(row["feasibility_rate"]) for row in rows]
    no_reference = [100.0 * float(row["no_reference_feasible_rate"]) for row in rows]
    x = np.arange(len(rows))
    width = 0.4
    fig, ax = plt.subplots(figsize=(9.4, 4.5), constrained_layout=True)
    ax.axvspan(11.5, 13.5, color=PALE, zorder=0)
    ax.bar(x - width / 2, feasible, width, color=BLUE, label="Feasible candidate rows")
    ax.bar(
        x + width / 2,
        no_reference,
        width,
        color=ORANGE,
        label="Decision sets with no feasible reference",
    )
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Rate (%)")
    ax.set_xlabel(
        "Development G01-G12 | shaded: uncertainty-calibration G13-G14\n"
        "Overall: 2,339/7,000 feasible rows; 319/1,400 sets lack a feasible reference"
    )
    ax.set_title("VALID D003-v1 F0 candidate feasibility coverage")
    ax.legend(ncols=2, loc="upper center")
    save(fig, path)


def draw_f0_runtime(path: Path) -> None:
    rows = [row for row in read_csv(V2_LEDGER) if row["fidelity"] == "F0"]
    labels = [row["group_id"] for row in rows]
    values = [float(row["elapsed_s"]) for row in rows]
    colors = [BLUE if row["split"] == "development" else MAGENTA for row in rows]
    fig, ax = plt.subplots(figsize=(9.4, 4.3), constrained_layout=True)
    ax.bar(labels, values, color=colors)
    ax.set_ylabel("Wall time (s per 500 rows)")
    ax.set_xlabel("G01-G12 development; G13-G14 uncertainty calibration")
    ax.set_title("D003-v1 F0 generation runtime on the reference laptop")
    ax.text(
        0.99,
        0.95,
        f"Total: {sum(values):.1f} s | Mean: {np.mean(values):.1f} s/group",
        transform=ax.transAxes,
        ha="right",
        color=GRAY,
    )
    save(fig, path)



def draw_f1_feasibility(path: Path) -> None:
    rows = sorted(read_csv(POST_F1_AUDIT), key=lambda row: int(row["group_id"][1:]))
    labels = [
        row["group_id"] if row["split"] == "development" else f"{row['group_id']}*"
        for row in rows
    ]
    measures = [
        (
            "Feasible candidate rows",
            np.array([100.0 * float(row["feasibility_rate"]) for row in rows]),
            mpl_colors.LinearSegmentedColormap.from_list(
                "f1_feasible", ["#F4F8FB", BLUE]
            ),
        ),
        (
            "Decision sets without feasible reference",
            np.array(
                [100.0 * float(row["no_reference_feasible_rate"]) for row in rows]
            ),
            mpl_colors.LinearSegmentedColormap.from_list(
                "f1_no_reference", ["#FFF7F2", ORANGE]
            ),
        ),
    ]
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(10.2, 3.8),
        sharex=True,
        constrained_layout=True,
        gridspec_kw={"height_ratios": [1, 1]},
    )
    for ax, (label, values, color_map) in zip(axes, measures):
        image = ax.imshow(
            values[np.newaxis, :],
            aspect="auto",
            cmap=color_map,
            vmin=0,
            vmax=100,
            interpolation="nearest",
        )
        ax.set_yticks([0], [label])
        ax.grid(False)
        ax.axvline(11.5, color=INK, linewidth=1.1, linestyle="--")
        for index, value in enumerate(values):
            ax.text(
                index,
                0,
                f"{value:.1f}",
                ha="center",
                va="center",
                fontsize=7.5,
                color="white" if value >= 55 else INK,
                fontweight="bold" if value >= 90 else "normal",
            )
        colorbar = fig.colorbar(image, ax=ax, fraction=0.018, pad=0.012)
        colorbar.set_label("%", rotation=0, labelpad=7)
        colorbar.set_ticks([0, 50, 100])
    axes[0].set_title("D003-v1 F1 candidate feasibility coverage", loc="left")
    axes[1].set_xticks(np.arange(len(labels)), labels)
    axes[1].set_xlabel(
        "G01-G12 development; G13-G14 uncertainty calibration (*)\n"
        "6,436/35,000 feasible rows; 4,215/7,000 decision sets have no feasible reference"
    )
    save(fig, path)


def draw_f1_runtime(path: Path) -> None:
    ledger_rows = sorted(
        [row for row in read_csv(V2_LEDGER) if row["fidelity"] == "F1"],
        key=lambda row: int(row["group_id"][1:]),
    )
    runtime_rows = {row["stage"]: row for row in read_csv(F1_RUNTIME)}
    scaleup = runtime_rows["parallel_scaleup"]
    labels = [row["group_id"] for row in ledger_rows]
    minutes = [float(row["elapsed_s"]) / 60.0 for row in ledger_rows]
    colors = [BLUE if row["split"] == "development" else MAGENTA for row in ledger_rows]
    fig, ax = plt.subplots(figsize=(10.0, 4.7), constrained_layout=True)
    bars = ax.bar(labels, minutes, color=colors, edgecolor=INK, linewidth=0.5)
    for bar, row, value in zip(bars, ledger_rows, minutes):
        if row["split"] == "uncertainty_calibration":
            bar.set_hatch("//")
        ax.annotate(
            f"{value:.1f}",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7,
            color=INK,
        )
    projected_mean_minutes = float(scaleup["projected_group_work_s"]) / 13 / 60
    ax.hlines(
        projected_mean_minutes,
        0.5,
        13.5,
        color=GRAY,
        linewidth=1.0,
        linestyle="--",
        label=f"Pre-scale-up projection: {projected_mean_minutes:.1f} min/group",
    )
    ax.set_ylim(0, max(minutes) * 1.15)
    ax.set_ylabel("Wall time per 2,500-row group (min)")
    ax.set_xlabel(
        "G01 serial qualification; G02-G12 development; G13-G14 calibration (hatched)\n"
        "G02-G14: 17.68 worker-h in 5.04 wall-h at effective concurrency 3.51"
    )
    ax.set_title("D003-v1 F1 generation runtime on the reference laptop")
    ax.legend(loc="upper left")
    save(fig, path)



def draw_f2_feasibility(path: Path) -> None:
    rows = sorted(read_csv(POST_F2_AUDIT), key=lambda row: int(row["group_id"][1:]))
    labels = [
        row["group_id"] if row["split"] == "development" else f"{row['group_id']}*"
        for row in rows
    ]
    measures = [
        (
            "Feasible candidate rows",
            np.array([100.0 * float(row["feasibility_rate"]) for row in rows]),
            mpl_colors.LinearSegmentedColormap.from_list(
                "f2_feasible", ["#F4F8FB", BLUE]
            ),
        ),
        (
            "Decision sets without feasible reference",
            np.array(
                [100.0 * float(row["no_reference_feasible_rate"]) for row in rows]
            ),
            mpl_colors.LinearSegmentedColormap.from_list(
                "f2_no_reference", ["#FFF7F2", ORANGE]
            ),
        ),
    ]
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(10.2, 3.8),
        sharex=True,
        constrained_layout=True,
        gridspec_kw={"height_ratios": [1, 1]},
    )
    for ax, (label, values, color_map) in zip(axes, measures):
        image = ax.imshow(
            values[np.newaxis, :],
            aspect="auto",
            cmap=color_map,
            vmin=0,
            vmax=100,
            interpolation="nearest",
        )
        ax.set_yticks([0], [label])
        ax.grid(False)
        ax.axvline(11.5, color=INK, linewidth=1.1, linestyle="--")
        for index, value in enumerate(values):
            ax.text(
                index,
                0,
                f"{value:.1f}",
                ha="center",
                va="center",
                fontsize=7.5,
                color="white" if value >= 55 else INK,
                fontweight="bold" if value >= 90 else "normal",
            )
        colorbar = fig.colorbar(image, ax=ax, fraction=0.018, pad=0.012)
        colorbar.set_label("%", rotation=0, labelpad=7)
        colorbar.set_ticks([0, 50, 100])
    axes[0].set_title("D003-v1 F2 candidate feasibility coverage", loc="left")
    axes[1].set_xticks(np.arange(len(labels)), labels)
    axes[1].set_xlabel(
        "G01-G12 development; G13-G14 uncertainty calibration (*)\n"
        "642/3,500 feasible rows; 423/700 decision sets have no feasible reference"
    )
    save(fig, path)


def draw_f2_runtime(path: Path) -> None:
    ledger_rows = sorted(
        [row for row in read_csv(V2_LEDGER) if row["fidelity"] == "F2"],
        key=lambda row: int(row["group_id"][1:]),
    )
    runtime_rows = {row["stage"]: row for row in read_csv(F2_RUNTIME)}
    projection = runtime_rows["parallel_scaleup_projection"]
    actual = runtime_rows["parallel_scaleup_actual"]
    labels = [row["group_id"] for row in ledger_rows]
    minutes = [float(row["elapsed_s"]) / 60.0 for row in ledger_rows]
    colors = [BLUE if row["split"] == "development" else MAGENTA for row in ledger_rows]
    fig, ax = plt.subplots(figsize=(10.0, 4.7), constrained_layout=True)
    bars = ax.bar(labels, minutes, color=colors, edgecolor=INK, linewidth=0.5)
    for bar, row, value in zip(bars, ledger_rows, minutes):
        if row["split"] == "uncertainty_calibration":
            bar.set_hatch("//")
        ax.annotate(
            f"{value:.1f}",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7,
            color=INK,
        )
    projected_mean_minutes = float(projection["projected_group_work_s"]) / 13 / 60
    ax.hlines(
        projected_mean_minutes,
        0.5,
        13.5,
        color=GRAY,
        linewidth=1.0,
        linestyle="--",
        label=f"Pre-scale-up projection: {projected_mean_minutes:.1f} min/group",
    )
    ax.set_ylim(0, max(max(minutes) * 1.15, projected_mean_minutes * 1.15))
    ax.set_ylabel("Wall time per 250-row group (min)")
    ax.set_xlabel(
        "G01 serial qualification; G02-G12 development; G13-G14 calibration (hatched)\n"
        f"G02-G14: {float(actual['summed_group_work_s']) / 3600:.2f} worker-h in "
        f"{float(actual['stage_wall_s']) / 3600:.2f} wall-h at effective concurrency "
        f"{float(actual['effective_concurrency']):.2f}"
    )
    ax.set_title("D003-v1 F2 generation runtime on the reference laptop")
    ax.legend(loc="upper left")
    save(fig, path)


def draw_f0_f1_f2_summary(path: Path) -> None:
    audits = {
        "F0": read_csv(POST_F0_AUDIT),
        "F1": read_csv(POST_F1_AUDIT),
        "F2": read_csv(POST_F2_AUDIT),
    }
    ledger = read_csv(V2_LEDGER)

    def totals(fidelity: str) -> dict[str, float]:
        rows = audits[fidelity]
        return {
            "groups": len(rows),
            "records": sum(int(row["observed_records"]) for row in rows),
            "decisions": sum(int(row["observed_decision_sets"]) for row in rows),
            "feasible": sum(int(row["feasible_records"]) for row in rows),
            "no_reference": sum(int(row["no_reference_feasible_sets"]) for row in rows),
            "nonconverged": sum(int(row["nonconverged_records"]) for row in rows),
            "work_s": sum(
                float(row["elapsed_s"]) for row in ledger if row["fidelity"] == fidelity
            ),
        }

    values = {fidelity: totals(fidelity) for fidelity in ("F0", "F1", "F2")}

    def count_rate(fidelity: str, key: str, denominator: str) -> str:
        count = values[fidelity][key]
        total = values[fidelity][denominator]
        return f"{int(count):,}/{int(total):,} ({100.0 * count / total:.1f}%)"

    rows = [
        ["Valid groups", "14/14", "14/14", "14/14", "All unlocked groups"],
        ["Candidate rows", "7,000", "35,000", "3,500", "Five candidates per set"],
        [
            "Feasible candidate rows",
            count_rate("F0", "feasible", "records"),
            count_rate("F1", "feasible", "records"),
            count_rate("F2", "feasible", "records"),
            "Coverage diagnostic only",
        ],
        [
            "Sets without feasible reference",
            count_rate("F0", "no_reference", "decisions"),
            count_rate("F1", "no_reference", "decisions"),
            count_rate("F2", "no_reference", "decisions"),
            "Frozen penalty rule",
        ],
        ["Nonconverged rows", "0", "0", "0", "No case removed"],
        [
            "Summed group work",
            f"{values['F0']['work_s'] / 3600:.2f} h",
            f"{values['F1']['work_s'] / 3600:.2f} h",
            f"{values['F2']['work_s'] / 3600:.2f} h",
            "Reference laptop",
        ],
    ]
    draw_table_figure(
        path,
        "D003-v1 full unlocked scenario campaign audit summary",
        ["Audit measure", "F0", "F1", "F2", "Interpretation"],
        rows,
        "Exact three-fidelity table: all 45,500 unlocked rows are valid; calibration rows and coverage diagnostics cannot support model selection.",
        figsize=(10.8, 4.9),
        col_widths=[0.25, 0.15, 0.15, 0.15, 0.30],
        row_facecolors=[GOOD_PALE, "white", "white", WARNING_PALE, GOOD_PALE, "white"],
    )


def draw_g01_three_fidelity_checkpoint(path: Path) -> None:
    audits = {
        "F0": next(row for row in read_csv(POST_F0_AUDIT) if row["group_id"] == "G01"),
        "F1": read_csv(POST_F1_G01_AUDIT)[0],
        "F2": read_csv(POST_F2_G01_AUDIT)[0],
    }
    ledger_rows = {
        row["fidelity"]: row
        for row in read_csv(V2_LEDGER)
        if row["group_id"] == "G01" and row["fidelity"] in audits
    }
    projection = next(
        row
        for row in read_csv(F2_RUNTIME)
        if row["stage"] == "parallel_scaleup_projection"
    )
    rows = []
    for fidelity in ("F0", "F1", "F2"):
        audit = audits[fidelity]
        ledger = ledger_rows[fidelity]
        observed = int(audit["observed_records"])
        feasible = int(audit["feasible_records"])
        decisions = int(audit["observed_decision_sets"])
        no_reference = int(audit["no_reference_feasible_sets"])
        elapsed = float(ledger["elapsed_s"])
        rows.append(
            [
                f"{fidelity} G01",
                f"{observed:,}",
                f"{feasible:,}/{observed:,} ({100.0 * feasible / observed:.0f}%)",
                f"{no_reference}/{decisions} ({100.0 * no_reference / decisions:.0f}%)",
                f"{elapsed / observed:.3f}",
                f"{elapsed:,.1f} s",
            ]
        )
    planning_hours = float(projection["projected_planning_wall_s"]) / 3600
    draw_table_figure(
        path,
        "VALID D003-v1 G01 qualification across F0, F1, and F2",
        [
            "Checkpoint",
            "Rows",
            "Feasible rows",
            "No-reference sets",
            "Seconds/row",
            "Wall time",
        ],
        rows,
        f"Exact nominal-U0 table: every row is valid and every set retains a reference; F2 G02-G14 planning estimate is {planning_hours:.2f} wall-hours at two workers with 25% margin.",
        figsize=(10.2, 4.0),
        col_widths=[0.16, 0.10, 0.22, 0.21, 0.14, 0.17],
        row_facecolors=[GOOD_PALE, GOOD_PALE, GOOD_PALE],
    )


def draw_literature_refresh_flow(path: Path) -> None:
    search_rows = read_csv(SEARCH_LOG)
    screening_rows = read_csv(SCREENING_LOG)
    extraction_rows = read_csv(EXTRACTION_MATRIX)
    retrieved = sum(int(row["records_retrieved"]) for row in search_rows)
    decision_counts: dict[str, int] = {}
    for row in screening_rows:
        decision = row["decision"]
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
    openalex = [row for row in search_rows if row["database"] == "OpenAlex"]
    openalex_complete = sum(
        row["coverage_status"].startswith("complete") for row in openalex
    )
    openalex_partial = len(openalex) - openalex_complete

    fig, ax = plt.subplots(figsize=(10.4, 4.8), constrained_layout=True)
    ax.set_axis_off()
    ax.text(
        0.0,
        0.98,
        "Post-acceptance Gate 4 literature discovery refresh",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )

    def card(
        x_value: float,
        y_value: float,
        width: float,
        height: float,
        heading: str,
        body: str,
        facecolor: str,
        edgecolor: str,
        *,
        linestyle: str = "-",
    ) -> None:
        box = patches.FancyBboxPatch(
            (x_value, y_value),
            width,
            height,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            transform=ax.transAxes,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.1,
            linestyle=linestyle,
        )
        ax.add_patch(box)
        ax.text(
            x_value + 0.015,
            y_value + height - 0.045,
            heading,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            fontweight="bold",
            color=INK,
        )
        ax.text(
            x_value + 0.015,
            y_value + height - 0.095,
            body,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8,
            color=INK,
            linespacing=1.35,
        )

    def arrow(start: tuple[float, float], end: tuple[float, float]) -> None:
        ax.add_patch(
            patches.FancyArrowPatch(
                start,
                end,
                transform=ax.transAxes,
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=0.9,
                color=GRAY,
            )
        )

    card(
        0.02,
        0.58,
        0.18,
        0.22,
        "Frozen search interfaces",
        f"{len(search_rows)} runs\n7 concepts (S1-S7)",
        PALE,
        GRAY,
    )
    card(
        0.27,
        0.58,
        0.24,
        0.22,
        "Metadata retrieved",
        f"{retrieved:,} raw API rows\nOpenAlex: {openalex_complete} complete, {openalex_partial} partial",
        "#EAF3F8",
        BLUE,
    )
    card(
        0.58,
        0.58,
        0.20,
        0.22,
        "Current discovery ledger",
        f"{len(screening_rows):,} unique\ncanonical keys",
        GOOD_PALE,
        GREEN,
    )
    arrow((0.20, 0.69), (0.27, 0.69))
    arrow((0.51, 0.69), (0.58, 0.69))

    branch_y = 0.17
    branch_width = 0.18
    branches = [
        (
            0.10,
            "Title/abstract exclude",
            f"{decision_counts.get('exclude', 0):,} rows",
            PALE,
            GRAY,
        ),
        (
            0.35,
            "Pending full text",
            f"{decision_counts.get('include_for_full_text', 0):,} rows",
            WARNING_PALE,
            ORANGE,
        ),
        (
            0.60,
            "Provisional include",
            f"{decision_counts.get('include', 0):,} rows",
            "#F8ECF4",
            MAGENTA,
        ),
    ]
    junction = (0.68, 0.47)
    arrow((0.68, 0.58), junction)
    for x_value, heading, body, facecolor, edgecolor in branches:
        card(
            x_value,
            branch_y,
            branch_width,
            0.18,
            heading,
            body,
            facecolor,
            edgecolor,
        )
        arrow(junction, (x_value + branch_width / 2, branch_y + 0.18))

    card(
        0.83,
        0.17,
        0.15,
        0.26,
        "Gate 4 evidence",
        f"{len(extraction_rows)} extracted\nrecords remain\nunchanged",
        "white",
        INK,
        linestyle="--",
    )
    ax.text(
        0.0,
        0.045,
        "Discovery refresh only: 926 full-text screens remain open; no model, threshold, split, or accepted evidence claim changed.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8,
        color=GRAY,
    )
    save(fig, path)


def draw_gate5_literature_hardening(path: Path) -> None:
    rows = read_csv(GATE5_HARDENING)
    columns = [
        ("ranking_guard", "Ranking\nguard"),
        ("registered_candidate", "Registered\ncandidate"),
        ("diagnostic_reporting", "Diagnostic\nreport"),
        ("failure_diagnostic", "Failure\nmode"),
        ("interpretation_control", "Interpretation\ncontrol"),
        ("deferred", "Deferred"),
        ("excluded", "Excluded"),
    ]
    color_by_use = {
        "ranking_guard": GREEN,
        "registered_candidate": BLUE,
        "diagnostic_reporting": ORANGE,
        "failure_diagnostic": MAGENTA,
        "interpretation_control": "#56B4E9",
        "deferred": GRAY,
        "excluded": "#8B5A2B",
    }
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(10.8, 5.9))
    fig.subplots_adjust(left=0.28, right=0.98, top=0.88, bottom=0.23)
    ax.set_xlim(-0.5, len(columns) - 0.5)
    ax.set_ylim(-0.65, len(rows) - 0.35)
    ax.invert_yaxis()
    ax.set_xticks(np.arange(len(columns)), [label for _, label in columns])
    ax.set_yticks(y, [row["evidence_domain"] for row in rows])
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(False)
    ax.set_title("Gate 5 literature-hardening controls before model fitting")

    for row_index, row in enumerate(rows):
        ax.axhspan(
            row_index - 0.5,
            row_index + 0.5,
            color=PALE if row_index % 2 else "white",
            alpha=0.55,
            zorder=0,
        )
        decision_use = row["decision_use"]
        column_index = next(index for index, (key, _) in enumerate(columns) if key == decision_use)
        ax.scatter(
            column_index,
            row_index,
            marker="s",
            s=560,
            color=color_by_use[decision_use],
            edgecolor=INK,
            linewidth=0.6,
            zorder=3,
        )
        ax.text(
            column_index,
            row_index,
            "set",
            ha="center",
            va="center",
            fontsize=7.5,
            color="white",
            fontweight="bold",
            zorder=4,
        )

    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(
        0.28,
        0.055,
        "Source: gate5_literature_hardening_matrix.csv. Matrix records pre-fit controls only; it adds no model family, split, threshold, or final-test access.",
        ha="left",
        va="bottom",
        fontsize=8,
        color=GRAY,
    )
    save(fig, path)


def draw_gate5_cv_folds(path: Path) -> None:
    rows = read_csv(GATE5_FOLDS)
    by_fold: dict[str, dict[str, object]] = {}
    for row in rows:
        fold = row["fold_id"]
        summary = by_fold.setdefault(
            fold,
            {"groups": [], "F0": 0, "F1": 0, "F2": 0},
        )
        summary["groups"].append(row["group_id"])
        for fidelity, field in (("F0", "f0_rows"), ("F1", "f1_rows"), ("F2", "f2_rows")):
            summary[fidelity] += int(row[field])

    folds = sorted(by_fold)
    x = np.arange(len(folds))
    fig, ax = plt.subplots(figsize=(9.6, 5.5))
    fig.subplots_adjust(left=0.10, right=0.98, top=0.84, bottom=0.22)
    bottom = np.zeros(len(folds))
    palette = {"F0": BLUE, "F1": ORANGE, "F2": GRAY}
    for fidelity in ("F0", "F1", "F2"):
        values = np.asarray([int(by_fold[fold][fidelity]) for fold in folds])
        ax.bar(
            x,
            values,
            bottom=bottom,
            width=0.68,
            color=palette[fidelity],
            edgecolor=INK,
            linewidth=0.6,
            label=fidelity,
        )
        bottom += values
    for index, fold in enumerate(folds):
        groups = ", ".join(sorted(by_fold[fold]["groups"]))
        ax.text(
            index,
            bottom[index] + 220,
            f"{int(bottom[index]):,} rows\n{groups}",
            ha="center",
            va="bottom",
            fontsize=8,
            color=INK,
        )
    ax.set_xticks(x, folds)
    ax.set_ylabel("Validation rows")
    ax.set_ylim(0, max(bottom) * 1.22)
    ax.set_title("Gate 5 grouped cross-validation fold allocation")
    ax.legend(title="Fidelity", ncols=3, frameon=False, loc="upper right")
    ax.grid(axis="x", visible=False)
    fig.text(
        0.10,
        0.055,
        "Source: gate5_cv_fold_manifest.csv. Whole groups never cross folds; assignment balances frozen uncertainty/trajectory design strata and uses no outcomes.",
        ha="left",
        va="bottom",
        fontsize=8,
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
        FigureSpec(
            "RFIG-007",
            "d003_f0_pre_post_conformance",
            "All F0 pre/post D003 conformance",
            "Gate 5 generator repair",
            "Methods: generator qualification",
            "repair_validation_development",
            "data/processed/simulator/scenarios/pre_d003_audit.csv;data/processed/simulator/scenarios/post_d003_f0_audit.csv",
            "D003-v1 removed all recorded schema, relationship, and uncertainty-conformance failures across the 7,000 unlocked F0 rows.",
            "Conformance evidence only; this does not establish model performance or higher-fidelity validity.",
            draw_f0_pre_post_conformance,
        ),
        FigureSpec(
            "RFIG-008",
            "d003_f0_feasibility_coverage",
            "Valid D003-v1 F0 feasibility coverage",
            "Gate 5 scenario generation",
            "Methods: scenario coverage",
            "development_and_calibration_diagnostic",
            "data/processed/simulator/scenarios/post_d003_f0_audit.csv",
            "Across valid F0 payloads, 2,339 of 7,000 candidates are feasible and 319 of 1,400 decision sets have no feasible numerical reference.",
            "Development/calibration diagnostic only; calibration groups are shaded and cannot support model selection.",
            draw_f0_feasibility,
        ),
        FigureSpec(
            "RFIG-009",
            "d003_f0_generation_runtime",
            "D003-v1 F0 generation runtime",
            "computational methodology",
            "Methods: compute",
            "repair_validation_development",
            "data/processed/simulator/scenarios/generation_ledger_v2.csv",
            "The 14 corrected F0 groups required 542.1 seconds of measured group work on the reference laptop, with 16.4-56.7 seconds per 500 rows.",
            "Serial local wall time for F0 only; it is not a projection of F1/F2 cost.",
            draw_f0_runtime,
        ),
        FigureSpec(
            "RFIG-011",
            "d003_f1_feasibility_coverage",
            "Valid D003-v1 F1 feasibility coverage",
            "Gate 5 scenario generation",
            "Methods: scenario coverage",
            "development_and_calibration_diagnostic",
            "data/processed/simulator/scenarios/post_d003_f1_audit.csv",
            "All 35,000 F1 rows pass strict audit; 6,436 candidates are feasible and 4,215 of 7,000 decision sets have no feasible numerical reference.",
            "Development/calibration coverage diagnostic only; calibration groups are marked and cannot support model fitting or selection.",
            draw_f1_feasibility,
        ),
        FigureSpec(
            "RFIG-012",
            "d003_f1_generation_runtime",
            "D003-v1 F1 generation runtime",
            "computational methodology",
            "Methods: compute",
            "reference_hardware_observation",
            "data/processed/simulator/scenarios/generation_ledger_v2.csv;data/processed/reporting/gate5_f1_campaign_runtime.csv",
            "The 13-group four-worker F1 scale-up consumed 63,639.442 seconds of summed group work in 18,148.400 seconds of wall time, for effective concurrency 3.51 on the reference laptop.",
            "Reference-hardware scheduling evidence only; G01 was a separate serial checkpoint and runtime does not measure model or mission performance.",
            draw_f1_runtime,
        ),
        FigureSpec(
            "RFIG-014",
            "gate4_literature_discovery_refresh",
            "Post-acceptance Gate 4 literature discovery refresh",
            "Gate 4 literature update",
            "Methods: evidence coverage",
            "post_acceptance_discovery_update",
            "literature/search_log.csv;literature/screening_log.csv;literature/extraction_matrix.csv",
            "The post-acceptance refresh records 4,218 unique discovery rows: 3,288 title/abstract exclusions, 926 pending full-text screens, and four provisional includes; the 23 accepted extracted records remain unchanged.",
            "Discovery-flow evidence only; the refresh is incomplete and did not alter the accepted Gate 4 model, threshold, split, or evidence claims.",
            draw_literature_refresh_flow,
        ),
        FigureSpec(
            "RFIG-015",
            "d003_g01_three_fidelity_checkpoint",
            "Valid D003-v1 G01 F0/F1/F2 checkpoint",
            "Gate 5 scenario generation",
            "Methods: fidelity and compute",
            "repair_validation_development",
            "data/processed/simulator/scenarios/post_d003_f0_audit.csv;data/processed/simulator/scenarios/post_d003_f1_g01_audit.csv;data/processed/simulator/scenarios/post_d003_f2_g01_audit.csv;data/processed/simulator/scenarios/generation_ledger_v2.csv;data/processed/reporting/gate5_f2_campaign_runtime.csv",
            "F0, F1, and F2 G01 all pass strict audit with 80% feasible candidates and a feasible numerical reference in every nominal-U0 decision set; F2 G01 required 450.835 seconds for 250 rows.",
            "Nominal-U0 development qualification only; row counts and force-model workloads differ, and the timing values do not measure model or mission performance.",
            draw_g01_three_fidelity_checkpoint,
        ),
        FigureSpec(
            "RFIG-016",
            "d003_f2_feasibility_coverage",
            "Valid D003-v1 F2 feasibility coverage",
            "Gate 5 scenario generation",
            "Methods: scenario coverage",
            "development_and_calibration_diagnostic",
            "data/processed/simulator/scenarios/post_d003_f2_audit.csv",
            "All 3,500 F2 rows pass strict audit; 642 candidates are feasible and 423 of 700 decision sets have no feasible numerical reference.",
            "Development/calibration coverage diagnostic only; calibration groups are marked and cannot support model fitting or selection.",
            draw_f2_feasibility,
        ),
        FigureSpec(
            "RFIG-017",
            "d003_f2_generation_runtime",
            "D003-v1 F2 generation runtime",
            "computational methodology",
            "Methods: compute",
            "reference_hardware_observation",
            "data/processed/simulator/scenarios/generation_ledger_v2.csv;data/processed/reporting/gate5_f2_campaign_runtime.csv",
            "The 13-group two-worker F2 scale-up consumed 15,604.130 seconds of summed group work in 7,978.900 seconds of wall time, for effective concurrency 1.96 on the reference laptop.",
            "Reference-hardware scheduling evidence only; G01 was a separate serial checkpoint and runtime does not measure model or mission performance.",
            draw_f2_runtime,
        ),
        FigureSpec(
            "RFIG-018",
            "d003_full_scenario_campaign_summary",
            "D003-v1 full unlocked scenario campaign audit summary",
            "Gate 5 scenario generation",
            "Methods: generator qualification",
            "development_and_calibration_diagnostic",
            "data/processed/simulator/scenarios/post_d003_f0_audit.csv;data/processed/simulator/scenarios/post_d003_f1_audit.csv;data/processed/simulator/scenarios/post_d003_f2_audit.csv;data/processed/simulator/scenarios/generation_ledger_v2.csv",
            "All 45,500 unlocked F0/F1/F2 rows pass strict audit; 9,417 candidates are feasible and 4,957 of 9,100 decision sets have no feasible numerical reference.",
            "Exact fidelity-level diagnostic table only; different force-model workloads are not a speed benchmark and no value is model-performance evidence.",
            draw_f0_f1_f2_summary,
        ),
        FigureSpec(
            "RFIG-019",
            "gate5_literature_hardening_controls",
            "Gate 5 literature-hardening controls",
            "Gate 5 pre-fit hardening",
            "Methods: model benchmark",
            "pre_fit_literature_hardening",
            "data/processed/reporting/gate5_literature_hardening_matrix.csv",
            "Primary and official literature was translated into pre-fit Gate 5 controls: ranking guards, required diagnostics, matched interpretation controls, deferred QRL topics, and excluded non-primary claims.",
            "Process-control evidence only; this figure adds no model family, split, threshold, final-test access, or model-performance claim.",
            draw_gate5_literature_hardening,
        ),
        FigureSpec(
            "RFIG-020",
            "gate5_grouped_cv_fold_allocation",
            "Gate 5 grouped cross-validation fold allocation",
            "Gate 5 runner freeze",
            "Methods: model benchmark",
            "pre_fit_runner_freeze",
            "data/processed/reporting/gate5_cv_fold_manifest.csv",
            "All 39,000 development rows are assigned by whole frozen groups to one of five validation folds; each fold retains F0, F1, and F2 coverage.",
            "Outcome-blind methods evidence only; unequal two- and three-group fold sizes motivate pooled out-of-fold primary scoring and separate fold diagnostics.",
            draw_gate5_cv_folds,
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
