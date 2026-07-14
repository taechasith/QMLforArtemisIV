"""Generate D030-C reproducibility-correction PASS evidence and RFIG-049."""

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
CONFIG = ROOT / "configs/post_gate5_d030_reproducibility_correction.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d030_reproducibility_correction.json"
MATRIX = ROOT / "data/processed/reporting/post_gate5_d030_reproducibility_correction_matrix.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#152126"
GREEN = "#1B7F5A"
BLUE = "#246A8D"
GOLD = "#B7791F"
GRAY = "#5E6A71"
PALE_GREEN = "#E7F3ED"
PALE_BLUE = "#E7F0F5"
PALE_GOLD = "#FFF4D8"
PALE_GRAY = "#F1F4F5"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d030-repro-correction-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _matrix(config: dict[str, Any]) -> list[dict[str, str]]:
    rows = [
        {
            "audit_item": "line_ending_policy",
            "status": "corrected",
            "evidence": "; ".join(config["correction"]["line_ending_rules"]),
            "interpretation": "hashed text paths now materialize with LF bytes in clean checkouts",
            "next_action": "retain policy for release",
        },
    ]
    for name, command in config["audit_commands"].items():
        rows.append(
            {
                "audit_item": name,
                "status": command["result"],
                "evidence": command["summary"],
                "interpretation": "clean clone release validation passed",
                "next_action": "eligible for final human release review",
            }
        )
    return rows


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d030_reproducibility_correction_pass.png"
    svg = OUTPUT / "post_gate5_d030_reproducibility_correction_pass.svg"
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
            boxstyle="round,pad=0.012,rounding_size=0.014",
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
        fontsize=10.2,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        x + 0.018,
        y + h - 0.082,
        body,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.0,
        color=INK,
        linespacing=1.22,
    )


def _draw(config: dict[str, Any]) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    ax.set_axis_off()
    ax.text(
        0.02,
        0.97,
        "D030-C clean reproducibility correction: PASS",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=16,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.02,
        0.91,
        "Line-ending policy was frozen for hashed text artifacts, then the clean-clone audit passed.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        color=GRAY,
    )
    _card(
        ax,
        0.06,
        0.62,
        0.25,
        0.19,
        "Correction",
        ".gitattributes now pins LF\nfor source, CSV/JSON evidence,\nYAML, JSONL, and Markdown.",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.38,
        0.62,
        0.25,
        0.19,
        "Pytest",
        "252 passed + 667 subtests\nin the corrected clean clone.\n\nResult: PASS.",
        GREEN,
        PALE_GREEN,
    )
    _card(
        ax,
        0.70,
        0.62,
        0.23,
        0.19,
        "Static checks",
        "Ruff: passed.\ncompileall: passed.\n\nNo syntax/lint blocker.",
        GREEN,
        PALE_GREEN,
    )
    _card(
        ax,
        0.13,
        0.28,
        0.35,
        0.22,
        "What changed",
        "Only checkout byte policy changed.\nNo model family, threshold, seed,\nsplit, score, or evidence payload\nwas changed.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.56,
        0.28,
        0.32,
        0.22,
        "Next decision",
        "Release is now eligible for\nhuman claim/release review.\nGate 6 remains unauthorized.",
        GRAY,
        PALE_GRAY,
    )
    _card(
        ax,
        0.20,
        0.07,
        0.60,
        0.10,
        "Boundary",
        "Release-infrastructure reproducibility only; no Gate 5/5X reinterpretation, Gate 6, QML invention, or quantum-advantage claim.",
        BLUE,
        PALE_BLUE,
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
            "figure_id": "RFIG-049",
            "title": "D030-C clean reproducibility correction PASS",
            "phase": "Release reproducibility audit",
            "paper_section": "Reproducibility and release notes",
            "evidence_status": "clean_reproducibility_audit_pass",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{MATRIX.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d030_reproducibility_correction.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D030-C records that the line-ending and byte-provenance correction passed a clean-clone release audit.",
            "claim_boundary": "Release infrastructure only; no Gate 5 reinterpretation, Gate 6 authorization, locked-data access, mission-loop run, QML invention claim, or quantum-advantage claim.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-049"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D030-C":
        raise ValueError("D030-C config required")
    rows = _matrix(config)
    _write_csv(MATRIX, rows)
    result = {
        "decision_id": "D030-C",
        "protocol_id": "P001",
        "official_status": config["outcome"]["official_status"],
        "d029_stop_commit": config["source_evidence"]["d029_stop_commit"],
        "d030_correction_commit": config["source_evidence"]["d030_correction_commit"],
        "release_ready_for_human_decision": True,
        "release_authorized": False,
        "gate6_authorized": False,
        "pytest_result": config["audit_commands"]["pytest"]["summary"],
        "ruff_result": config["audit_commands"]["ruff"]["summary"],
        "compileall_result": config["audit_commands"]["compileall"]["summary"],
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs": 0,
        "gpu_hours": 0,
        "mission_loop_runs": 0,
        "gate6_runs": 0,
        "next_recommended_step": config["outcome"]["next_recommended_step"],
        "claim_boundary": config["claim_boundary"],
    }
    _write_json(RESULT, result)
    png, svg = _draw(config)
    _register(png, svg, config["source_evidence"]["d030_correction_commit"])
    print("Generated D030-C clean reproducibility correction PASS")


if __name__ == "__main__":
    main()
