"""Generate D029-C clean reproducibility audit STOP evidence and RFIG-048."""

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
CONFIG = ROOT / "configs/post_gate5_d029_reproducibility_audit.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d029_reproducibility_audit.json"
MATRIX = ROOT / "data/processed/reporting/post_gate5_d029_reproducibility_audit_matrix.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
GREEN = "#1B7F5A"
GOLD = "#E69F00"
RED = "#B24A3B"
GRAY = "#68737D"
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
        "svg.hashsalt": "qmlforartemisiv-d029-repro-audit-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _matrix(config: dict[str, Any]) -> list[dict[str, str]]:
    rows = [
        {
            "audit_item": "pytest",
            "status": config["audit_commands"]["pytest"]["result"],
            "evidence": config["audit_commands"]["pytest"]["summary"],
            "interpretation": "clean clone is not release-ready",
            "next_action": config["outcome"]["next_recommended_step"],
        },
        {
            "audit_item": "ruff",
            "status": config["audit_commands"]["ruff"]["result"],
            "evidence": config["audit_commands"]["ruff"]["summary"],
            "interpretation": "lint is portable",
            "next_action": "retain as passing check",
        },
        {
            "audit_item": "compileall",
            "status": config["audit_commands"]["compileall"]["result"],
            "evidence": config["audit_commands"]["compileall"]["summary"],
            "interpretation": "Python files compile in clean clone",
            "next_action": "retain as passing check",
        },
    ]
    for failure in config["failures"]:
        rows.append(
            {
                "audit_item": failure["test_id"],
                "status": "failed",
                "evidence": failure["observed"],
                "interpretation": failure["interpretation"],
                "next_action": "future D030-C byte-provenance correction",
            }
        )
    return rows


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d029_reproducibility_audit_stop.png"
    svg = OUTPUT / "post_gate5_d029_reproducibility_audit_stop.svg"
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


def _draw(config: dict[str, Any]) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    ax.set_axis_off()
    ax.text(0.02, 0.97, "D029-C clean reproducibility audit: STOP", transform=ax.transAxes, ha="left", va="top", fontsize=16, fontweight="bold", color=INK)
    ax.text(0.02, 0.91, "The clean clone reached lint and compile checks, but pytest failed on byte-provenance/hash portability.", transform=ax.transAxes, ha="left", va="top", fontsize=9.2, color=GRAY)
    _card(
        ax,
        0.06,
        0.62,
        0.25,
        0.19,
        "Pytest",
        config["audit_commands"]["pytest"]["summary"] + "\n\nRelease readiness: STOP.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.38,
        0.62,
        0.25,
        0.19,
        "Ruff",
        "All checks passed.\n\nLint is not the blocker.",
        GREEN,
        PALE_GREEN,
    )
    _card(
        ax,
        0.70,
        0.62,
        0.23,
        0.19,
        "Compile",
        "compileall passed.\n\nPython syntax is not\nthe blocker.",
        GREEN,
        PALE_GREEN,
    )
    _card(
        ax,
        0.13,
        0.29,
        0.35,
        0.21,
        "Root cause class",
        "Frozen CSV and generator hashes\nare not portable under the clean\nclone byte state.\n\nGate 5 preflight failed closed.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.56,
        0.29,
        0.32,
        0.21,
        "Next correction",
        "D030-C should freeze line-ending\nand byte-provenance behavior,\nthen rerun the clean audit.",
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
        "This STOP is release infrastructure evidence only; it does not change model results or authorize release, correction, locked data, or Gate 6.",
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
            "figure_id": "RFIG-048",
            "title": "D029-C clean reproducibility audit STOP",
            "phase": "Release reproducibility audit",
            "paper_section": "Reproducibility and release notes",
            "evidence_status": "clean_reproducibility_audit_stop",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{MATRIX.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d029_reproducibility_audit.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D029-C records a clean clone reproducibility STOP caused by byte-provenance/hash portability failures.",
            "claim_boundary": "Release audit failure only; no release, correction, Gate 6 run, locked-data access, mission-loop execution, model fitting, QML invention, quantum advantage, or Gate 5 reinterpretation.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-048"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D029-C":
        raise ValueError("D029-C config required")
    rows = _matrix(config)
    _write_csv(MATRIX, rows)
    result = {
        "decision_id": "D029-C",
        "protocol_id": "P001",
        "official_status": config["outcome"]["official_status"],
        "source_d028_commit": config["source_evidence"]["d028_commit"],
        "release_ready": False,
        "release_authorized": False,
        "correction_authorized": False,
        "gate6_authorized": False,
        "pytest_result": config["audit_commands"]["pytest"]["summary"],
        "ruff_result": config["audit_commands"]["ruff"]["summary"],
        "compileall_result": config["audit_commands"]["compileall"]["summary"],
        "failure_count": len(config["failures"]),
        "next_recommended_step": config["outcome"]["next_recommended_step"],
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs": 0,
        "gpu_hours": 0,
        "mission_loop_runs": 0,
        "gate6_runs": 0,
        "claim_boundary": config["claim_boundary"],
    }
    _write_json(RESULT, result)
    png, svg = _draw(config)
    _register(png, svg, config["source_evidence"]["d028_commit"])
    print("Generated D029-C clean reproducibility audit STOP")


if __name__ == "__main__":
    main()
