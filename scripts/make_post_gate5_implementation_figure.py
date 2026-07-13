"""Generate the D008 exploratory implementation-freeze figure."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_exploratory.yaml"
MANIFEST = (
    ROOT / "data/processed/reporting/post_gate5_exploratory_trial_manifest.csv"
)
DISCUSSION = (
    ROOT / "data/processed/reporting/post_gate5_future_research_discussion.csv"
)
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#1F2937"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
MAGENTA = "#CC79A7"
GRAY = "#5B6573"
PALE_BLUE = "#EAF3F8"
PALE_GREEN = "#EAF7F1"
PALE_ORANGE = "#FFF0E6"
PALE_MAGENTA = "#F7EDF4"
PALE_GRAY = "#F2F4F6"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d008-implementation-freeze-v1",
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
) -> None:
    ax.add_patch(
        patches.FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.010,rounding_size=0.014",
            transform=ax.transAxes,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.15,
            linestyle=linestyle,
        )
    )
    ax.text(
        x + 0.014,
        y + height - 0.026,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        x + 0.014,
        y + height - 0.070,
        body,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.7,
        color=INK,
        linespacing=1.23,
    )


def _arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = GRAY,
) -> None:
    ax.add_patch(
        patches.FancyArrowPatch(
            start,
            end,
            transform=ax.transAxes,
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.05,
            color=color,
            connectionstyle="arc3,rad=0.0",
        )
    )


def save(fig: plt.Figure, path: Path) -> tuple[Path, Path]:
    png = path.with_suffix(".png")
    svg = path.with_suffix(".svg")
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV D008 figure generator"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={"Creator": "QMLforArtemisIV D008 figure generator", "Date": None},
    )
    plt.close(fig)
    normalized = "\n".join(
        line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()
    )
    svg.write_text(normalized + "\n", encoding="utf-8", newline="\n")
    return png, svg


def draw(path: Path) -> tuple[Path, Path]:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    trials = read_csv(MANIFEST)
    if config["status"] != (
        "accepted_implementation_freeze_implementation_and_synthetic_validation_authorized"
    ):
        raise ValueError("RFIG-025 may only describe the accepted D008 freeze")
    if len(trials) != 30 or {row["execution_status"] for row in trials} != {
        "frozen_not_run"
    }:
        raise ValueError("RFIG-025 requires 30 unexecuted paired projections")

    fig, ax = plt.subplots(figsize=(11.8, 6.4), constrained_layout=True)
    ax.set_axis_off()
    ax.text(
        0.0,
        0.985,
        "D008 exploratory implementation freeze",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.0,
        0.942,
        "Accepted for implementation and synthetic validation; zero research fits and all locked data boundaries retained",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color=GRAY,
    )

    _card(
        ax,
        0.01,
        0.69,
        0.18,
        0.16,
        "Development inputs",
        "5 grouped folds\nFold-local preprocessing\nIdentical rows per rung\nCalibration/final locked",
        facecolor=PALE_GRAY,
        edgecolor=GRAY,
    )
    _card(
        ax,
        0.24,
        0.66,
        0.25,
        0.22,
        "Shared projected kernel",
        "30 paired projection IDs\n4/6/8 qubits; 1/2 layers\nPauli X/Y/Z -> one-qubit RDMs\nMedian-distance bandwidth\n256 Nyström landmarks",
        facecolor=PALE_BLUE,
        edgecolor=BLUE,
    )
    _arrow(ax, (0.19, 0.77), (0.24, 0.77))

    _card(
        ax,
        0.56,
        0.72,
        0.19,
        0.16,
        "Q01b cost track",
        "Primary: NRMSE\nTie: constrained regret\nC06 + matched controls",
        facecolor=PALE_GREEN,
        edgecolor=GREEN,
    )
    _card(
        ax,
        0.56,
        0.51,
        0.19,
        0.16,
        "FQK feasibility track",
        "Primary: Brier score\nRecall/AUROC/precision\nFrozen classifier controls",
        facecolor=PALE_ORANGE,
        edgecolor=ORANGE,
    )
    _arrow(ax, (0.49, 0.78), (0.56, 0.80), color=GREEN)
    _arrow(ax, (0.49, 0.73), (0.56, 0.59), color=ORANGE)

    _card(
        ax,
        0.81,
        0.61,
        0.18,
        0.20,
        "Frozen staging",
        "Rungs: 128 -> 1,024\nRetain: 30 -> 4\nSelected: 20 seeds\nShot/noise: report-only\nNo rerank from sensitivity",
        facecolor="white",
        edgecolor=INK,
    )
    _arrow(ax, (0.75, 0.80), (0.81, 0.74), color=GREEN)
    _arrow(ax, (0.75, 0.59), (0.81, 0.68), color=ORANGE)

    ax.add_patch(
        patches.FancyBboxPatch(
            (0.02, 0.16),
            0.96,
            0.23,
            boxstyle="round,pad=0.012,rounding_size=0.014",
            transform=ax.transAxes,
            facecolor=PALE_MAGENTA,
            edgecolor=MAGENTA,
            linewidth=1.2,
        )
    )
    ax.text(
        0.04,
        0.355,
        "Failure and future-research firewall",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        fontweight="bold",
        color=INK,
    )
    _card(
        ax,
        0.05,
        0.205,
        0.22,
        0.105,
        "1. Observe",
        "Failure, stop, undefined metric,\nnonadvancement, or negative result",
        facecolor="white",
        edgecolor=MAGENTA,
    )
    _card(
        ax,
        0.39,
        0.205,
        0.22,
        0.105,
        "2. Commit record",
        "Evidence + bounded interpretation +\nfuture improvement hypothesis",
        facecolor="white",
        edgecolor=MAGENTA,
    )
    _card(
        ax,
        0.73,
        0.205,
        0.22,
        0.105,
        "3. Keep outside pipeline",
        "No retry or active change;\nnew prospective protocol required",
        facecolor="white",
        edgecolor=MAGENTA,
    )
    _arrow(ax, (0.27, 0.257), (0.39, 0.257), color=MAGENTA)
    _arrow(ax, (0.61, 0.257), (0.73, 0.257), color=MAGENTA)

    ax.text(
        0.0,
        0.065,
        "Source: configs/post_gate5_exploratory.yaml and the 30-row paired trial manifest. RFIG-025 records preregistered methods only, not performance evidence.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7.8,
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
            "figure_id": "RFIG-025",
            "title": "D008 exploratory implementation freeze",
            "phase": "Post-Gate-5 exploratory protocol",
            "paper_section": "Methods: exploratory implementation freeze",
            "evidence_status": "pre_execution_implementation_freeze_accepted",
            "source_data": ";".join(
                [
                    str(CONFIG.relative_to(ROOT)).replace("\\", "/"),
                    str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
                    str(DISCUSSION.relative_to(ROOT)).replace("\\", "/"),
                ]
            ),
            "generator": "scripts/make_post_gate5_implementation_figure.py",
            "png_path": str(png.relative_to(ROOT)).replace("\\", "/"),
            "png_sha256": sha256_file(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"),
            "svg_sha256": sha256_file(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "Accepted D008 freezes a shared 30-projection design for Q01b cost regression and FQK feasibility classification, with grouped development folds, matched controls, bounded staging, and a mandatory future-research firewall for every failure or stop.",
            "claim_boundary": "Accepted pre-execution methods record only; no research fit, result, calibration/final-test read, Gate 5 reinterpretation, Gate 6 authorization, hardware run, or quantum-advantage claim.",
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
    png, svg = draw(OUTPUT / "post_gate5_implementation_freeze")
    register(png, svg)
    print("Generated RFIG-025 D008 implementation-freeze figure")


if __name__ == "__main__":
    main()
