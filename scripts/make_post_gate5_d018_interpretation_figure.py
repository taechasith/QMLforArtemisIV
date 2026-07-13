"""Generate RFIG-037 for D018-C development-only interpretation."""

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
RESULT = ROOT / "data/processed/reporting/post_gate5_d018_interpretation.json"
MATRIX = ROOT / "data/processed/reporting/post_gate5_d018_interpretation_matrix.csv"
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

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d018-interpretation-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d018_interpretation_boundary.png"
    svg = OUTPUT / "post_gate5_d018_interpretation_boundary.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return png, svg


def _card(ax: plt.Axes, x: float, y: float, w: float, h: float, title: str, body: str, color: str, face: str) -> None:
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
    ax.text(x + 0.02, y + h - 0.035, title, transform=ax.transAxes, ha="left", va="top", fontsize=11, fontweight="bold", color=INK)
    ax.text(x + 0.02, y + h - 0.090, body, transform=ax.transAxes, ha="left", va="top", fontsize=8.3, color=INK, linespacing=1.25)


def _draw(payload: dict) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.5, 6.8))
    ax.set_axis_off()
    ax.text(0.02, 0.97, "D018-C interpretation: development evidence does not advance", transform=ax.transAxes, ha="left", va="top", fontsize=17, fontweight="bold", color=INK)
    ax.text(0.02, 0.90, "No calibration, final-test, hardware, mission-loop, QML-invention, quantum-advantage, or Gate 6 authority follows from D017-C.", transform=ax.transAxes, ha="left", va="top", fontsize=9.5, color=GRAY)
    _card(
        ax,
        0.04,
        0.55,
        0.27,
        0.24,
        "CRES",
        f"Best model: {payload['cres_best_model']}\nMean residual NRMSE: {payload['cres_best_mean_nrmse']:.4f}\n\nInterpretation: useful baseline only,\nnot a qualifying result.",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.37,
        0.55,
        0.27,
        0.24,
        "CSAFE",
        f"Best Brier: {payload['csafe_best_brier_mean_brier']:.4f}\nMean recall: {payload['csafe_best_brier_mean_recall']:.4f}\n\nInterpretation: fails safety utility\nunder frozen selection.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.70,
        0.55,
        0.25,
        0.24,
        "Future-only signal",
        "Logistic head had much higher recall\nbut worse Brier.\n\nUse only for a future recall-first\nprotocol, not D017 rescue.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.21,
        0.17,
        0.58,
        0.18,
        "Official D018-C decision",
        "NO_ADVANCE. D017 remains development-only evidence. D019, if opened, must be a future-only redesign discussion with no locked-data or mission authority.",
        GRAY,
        "#F2F4F6",
    )
    ax.annotate("", xy=(0.50, 0.36), xytext=(0.50, 0.52), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.2})
    return _save(fig)


def _register(png: Path, svg: Path) -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_id = {row["figure_id"]: row for row in rows}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-037",
            "title": "D018-C development-only interpretation boundary",
            "phase": "Post-Gate-5 classical-first interpretation",
            "paper_section": "Discussion: development interpretation",
            "evidence_status": "development_only_interpretation_no_advance",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{MATRIX.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d018_interpretation_figure.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D018-C separates usable development signals from non-advancing evidence after D017-C.",
            "claim_boundary": "Development-only interpretation; no calibration, final-test, hardware/GPU, mission, QML invention, quantum advantage, Gate 5 reinterpretation, or Gate 6.",
            "reporting_source_commit": "a173b9308ac1073120475a1a13a1b79c5c5063dd",
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-037"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    if payload["decision_id"] != "D018-C" or payload["official_status"] != "NO_ADVANCE":
        raise ValueError("RFIG-037 requires completed D018-C NO_ADVANCE evidence")
    png, svg = _draw(payload)
    _register(png, svg)
    print("Generated RFIG-037 D018-C interpretation boundary")


if __name__ == "__main__":
    main()
