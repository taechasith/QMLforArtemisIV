"""Generate D031-C final claim/release review evidence and RFIG-050."""

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
CONFIG = ROOT / "configs/post_gate5_d031_claim_release_review.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d031_claim_release_review.json"
MATRIX = ROOT / "data/processed/reporting/post_gate5_d031_claim_release_review_matrix.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#172026"
GREEN = "#1B7F5A"
BLUE = "#246A8D"
GOLD = "#B7791F"
RED = "#A8483D"
GRAY = "#5E6A71"
PALE_GREEN = "#E8F4EF"
PALE_BLUE = "#E7F0F5"
PALE_GOLD = "#FFF4D8"
PALE_RED = "#F9E7E4"
PALE_GRAY = "#F1F4F5"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d031-claim-release-review-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object in {path}")
    return value


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
    review = config["review"]
    rows = [
        {
            "review_item": "allowed_claim",
            "status": "ready_for_human_decision",
            "evidence": review["allowed_release_candidate_claim"],
            "release_effect": "claim may be used only with development-only labels",
        }
    ]
    for label in review["required_release_labels"]:
        rows.append(
            {
                "review_item": "required_label",
                "status": "required",
                "evidence": label,
                "release_effect": "must remain visible in release/manuscript context",
            }
        )
    for claim in review["prohibited_claims"]:
        rows.append(
            {
                "review_item": "prohibited_claim",
                "status": "prohibited",
                "evidence": claim,
                "release_effect": "must not be stated as a conclusion",
            }
        )
    rows.append(
        {
            "review_item": "human_decision",
            "status": "pending",
            "evidence": review["next_human_decision"],
            "release_effect": "release remains unauthorized until accepted",
        }
    )
    return rows


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d031_claim_release_review_ready.png"
    svg = OUTPUT / "post_gate5_d031_claim_release_review_ready.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines())
        + "\n",
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
        "D031-C final claim/release review: READY",
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
        "The package is reviewed for claim boundaries; release still requires a human decision.",
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
        "Allowed",
        "Negative public-data\nbenchmark.\n\nNo P001 QML Gate-6 claim.",
        GREEN,
        PALE_GREEN,
    )
    _card(
        ax,
        0.38,
        0.62,
        0.25,
        0.19,
        "Required labels",
        "Development-only result.\nCalibration/final-test locked.\nNo mission-loop validation.\nRelease needs acceptance.",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.70,
        0.62,
        0.23,
        0.19,
        "Prohibited",
        "No quantum advantage.\nNo fuel-savings claim.\nNo flight readiness.\nNo NASA approval.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.13,
        0.28,
        0.35,
        0.22,
        "Evidence basis",
        "D026-C claim matrix,\nD027-C manuscript draft,\nD028-C release cards,\nand D030-C clean audit PASS.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.56,
        0.28,
        0.32,
        0.22,
        "Next human decision",
        "Accept release package,\nrequest revisions,\nor reject release.\n\nNo automatic release.",
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
        "No release, tag, archive, Gate 6, locked data, QML invention, or quantum-advantage claim is authorized.",
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
            "figure_id": "RFIG-050",
            "title": "D031-C final claim/release review READY",
            "phase": "Release decision preparation",
            "paper_section": "Claims and limitations",
            "evidence_status": "claim_release_review_ready",
            "source_data": (
                f"{RESULT.relative_to(ROOT).as_posix()};"
                f"{MATRIX.relative_to(ROOT).as_posix()}"
            ),
            "generator": "scripts/make_post_gate5_d031_claim_release_review.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D031-C records final claim/release review readiness while keeping release unauthorized.",
            "claim_boundary": (
                "Release decision preparation only; no release, tag, archive, "
                "Gate 6 authorization, locked-data access, mission-loop run, "
                "QML invention claim, or quantum-advantage claim."
            ),
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-050"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D031-C":
        raise ValueError("D031-C config required")
    d030 = _read_json(ROOT / config["source_evidence"]["d030_reproducibility"])
    if d030["official_status"] != "REPRODUCIBILITY_AUDIT_PASS":
        raise ValueError("D031-C requires D030-C reproducibility PASS")
    if d030["release_authorized"] is not False:
        raise ValueError("D031-C must not inherit release authorization")

    rows = _matrix(config)
    _write_csv(MATRIX, rows)
    result = {
        "decision_id": "D031-C",
        "protocol_id": "P001",
        "official_status": config["review"]["official_status"],
        "release_ready_for_human_decision": True,
        "release_authorized": False,
        "tag_authorized": False,
        "archive_authorized": False,
        "doi_authorized": False,
        "gate6_authorized": False,
        "allowed_release_candidate_claim": config["review"][
            "allowed_release_candidate_claim"
        ],
        "required_label_count": len(config["review"]["required_release_labels"]),
        "prohibited_claim_count": len(config["review"]["prohibited_claims"]),
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs": 0,
        "gpu_hours": 0,
        "mission_loop_runs": 0,
        "gate6_runs": 0,
        "next_human_decision": config["review"]["next_human_decision"],
        "claim_boundary": config["claim_boundary"],
    }
    _write_json(RESULT, result)
    png, svg = _draw(config)
    _register(png, svg, d030["d030_correction_commit"])
    print("Generated D031-C final claim/release review READY")


if __name__ == "__main__":
    main()
