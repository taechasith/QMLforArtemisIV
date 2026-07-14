"""Generate RFIG-040 for D021-C recall-first synthetic validation."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "data/processed/reporting/post_gate5_d021_recall_first_synthetic.json"
SCORES = ROOT / "data/processed/reporting/post_gate5_d021_recall_first_synthetic_scores.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GOLD = "#E69F00"
RED = "#B24A3B"
GRAY = "#68737D"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d021-synthetic-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d021_recall_first_synthetic_validation.png"
    svg = OUTPUT / "post_gate5_d021_recall_first_synthetic_validation.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return png, svg


def _read_scores() -> list[dict[str, str]]:
    with SCORES.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _draw(payload: dict, rows: list[dict[str, str]]) -> tuple[Path, Path]:
    labels = [
        row["model_id"].replace("synthetic_", "").replace("_", "\n")
        for row in rows
    ]
    recall = np.asarray([float(row["recall"]) for row in rows])
    fnr = np.asarray([float(row["false_negative_rate"]) for row in rows])
    brier = np.asarray([float(row["brier"]) for row in rows])
    x = np.arange(len(rows))
    width = 0.23
    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    fig.subplots_adjust(top=0.78, bottom=0.20)
    fig.text(
        0.08,
        0.95,
        "D021-C CSAFE-RF synthetic recall-first validation",
        ha="left",
        va="top",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.08,
        0.90,
        "Synthetic arrays only; lower Brier does not override lower recall under the D020-C freeze.",
        ha="left",
        va="top",
        color=GRAY,
        fontsize=9.5,
    )
    ax.bar(x - width, recall, width, label="Recall", color=BLUE)
    ax.bar(x, fnr, width, label="False-negative rate", color=RED)
    ax.bar(x + width, brier, width, label="Brier score", color=GOLD)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Synthetic held-out metric")
    selected_index = next(index for index, row in enumerate(rows) if row["selected"] == "true")
    ax.annotate(
        f"Selected: {payload['selected_model_id'].replace('synthetic_', '')}",
        xy=(selected_index - width, recall[selected_index]),
        xytext=(selected_index - 0.36, 0.92),
        arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.1},
        ha="left",
        va="bottom",
        color=INK,
        fontsize=9,
    )
    for bars in ax.containers:
        ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
    ax.legend(loc="upper right", frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D8DEE3", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.text(
        0.0,
        -0.24,
        "Counters: development rows = 0, calibration rows = 0, final-test rows = 0, hardware/GPU/Gate 6 = 0.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        color=GRAY,
        fontsize=8.5,
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
            "figure_id": "RFIG-040",
            "title": "D021-C recall-first synthetic validation",
            "phase": "Post-Gate-5 CSAFE-RF synthetic validation",
            "paper_section": "Discussion: future safety objective",
            "evidence_status": "recall_first_synthetic_validation_pass",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{SCORES.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d021_synthetic_figure.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D021-C validates CSAFE-RF recall-first candidate scoring on synthetic arrays only.",
            "claim_boundary": "Synthetic validation only; no threshold application to real data, development fitting, calibration, final-test, hardware/GPU, mission, Gate 5 reinterpretation, QML invention, quantum advantage, or Gate 6.",
            "reporting_source_commit": "fc0c31c49279b117f93122c9018df78574e6c035",
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-040"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    if payload["decision_id"] != "D021-C" or payload["official_status"] != "SYNTHETIC_VALIDATION_PASS":
        raise ValueError("RFIG-040 requires completed D021-C synthetic PASS evidence")
    png, svg = _draw(payload, _read_scores())
    _register(png, svg)
    print("Generated RFIG-040 D021-C synthetic validation figure")


if __name__ == "__main__":
    main()
