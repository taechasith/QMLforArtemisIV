"""Generate the post-Gate-5 exploratory protocol figure."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
REPORTING = ROOT / "data/processed/reporting"
MATRIX = REPORTING / "post_gate5_exploratory_protocol_matrix.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#1F2937"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
MAGENTA = "#CC79A7"
GRAY = "#5B6573"
PALE = "#E8EDF2"
GOOD_PALE = "#EAF7F1"
WARNING_PALE = "#FFF0E6"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-post-gate5-exploratory-v1",
    }
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save(fig: plt.Figure, path: Path) -> tuple[Path, Path]:
    png = path.with_suffix(".png")
    svg = path.with_suffix(".svg")
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV post-Gate-5 figure generator"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={
            "Creator": "QMLforArtemisIV post-Gate-5 figure generator",
            "Date": None,
        },
    )
    plt.close(fig)
    normalized = "\n".join(
        line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()
    )
    svg.write_text(normalized + "\n", encoding="utf-8", newline="\n")
    return png, svg


def _card(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str,
    *,
    facecolor: str,
    edgecolor: str,
    linestyle: str = "-",
) -> tuple[float, float]:
    patch = patches.FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        transform=ax.transAxes,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.1,
        linestyle=linestyle,
    )
    ax.add_patch(patch)
    ax.text(
        x + 0.018,
        y + height - 0.04,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        x + 0.018,
        y + height - 0.09,
        body,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.0,
        color=INK,
        linespacing=1.25,
    )
    return x + width / 2, y + height / 2


def _arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(
        patches.FancyArrowPatch(
            start,
            end,
            transform=ax.transAxes,
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=1.0,
            color=GRAY,
            connectionstyle="arc3,rad=0.0",
        )
    )


def draw_protocol(path: Path) -> tuple[Path, Path]:
    rows = read_csv(MATRIX)
    near_term = [row for row in rows if row["near_term_status"] == "near_term_qml_test"]
    future = [row for row in rows if row["near_term_status"] == "appendix_future_only"]
    fig, ax = plt.subplots(figsize=(10.8, 5.7), constrained_layout=True)
    ax.set_axis_off()
    ax.text(
        0.0,
        0.98,
        "Post-Gate-5 exploratory protocol boundary",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.0,
        0.925,
        "Opened 2026-07-13; development-only planning. No calibration, final-test, Gate 6, or Gate 5 reinterpretation is authorized.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color=GRAY,
    )

    gate5 = _card(
        ax,
        0.02,
        0.64,
        0.23,
        0.18,
        "Accepted Gate 5 result",
        "Technical FAIL\nQ01 lost to C06\nQ02/Q03 stopped at\nfrozen eligibility gate",
        facecolor=WARNING_PALE,
        edgecolor=ORANGE,
    )
    protocol = _card(
        ax,
        0.38,
        0.64,
        0.25,
        0.18,
        "New exploratory protocol",
        "Prospective branch\nOriginal rows, folds,\nmetrics, locks, and\nclaim discipline retained",
        facecolor="white",
        edgecolor=INK,
    )
    locked = _card(
        ax,
        0.73,
        0.64,
        0.23,
        0.18,
        "Locked boundaries",
        "No refit or rerank\nNo final-test read\nNo Gate 6 run\nNo advantage claim",
        facecolor=PALE,
        edgecolor=GRAY,
    )
    _arrow(ax, (gate5[0] + 0.12, gate5[1]), (protocol[0] - 0.14, protocol[1]))
    _arrow(ax, (protocol[0] + 0.14, protocol[1]), (locked[0] - 0.13, locked[1]))

    x_positions = [0.06, 0.38]
    for x, row in zip(x_positions, near_term):
        body = (
            "Projected quantum kernel\nCost NRMSE + regret\nDevelopment split only"
            if row["track_id"] == "Q01b"
            else "Feasibility kernel classifier\nAUROC/Brier/recall\nDevelopment split only"
        )
        _card(
            ax,
            x,
            0.30,
            0.25,
            0.23,
            row["track_id"],
            body,
            facecolor=GOOD_PALE,
            edgecolor=GREEN if row["track_id"] == "Q01b" else BLUE,
        )
        _arrow(ax, (protocol[0] - 0.02, protocol[1] - 0.10), (x + 0.125, 0.53))

    future_names = ", ".join(row["track_id"] for row in future)
    _card(
        ax,
        0.70,
        0.30,
        0.26,
        0.23,
        "Appendix / future only",
        f"{future_names}\nSeparate protocol required\nbefore any run",
        facecolor="#F6EEF5",
        edgecolor=MAGENTA,
        linestyle="--",
    )
    _arrow(ax, (locked[0], locked[1] - 0.10), (0.83, 0.53))

    ax.text(
        0.0,
        0.08,
        "Source: post_gate5_exploratory_protocol_matrix.csv. Diagram records scope only; it is not model-performance evidence.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8,
        color=GRAY,
    )
    return save(fig, path)


def register(png: Path, svg: Path) -> None:
    existing = read_csv(REGISTRY)
    fields = list(existing[0])
    by_id = {row["figure_id"]: row for row in existing}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-024",
            "title": "Post-Gate-5 exploratory protocol boundary",
            "phase": "Post-Gate-5 exploratory protocol",
            "paper_section": "Methods: exploratory protocol",
            "evidence_status": "post_gate5_exploratory_protocol",
            "source_data": str(MATRIX.relative_to(ROOT)).replace("\\", "/"),
            "generator": "scripts/make_post_gate5_exploratory_figures.py",
            "png_path": str(png.relative_to(ROOT)).replace("\\", "/"),
            "png_sha256": sha256_file(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"),
            "svg_sha256": sha256_file(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "The post-Gate-5 branch opens only Q01b projected quantum kernel and a feasibility-only quantum-kernel classifier as near-term exploratory QML tests.",
            "claim_boundary": "Protocol-boundary evidence only; no model result, calibration/final-test access, Gate 6 authorization, or quantum-advantage claim.",
        }
    )
    by_id[row["figure_id"]] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    temporary = REGISTRY.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    temporary.replace(REGISTRY)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png, svg = draw_protocol(OUTPUT / "post_gate5_exploratory_protocol_boundary")
    register(png, svg)
    print("Generated RFIG-024 post-Gate-5 exploratory protocol figure")


if __name__ == "__main__":
    main()
