"""Generate RFIG-039 for D020-C recall-first safety freeze proposal."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "data/processed/reporting/post_gate5_d020_recall_first_freeze.json"
MATRIX = ROOT / "data/processed/reporting/post_gate5_d020_recall_first_freeze_matrix.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GOLD = "#E69F00"
OLIVE = "#6B8E23"
RED = "#B24A3B"
GRAY = "#68737D"
PALE_BLUE = "#EAF3F8"
PALE_GOLD = "#FFF4D6"
PALE_OLIVE = "#EEF5E4"
PALE_RED = "#FBEDEA"
PALE_GRAY = "#F2F4F6"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d020-recall-first-freeze-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d020_recall_first_freeze_boundary.png"
    svg = OUTPUT / "post_gate5_d020_recall_first_freeze_boundary.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return png, svg


def _card(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    color: str,
    face: str,
) -> None:
    ax.add_patch(
        patches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            transform=ax.transAxes,
            facecolor=face,
            edgecolor=color,
            linewidth=1.2,
        )
    )
    ax.text(
        x + 0.018,
        y + h - 0.035,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10.6,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        x + 0.018,
        y + h - 0.083,
        body,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.15,
        color=INK,
        linespacing=1.22,
    )


def _draw(payload: dict) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(13.4, 7.5))
    ax.set_axis_off()
    ax.text(
        0.02,
        0.97,
        "D020-C recall-first safety freeze proposal",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=17,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.02,
        0.905,
        "Future CSAFE-RF work must treat missed unsafe cases as the primary risk before any new implementation or data fitting.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        color=GRAY,
    )
    _card(
        ax,
        0.04,
        0.59,
        0.26,
        0.23,
        "Triggering lesson",
        "D017 best-Brier safety head\nhad mean recall 0.0139.\n\nBrier alone is not enough\nfor a safety-filter claim.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.37,
        0.59,
        0.26,
        0.23,
        "Frozen future objective",
        "Primary: recall or\nfalse-negative risk.\n\nSecondary: Brier,\ncalibration, precision,\nand false-positive burden.",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.70,
        0.59,
        0.26,
        0.23,
        "Threshold discipline",
        "Choose thresholds only\ninside authorized training folds.\n\nHeld-out D017/D018 outcomes\ncannot tune active thresholds.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.16,
        0.30,
        0.30,
        0.18,
        "Required controls",
        "C02-T02, calibrated logistic,\nclass-weighted tree, A02 exact RBF.\n\nFuture QML requires a separate freeze.",
        OLIVE,
        PALE_OLIVE,
    )
    _card(
        ax,
        0.54,
        0.30,
        0.30,
        0.18,
        "Current authority",
        f"{payload['official_status']}.\nNo implementation or fitting.\nD021 required before synthetic work.",
        GRAY,
        PALE_GRAY,
    )
    ax.annotate(
        "",
        xy=(0.50, 0.50),
        xytext=(0.50, 0.57),
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.2},
    )
    _card(
        ax,
        0.17,
        0.07,
        0.66,
        0.13,
        "Prohibited by D020-C",
        "No implementation, threshold application, development fitting, locked data,\nmission-loop work, Gate 5 reinterpretation, QML invention, quantum advantage, or Gate 6.",
        GRAY,
        PALE_GRAY,
    )
    return _save(fig)


def _register(png: Path, svg: Path) -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_id = {row["figure_id"]: row for row in rows}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-039",
            "title": "D020-C recall-first safety freeze proposal",
            "phase": "Post-Gate-5 safety freeze proposal",
            "paper_section": "Discussion: future safety objective",
            "evidence_status": "recall_first_safety_freeze_proposal",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{MATRIX.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d020_recall_first_freeze_figure.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D020-C freezes a future recall-first safety objective without authorizing implementation, fitting, or locked-data access.",
            "claim_boundary": "Future freeze proposal only; no implementation, threshold application, development fitting, calibration, final-test, hardware/GPU, mission, Gate 5 reinterpretation, QML invention, quantum advantage, or Gate 6.",
            "reporting_source_commit": "cbb57389cbccb9ed78a32403d602c59b6de64c9b",
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-039"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    if payload["decision_id"] != "D020-C" or payload["official_status"] != "FREEZE_PROPOSAL_ONLY":
        raise ValueError("RFIG-039 requires completed D020-C freeze proposal evidence")
    png, svg = _draw(payload)
    _register(png, svg)
    print("Generated RFIG-039 D020-C recall-first safety freeze boundary")


if __name__ == "__main__":
    main()
