"""Generate RFIG-029 for governed post-Gate-5 failures and stops."""

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
FAILURE = ROOT / "data/processed/reporting/post_gate5_compute_preflight.json"
DISCUSSION = (
    ROOT / "data/processed/reporting/post_gate5_future_research_discussion.csv"
)
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#1F2937"
BLUE = "#0072B2"
ORANGE = "#D55E00"
MAGENTA = "#CC79A7"
GRAY = "#5B6573"
PALE_BLUE = "#EAF3F8"
PALE_ORANGE = "#FFF0E6"
PALE_MAGENTA = "#F7EDF4"
PALE_GRAY = "#F2F4F6"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-rfig029-d009-stop-v1",
    }
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
            boxstyle="round,pad=0.012,rounding_size=0.014",
            transform=ax.transAxes,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.15,
            linestyle=linestyle,
        )
    )
    ax.text(
        x + 0.016,
        y + height - 0.030,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        x + 0.016,
        y + height - 0.078,
        body,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.8,
        color=INK,
        linespacing=1.25,
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
        )
    )


def _save(fig: plt.Figure, path: Path) -> tuple[Path, Path]:
    png = path.with_suffix(".png")
    svg = path.with_suffix(".svg")
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV RFIG-029 generator"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={"Creator": "QMLforArtemisIV RFIG-029 generator", "Date": None},
    )
    plt.close(fig)
    normalized = "\n".join(
        line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()
    )
    svg.write_text(normalized + "\n", encoding="utf-8", newline="\n")
    return png, svg


def draw(path: Path) -> tuple[Path, Path]:
    failure = json.loads(FAILURE.read_text(encoding="utf-8"))
    rows = _read_csv(DISCUSSION)
    if failure["status"] != "STOP" or failure["terminal_status"] != "technical_failure":
        raise ValueError("RFIG-029 requires a governed terminal failure or stop")
    matching = [row for row in rows if row["record_id"] == "P001-FR001"]
    if len(matching) != 1:
        raise ValueError("RFIG-029 requires exactly one P001-FR001 record")
    future = matching[0]
    if (
        future["new_protocol_required"].lower() != "true"
        or future["active_pipeline_change_authorized"].lower() != "false"
        or future["post_outcome_retry_authorized"].lower() != "false"
    ):
        raise ValueError("RFIG-029 future-research firewall is invalid")

    fig, ax = plt.subplots(figsize=(11.8, 6.2), constrained_layout=True)
    ax.set_axis_off()
    ax.text(
        0.0,
        0.985,
        "D009 synthetic compute preflight technical stop",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.0,
        0.940,
        "Clean source commit 7aade60; zero research-row reads; no head, matched-control, or resource-admission result",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color=GRAY,
    )

    _card(
        ax,
        0.02,
        0.65,
        0.25,
        0.19,
        "Authorized synthetic workload",
        "q=8; two layers\n1,024 train + 256 validation\nShared Q01b/FQK projection\nAll matched controls required",
        facecolor=PALE_BLUE,
        edgecolor=BLUE,
    )
    _card(
        ax,
        0.38,
        0.65,
        0.23,
        0.19,
        "Reached",
        "Synthetic arrays created\nShared training projection complete\nNo persisted statevector\nNo locked data read",
        facecolor=PALE_GRAY,
        edgecolor=GRAY,
    )
    _card(
        ax,
        0.72,
        0.65,
        0.26,
        0.19,
        "STOP: telemetry failure",
        "Windows peak-working-set probe\nreturned no valid counters\nHeads and controls not reached\nAdmission unavailable",
        facecolor=PALE_ORANGE,
        edgecolor=ORANGE,
    )
    _arrow(ax, (0.27, 0.745), (0.38, 0.745))
    _arrow(ax, (0.61, 0.745), (0.72, 0.745), color=ORANGE)

    ax.add_patch(
        patches.FancyBboxPatch(
            (0.02, 0.15),
            0.96,
            0.34,
            boxstyle="round,pad=0.012,rounding_size=0.014",
            transform=ax.transAxes,
            facecolor=PALE_MAGENTA,
            edgecolor=MAGENTA,
            linewidth=1.15,
        )
    )
    ax.text(
        0.04,
        0.455,
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
        0.215,
        0.25,
        0.17,
        "Observed evidence",
        "Memory telemetry interface failed.\nNo resource ceiling was tested.\nNo QML outcome exists.",
        facecolor="white",
        edgecolor=MAGENTA,
    )
    _card(
        ax,
        0.375,
        0.215,
        0.25,
        0.17,
        "Future-only improvement",
        "Validate a typed Windows adapter\nagainst an independent OS reading\nbefore a later preflight.",
        facecolor="white",
        edgecolor=MAGENTA,
        linestyle="--",
    )
    _card(
        ax,
        0.70,
        0.215,
        0.25,
        0.17,
        "Still locked",
        "No active correction or retry\nNew prospective decision required\nNo research fit or Gate 6",
        facecolor="white",
        edgecolor=INK,
    )
    _arrow(ax, (0.30, 0.30), (0.375, 0.30), color=MAGENTA)
    _arrow(ax, (0.625, 0.30), (0.70, 0.30), color=MAGENTA)

    ax.text(
        0.0,
        0.055,
        "Source: post_gate5_compute_preflight.json and P001-FR001. Missing admission values are not plotted as zero.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7.8,
        color=GRAY,
    )
    return _save(fig, path)


def register(png: Path, svg: Path) -> None:
    existing = _read_csv(REGISTRY)
    fields = list(existing[0])
    by_id = {row["figure_id"]: row for row in existing}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-029",
            "title": "D009 synthetic compute preflight technical stop",
            "phase": "Post-Gate-5 exploratory protocol",
            "paper_section": "Methods: compute limitations and failed execution",
            "evidence_status": "technical_failure_preflight_stop",
            "source_data": ";".join(
                [
                    str(FAILURE.relative_to(ROOT)).replace("\\", "/"),
                    str(DISCUSSION.relative_to(ROOT)).replace("\\", "/"),
                ]
            ),
            "generator": "scripts/make_post_gate5_failure_figure.py",
            "png_path": str(png.relative_to(ROOT)).replace("\\", "/"),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": (
                "The single D009 preflight attempt stopped after its first shared "
                "synthetic projection because Windows process-memory telemetry failed; "
                "no projected head, matched control, or resource admission was reached."
            ),
            "claim_boundary": (
                "Technical preflight-stop evidence only. P001-FR001 is future research "
                "and cannot alter or retry P001; no QML performance, resource-limit, "
                "research-data, Gate 5, hardware, or Gate 6 claim."
            ),
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
    png, svg = draw(OUTPUT / "post_gate5_d009_technical_stop")
    register(png, svg)
    print("Generated RFIG-029 D009 technical-stop figure")


if __name__ == "__main__":
    main()
