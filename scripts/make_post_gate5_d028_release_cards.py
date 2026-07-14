"""Generate D028-C release-support card evidence and RFIG-047."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d028_release_support_cards.yaml"
D027 = ROOT / "data/processed/reporting/post_gate5_d027_manuscript_results.json"
RESULT = ROOT / "data/processed/reporting/post_gate5_d028_release_support_cards.json"
CARD_INDEX = ROOT / "data/processed/reporting/post_gate5_d028_release_support_cards.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GREEN = "#1B7F5A"
GOLD = "#E69F00"
RED = "#B24A3B"
GRAY = "#68737D"
PALE_BLUE = "#EAF3F8"
PALE_GREEN = "#E8F4EF"
PALE_GOLD = "#FFF4D6"
PALE_RED = "#FBEDEA"
PALE_GRAY = "#F2F4F6"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d028-release-cards-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _card_rows(config: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "card_id": "model",
            "path": config["cards"]["model_card"],
            "purpose": "Explain evaluated model families and non-release status",
            "release_status": "no trained model released",
            "claim_boundary": "negative benchmark only",
        },
        {
            "card_id": "simulator",
            "path": config["cards"]["simulator_card"],
            "purpose": "Summarize simulator credibility and validation boundaries",
            "release_status": "research simulator evidence only",
            "claim_boundary": "not flight readiness",
        },
        {
            "card_id": "data",
            "path": config["cards"]["data_card"],
            "purpose": "Summarize public-data provenance, splits, and locked-data limits",
            "release_status": "public/reproducible evidence only",
            "claim_boundary": "no final-test or mission-owned data released",
        },
        {
            "card_id": "limitations",
            "path": config["cards"]["limitation_card"],
            "purpose": "State limitations and prohibited interpretations",
            "release_status": "required before release decision",
            "claim_boundary": "no QML advantage, Gate 6, or flight claim",
        },
    ]


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d028_release_support_cards.png"
    svg = OUTPUT / "post_gate5_d028_release_support_cards.svg"
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
            boxstyle="round,pad=0.012,rounding_size=0.014",
            transform=ax.transAxes,
            facecolor=face,
            edgecolor=color,
            linewidth=1.2,
        )
    )
    ax.text(x + 0.018, y + h - 0.035, title, transform=ax.transAxes, ha="left", va="top", fontsize=10.2, fontweight="bold", color=INK)
    ax.text(x + 0.018, y + h - 0.082, body, transform=ax.transAxes, ha="left", va="top", fontsize=8.0, color=INK, linespacing=1.22)


def _draw() -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    ax.set_axis_off()
    ax.text(0.02, 0.97, "D028-C release-support cards", transform=ax.transAxes, ha="left", va="top", fontsize=16, fontweight="bold", color=INK)
    ax.text(0.02, 0.91, "Cards prepare the manuscript/release package without authorizing release, Gate 6, locked data, or mission-loop work.", transform=ax.transAxes, ha="left", va="top", fontsize=9.2, color=GRAY)
    _card(
        ax,
        0.06,
        0.62,
        0.25,
        0.19,
        "Model card",
        "No trained model is released.\nQML evidence is negative.\nC06 remains the strongest\nreported control.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.38,
        0.62,
        0.25,
        0.19,
        "Simulator card",
        "Research credibility only.\nGate 3 validation passed\nwith RTC3 outside claim.\nNot flight readiness.",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.70,
        0.62,
        0.23,
        0.19,
        "Data card",
        "Public-data provenance.\nFrozen splits.\nCalibration/final-test\nremain locked.",
        GREEN,
        PALE_GREEN,
    )
    _card(
        ax,
        0.18,
        0.30,
        0.29,
        0.20,
        "Limitation card",
        "No quantum advantage.\nNo fuel-savings claim.\nNo NASA approval.\nNo Gate 6 authority.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.55,
        0.30,
        0.29,
        0.20,
        "Next release step",
        "Clean reproducibility audit,\nrelease checklist,\nclaim review,\nand human release decision.",
        GRAY,
        PALE_GRAY,
    )
    ax.annotate("", xy=(0.50, 0.52), xytext=(0.50, 0.60), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.2})
    _card(
        ax,
        0.20,
        0.08,
        0.60,
        0.10,
        "Release boundary",
        "D028-C documents what can be released later; it is not itself a release, model release, Gate 6 opening, or operational approval.",
        RED,
        PALE_RED,
    )
    return _save(fig)


def _register(png: Path, svg: Path, source_commit: str) -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_id = {row["figure_id"]: row for row in rows}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-047",
            "title": "D028-C release-support card map",
            "phase": "Release support",
            "paper_section": "Reproducibility and release notes",
            "evidence_status": "release_support_cards_ready",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{CARD_INDEX.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d028_release_cards.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D028-C maps release-support cards required before any release decision.",
            "claim_boundary": "Release documentation only; no release, Gate 6 run, locked-data access, mission-loop execution, model fitting, QML invention, quantum advantage, or Gate 5 reinterpretation.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-047"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D028-C":
        raise ValueError("D028-C config required")
    d027 = json.loads(D027.read_text(encoding="utf-8"))
    if d027["official_status"] != "MANUSCRIPT_RESULTS_DISCUSSION_DRAFT_READY":
        raise ValueError("D028-C requires completed D027-C manuscript draft")
    for field in (
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "mission_loop_runs",
        "gate6_runs",
    ):
        if int(d027[field]) != 0:
            raise PermissionError(f"D027 source violates locked counter {field}")
    rows = _card_rows(config)
    _write_csv(CARD_INDEX, rows)
    result = {
        "decision_id": "D028-C",
        "protocol_id": "P001",
        "official_status": config["outcome"]["official_status"],
        "source_d027_commit": config["source_evidence"]["d027_reporting_commit"],
        "cards": config["cards"],
        "next_recommended_step": config["outcome"]["next_recommended_step"],
        "release_authorized": False,
        "gate6_authorized": False,
        "qml_gate6_candidate": False,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs": 0,
        "gpu_hours": 0,
        "mission_loop_runs": 0,
        "gate6_runs": 0,
        "claim_boundary": config["claim_boundary"],
    }
    _write_json(RESULT, result)
    png, svg = _draw()
    _register(png, svg, config["source_evidence"]["d027_reporting_commit"])
    print("Generated D028-C release-support cards")


if __name__ == "__main__":
    main()
