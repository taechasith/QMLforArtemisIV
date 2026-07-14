"""Generate D026-C manuscript synthesis evidence and RFIG-045."""

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
CONFIG = ROOT / "configs/post_gate5_d026_manuscript_synthesis.yaml"
D025 = ROOT / "data/processed/reporting/post_gate5_d025_gate6_recommendation.json"
RESULT = ROOT / "data/processed/reporting/post_gate5_d026_manuscript_synthesis.json"
MATRIX = ROOT / "data/processed/reporting/post_gate5_d026_manuscript_claim_matrix.csv"
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
        "svg.hashsalt": "qmlforartemisiv-d026-manuscript-synthesis-v1",
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


def _claim_matrix(d025: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "claim_area": "Main result",
            "allowed_wording": "Frozen public-data development benchmark found no QML improvement over strong classical controls.",
            "evidence_basis": f"Q01 NRMSE {d025['q01_mean_nrmse']:.4f} vs C06 {d025['c06_mean_nrmse']:.4f}; zero qualifying regimes",
            "prohibited_wording": "QML improves cislunar propellant efficiency",
            "paper_location": "Abstract, Results, Discussion",
        },
        {
            "claim_area": "Exploratory QML",
            "allowed_wording": "Q01b and FQK are development-only exploratory negatives.",
            "evidence_basis": f"Q01b gap {d025['q01b_relative_gap_vs_c06']:.1f}x; FQK recall {d025['fqk_mean_recall']:.4f}",
            "prohibited_wording": "Projected kernels or FQK are promising mission candidates",
            "paper_location": "Supplementary negative-results appendix",
        },
        {
            "claim_area": "Safety-filter lesson",
            "allowed_wording": "Recall-first CSAFE-RF is a future protocol design lesson.",
            "evidence_basis": f"{d025['recall_first_model']} recall {d025['recall_first_recall']:.4f}; Brier {d025['recall_first_brier']:.4f}",
            "prohibited_wording": "Recall-first audit rescues D017 or opens locked data",
            "paper_location": "Discussion and future work",
        },
        {
            "claim_area": "Gate 6",
            "allowed_wording": "No QML Gate 6 candidate is eligible from P001.",
            "evidence_basis": d025["gate6_recommendation"],
            "prohibited_wording": "Gate 6 mission experiment is authorized",
            "paper_location": "Conclusion and limitations",
        },
        {
            "claim_area": "Operational relevance",
            "allowed_wording": "Results are computational research evidence under public-data limits.",
            "evidence_basis": "Calibration, final-test, mission-loop, hardware, and Gate 6 counters remain zero",
            "prohibited_wording": "Flight readiness, NASA approval, or astronaut-use readiness",
            "paper_location": "Limitations",
        },
    ]


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d026_manuscript_synthesis.png"
    svg = OUTPUT / "post_gate5_d026_manuscript_synthesis.svg"
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
    ax.text(x + 0.018, y + h - 0.084, body, transform=ax.transAxes, ha="left", va="top", fontsize=8.0, color=INK, linespacing=1.22)


def _draw(d025: dict[str, Any]) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.8, 7.1))
    ax.set_axis_off()
    ax.text(0.02, 0.97, "D026-C manuscript synthesis: defensible claims after Gate 5", transform=ax.transAxes, ha="left", va="top", fontsize=16, fontweight="bold", color=INK)
    ax.text(0.02, 0.91, "The paper should emphasize a valid negative QML benchmark, not a mission or quantum-advantage claim.", transform=ax.transAxes, ha="left", va="top", fontsize=9.2, color=GRAY)
    _card(
        ax,
        0.04,
        0.64,
        0.27,
        0.20,
        "Allowed main claim",
        f"QML did not beat C06 under\nthe frozen development benchmark.\n\nQ01 {d025['q01_mean_nrmse']:.4f}\nC06 {d025['c06_mean_nrmse']:.4f}",
        GREEN,
        PALE_GREEN,
    )
    _card(
        ax,
        0.37,
        0.64,
        0.27,
        0.20,
        "Appendix evidence",
        f"Q01b and FQK are exploratory\nnegatives.\n\nQ01b gap {d025['q01b_relative_gap_vs_c06']:.1f}x\nFQK recall {d025['fqk_mean_recall']:.4f}",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.70,
        0.64,
        0.25,
        0.20,
        "Future-work lesson",
        f"Recall-first CSAFE-RF informs\nfuture safety objectives only.\n\nRecall {d025['recall_first_recall']:.4f}\nBrier {d025['recall_first_brier']:.4f}",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.10,
        0.30,
        0.36,
        0.21,
        "Prohibited claims",
        "No quantum advantage.\nNo flight readiness.\nNo NASA approval.\nNo Gate 6 authorization.\nNo Gate 5 rescue.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.54,
        0.30,
        0.36,
        0.21,
        "Next writing task",
        "Draft Results and Discussion around:\nnegative benchmark evidence,\nfailed/stopped branches,\nlimitations, and future protocol design.",
        GRAY,
        PALE_GRAY,
    )
    ax.annotate("", xy=(0.50, 0.53), xytext=(0.50, 0.62), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.2})
    _card(
        ax,
        0.18,
        0.07,
        0.64,
        0.11,
        "Gate 6 wording",
        "No QML Gate 6 candidate is eligible from P001. A later Gate 6 requires a separate baseline/safety protocol and human approval.",
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
            "figure_id": "RFIG-045",
            "title": "D026-C manuscript claim synthesis",
            "phase": "Post-Gate-5 manuscript synthesis",
            "paper_section": "Claims and limitations",
            "evidence_status": "manuscript_claim_synthesis",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{MATRIX.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d026_manuscript_synthesis.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D026-C converts Gate 5 and 5X closure evidence into allowed and prohibited manuscript claims.",
            "claim_boundary": "Manuscript synthesis only; no Gate 6 run, locked-data access, mission-loop execution, model fitting, QML invention, quantum advantage, or Gate 5 reinterpretation.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-045"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D026-C":
        raise ValueError("D026-C config required")
    d025 = json.loads(D025.read_text(encoding="utf-8"))
    if d025["official_status"] != "GATE5_CLOSED_NO_QML_GATE6_CANDIDATE":
        raise ValueError("D026-C requires completed D025-C closure evidence")
    for field in (
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "mission_loop_runs",
        "gate6_runs",
    ):
        if int(d025[field]) != 0:
            raise PermissionError(f"D025 source violates locked counter {field}")
    matrix = _claim_matrix(d025)
    _write_csv(MATRIX, matrix)
    result = {
        "decision_id": "D026-C",
        "protocol_id": "P001",
        "official_status": config["synthesis"]["official_status"],
        "source_d025_commit": config["source_evidence"]["d025_reporting_commit"],
        "allowed_main_claim": config["synthesis"]["allowed_main_claim"],
        "allowed_secondary_claim": config["synthesis"]["allowed_secondary_claim"],
        "prohibited_claims": config["synthesis"]["prohibited_claims"],
        "next_recommended_step": config["synthesis"]["next_recommended_step"],
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
    png, svg = _draw(d025)
    _register(png, svg, config["source_evidence"]["d025_reporting_commit"])
    print("Generated D026-C manuscript synthesis")


if __name__ == "__main__":
    main()
