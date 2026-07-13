"""Generate RFIG-038 for D019-C safety-objective redesign discussion."""

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
RESULT = ROOT / "data/processed/reporting/post_gate5_d019_safety_redesign.json"
MATRIX = ROOT / "data/processed/reporting/post_gate5_d019_safety_redesign_matrix.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GOLD = "#E69F00"
RED = "#B24A3B"
GRAY = "#68737D"
PALE_BLUE = "#EAF3F8"
PALE_GOLD = "#FFF4D6"
PALE_RED = "#FBEDEA"
PALE_GRAY = "#F2F4F6"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d019-safety-redesign-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d019_safety_redesign_boundary.png"
    svg = OUTPUT / "post_gate5_d019_safety_redesign_boundary.svg"
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
        x + 0.02,
        y + h - 0.035,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        x + 0.02,
        y + h - 0.090,
        body,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.4,
        color=INK,
        linespacing=1.25,
    )


def _draw(payload: dict) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(13.2, 7.4))
    ax.set_axis_off()
    ax.text(
        0.02,
        0.97,
        "D019-C safety-objective redesign discussion",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=17,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.02,
        0.90,
        "D017-C showed that lower Brier can still be unsafe when recall is near zero; D019 opens only a future protocol discussion.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        color=GRAY,
    )

    _card(
        ax,
        0.05,
        0.58,
        0.39,
        0.24,
        "Frozen D017 selector",
        f"Model: {payload['active_frozen_selection_model']}\n"
        f"Mean Brier: {payload['active_frozen_selection_mean_brier']:.4f}\n"
        f"Mean recall: {payload['active_frozen_selection_mean_recall']:.4f}\n\n"
        "Decision: failed safety utility.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.56,
        0.58,
        0.39,
        0.24,
        "Future-only signal",
        f"Model: {payload['future_only_signal_model']}\n"
        f"Mean Brier: {payload['future_only_signal_mean_brier']:.4f}\n"
        f"Mean recall: {payload['future_only_signal_mean_recall']:.4f}\n\n"
        "Use: design a future recall-first objective.",
        GOLD,
        PALE_GOLD,
    )
    ax.annotate(
        "",
        xy=(0.50, 0.43),
        xytext=(0.50, 0.54),
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.2},
    )
    _card(
        ax,
        0.18,
        0.01,
        0.64,
        0.17,
        "Prohibited by this decision",
        "No implementation, refit, rerank, threshold change, or locked-data access.\nNo mission-loop work, QML invention, quantum advantage, or Gate 6.",
        GRAY,
        PALE_GRAY,
    )
    _card(
        ax,
        0.22,
        0.22,
        0.56,
        0.18,
        "D019-C boundary",
        "DISCUSSION_ONLY. A later executable protocol must prospectively freeze\nrecall or false-negative cost, thresholds, controls, compute admission,\nand stop rules.",
        BLUE,
        PALE_BLUE,
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
            "figure_id": "RFIG-038",
            "title": "D019-C safety-objective redesign boundary",
            "phase": "Post-Gate-5 safety redesign discussion",
            "paper_section": "Discussion: future safety objective",
            "evidence_status": "future_only_safety_objective_discussion",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{MATRIX.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d019_safety_redesign_figure.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D019-C converts the D018-C CSAFE failure into a future-only recall-first safety-objective discussion without rescuing D017.",
            "claim_boundary": "Future-only discussion; no implementation, fitting, threshold change, calibration, final-test, hardware/GPU, mission, Gate 5 reinterpretation, QML invention, quantum advantage, or Gate 6.",
            "reporting_source_commit": "06e6283d99682615c16465af0254049987113563",
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-038"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    if payload["decision_id"] != "D019-C" or payload["official_status"] != "DISCUSSION_ONLY":
        raise ValueError("RFIG-038 requires completed D019-C discussion evidence")
    png, svg = _draw(payload)
    _register(png, svg)
    print("Generated RFIG-038 D019-C safety-objective redesign boundary")


if __name__ == "__main__":
    main()
