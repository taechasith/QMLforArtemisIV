"""Generate RFIG-034 and RFIG-035 for D017-C development-only results."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
REPORTING = ROOT / "data/processed/reporting/post_gate5_d017_classical_first"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GREEN = "#009E73"
GOLD = "#E69F00"
LIGHT = "#D9E1E8"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d017-figures-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _summary() -> dict[str, Any]:
    payload = json.loads((REPORTING / "campaign_summary.json").read_text(encoding="utf-8"))
    if payload["decision_id"] != "D017-C" or payload["status"] != "complete":
        raise ValueError("D017 figures require complete D017-C evidence")
    for field in ("calibration_rows_read", "final_test_rows_read", "hardware_jobs_submitted", "gate6_runs"):
        if int(payload[field]) != 0:
            raise PermissionError(f"D017 figure source violates {field}")
    return payload


def _save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / f"{stem}.png"
    svg = OUTPUT / f"{stem}.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight", metadata={"Software": "QMLforArtemisIV D017 figure generator"})
    fig.savefig(svg, bbox_inches="tight", metadata={"Creator": "QMLforArtemisIV D017 figure generator", "Date": None})
    plt.close(fig)
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return png, svg


def _bar(
    rows: Sequence[dict[str, str]],
    *,
    metric: str,
    title: str,
    ylabel: str,
    stem: str,
    color: str,
) -> tuple[Path, Path]:
    ordered = sorted(rows, key=lambda row: float(row[metric]))
    labels = [row["model_id"].replace("_", "\n") for row in ordered]
    values = [float(row[metric]) for row in ordered]
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.bar(labels, values, color=color, edgecolor=INK, linewidth=0.6)
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", color=INK)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=LIGHT, linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    for index, value in enumerate(values):
        ax.text(index, value, f"{value:.4g}", ha="center", va="bottom", fontsize=8)
    return _save(fig, stem)


def _register(figures: dict[str, tuple[Path, Path]], summary: dict[str, Any]) -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_id = {row["figure_id"]: row for row in rows}
    specs = {
        "RFIG-034": {
            "title": "D017-C CRES development residual-cost results",
            "paper_section": "Results: classical-first residual cost",
            "evidence_status": "development_only_classical_first_residual_cost",
            "source_data": "data/processed/reporting/post_gate5_d017_classical_first/cres_summary.csv;data/processed/reporting/post_gate5_d017_classical_first/campaign_summary.json",
            "png_svg": figures["RFIG-034"],
            "caption": "D017-C compares CRES residual-cost controls over the original grouped development split.",
        },
        "RFIG-035": {
            "title": "D017-C CSAFE development safety-filter results",
            "paper_section": "Results: classical-first safety filter",
            "evidence_status": "development_only_classical_first_safety_filter",
            "source_data": "data/processed/reporting/post_gate5_d017_classical_first/csafe_summary.csv;data/processed/reporting/post_gate5_d017_classical_first/campaign_summary.json",
            "png_svg": figures["RFIG-035"],
            "caption": "D017-C compares CSAFE safety-filter controls over the original grouped development split.",
        },
    }
    for figure_id, spec in specs.items():
        png, svg = spec["png_svg"]
        row = {field: "" for field in fields}
        row.update(
            {
                "figure_id": figure_id,
                "title": spec["title"],
                "phase": "Post-Gate-5 classical-first development",
                "paper_section": spec["paper_section"],
                "evidence_status": spec["evidence_status"],
                "source_data": spec["source_data"],
                "generator": "scripts/make_post_gate5_d017_figures.py",
                "png_path": png.relative_to(ROOT).as_posix(),
                "png_sha256": _sha256(png),
                "png_bytes": str(png.stat().st_size),
                "svg_path": svg.relative_to(ROOT).as_posix(),
                "svg_sha256": _sha256(svg),
                "svg_bytes": str(svg.stat().st_size),
                "caption": spec["caption"],
                "claim_boundary": (
                    "Development-only classical-first evidence; no calibration, final-test, "
                    "hardware/GPU, Gate 5 reinterpretation, QML invention claim, "
                    "quantum-advantage claim, mission, or Gate 6."
                ),
                "reporting_source_commit": summary["source_commit"],
                "figure_generator_sha256": _sha256(Path(__file__)),
            }
        )
        by_id[figure_id] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    temporary = REGISTRY.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    temporary.replace(REGISTRY)


def main() -> None:
    summary = _summary()
    cres = _rows(REPORTING / "cres_summary.csv")
    csafe = _rows(REPORTING / "csafe_summary.csv")
    figures = {
        "RFIG-034": _bar(
            cres,
            metric="mean_nrmse",
            title="D017-C residual-cost development NRMSE",
            ylabel="Mean fold-seed residual NRMSE",
            stem="post_gate5_d017_cres_residual_cost",
            color=BLUE,
        ),
        "RFIG-035": _bar(
            csafe,
            metric="mean_brier",
            title="D017-C safety-filter development Brier score",
            ylabel="Mean fold-seed Brier score",
            stem="post_gate5_d017_csafe_safety_filter",
            color=GREEN,
        ),
    }
    _register(figures, summary)
    print("Generated RFIG-034 and RFIG-035 D017-C development figures")


if __name__ == "__main__":
    main()
