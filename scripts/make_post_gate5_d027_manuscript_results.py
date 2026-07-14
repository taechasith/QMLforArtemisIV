"""Generate D027-C manuscript Results/Discussion tables and RFIG-046."""

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
CONFIG = ROOT / "configs/post_gate5_d027_manuscript_results.yaml"
D025 = ROOT / "data/processed/reporting/post_gate5_d025_gate6_recommendation.json"
D026 = ROOT / "data/processed/reporting/post_gate5_d026_manuscript_synthesis.json"
RESULT = ROOT / "data/processed/reporting/post_gate5_d027_manuscript_results.json"
MAP = ROOT / "data/processed/reporting/post_gate5_d027_manuscript_result_map.csv"
TABLE_DIR = ROOT / "paper/results_tables"
GATE5_TABLE = TABLE_DIR / "gate5_qml_vs_controls.csv"
CLAIM_TABLE = TABLE_DIR / "claim_boundary_table.csv"
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
        "svg.hashsalt": "qmlforartemisiv-d027-manuscript-results-v1",
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


def _gate5_table(d025: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "result_block": "Preregistered Gate 5",
            "candidate": "Q01 quantum kernel",
            "primary_metric": "mean NRMSE",
            "candidate_value": f"{d025['q01_mean_nrmse']:.6f}",
            "control": "C06 physics residual",
            "control_value": f"{d025['c06_mean_nrmse']:.6f}",
            "interpretation": "technical FAIL; zero qualifying regimes",
        },
        {
            "result_block": "Exploratory Q01b",
            "candidate": "Q01b projected quantum kernel",
            "primary_metric": "mean NRMSE",
            "candidate_value": f"{d025['q01b_mean_nrmse']:.6f}",
            "control": "C06 physics residual",
            "control_value": f"{d025['q01b_c06_mean_nrmse']:.6f}",
            "interpretation": "exploratory negative; 95.77x relative gap",
        },
        {
            "result_block": "Exploratory FQK",
            "candidate": "FQK feasibility kernel",
            "primary_metric": "recall at 0.5",
            "candidate_value": f"{d025['fqk_mean_recall']:.6f}",
            "control": "classical feasibility controls",
            "control_value": "stronger than FQK in D011 evidence",
            "interpretation": "exploratory negative; not a safety filter",
        },
        {
            "result_block": "CSAFE-RF lesson",
            "candidate": d025["recall_first_model"],
            "primary_metric": "recall / Brier",
            "candidate_value": f"{d025['recall_first_recall']:.6f} / {d025['recall_first_brier']:.6f}",
            "control": "best-Brier tree and A02 exact-RBF",
            "control_value": "calibration/QML dominance unresolved",
            "interpretation": "future protocol design only",
        },
    ]


def _claim_table(d026: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim_type": "Allowed main claim",
            "manuscript_wording": d026["allowed_main_claim"],
            "evidence_status": "development-only benchmark",
            "boundary": "not final-test, mission, or flight evidence",
        },
        {
            "claim_type": "Allowed secondary claim",
            "manuscript_wording": d026["allowed_secondary_claim"],
            "evidence_status": "future-design lesson",
            "boundary": "not an advancing model result",
        },
        {
            "claim_type": "Prohibited claim",
            "manuscript_wording": "; ".join(d026["prohibited_claims"]),
            "evidence_status": "not supported",
            "boundary": "must not appear as a conclusion",
        },
        {
            "claim_type": "Gate 6 wording",
            "manuscript_wording": "No QML Gate 6 candidate is eligible from P001.",
            "evidence_status": "closure recommendation",
            "boundary": "later Gate 6 requires a separate human-approved protocol",
        },
    ]


def _result_map() -> list[dict[str, str]]:
    return [
        {
            "manuscript_section": "Results",
            "evidence": "Gate 5 Q01 vs C06",
            "reader_takeaway": "The preregistered QML trigger failed.",
            "figure_or_table": "RFIG-021-RFIG-023; gate5_qml_vs_controls.csv",
        },
        {
            "manuscript_section": "Results appendix",
            "evidence": "Q01b and FQK",
            "reader_takeaway": "Near-term QML follow-ups were exploratory negatives.",
            "figure_or_table": "RFIG-026-RFIG-031; gate5_qml_vs_controls.csv",
        },
        {
            "manuscript_section": "Discussion",
            "evidence": "CSAFE-RF recall-first",
            "reader_takeaway": "Safety-objective design should prioritize missed unsafe cases prospectively.",
            "figure_or_table": "RFIG-037-RFIG-043",
        },
        {
            "manuscript_section": "Conclusion",
            "evidence": "D025/D026 closure",
            "reader_takeaway": "No QML Gate 6 candidate is eligible from P001.",
            "figure_or_table": "RFIG-044-RFIG-045; claim_boundary_table.csv",
        },
    ]


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d027_manuscript_results_map.png"
    svg = OUTPUT / "post_gate5_d027_manuscript_results_map.svg"
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
    ax.text(x + 0.018, y + h - 0.035, title, transform=ax.transAxes, ha="left", va="top", fontsize=10.0, fontweight="bold", color=INK)
    ax.text(x + 0.018, y + h - 0.082, body, transform=ax.transAxes, ha="left", va="top", fontsize=7.9, color=INK, linespacing=1.22)


def _draw(d025: dict[str, Any]) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.8, 7.0))
    ax.set_axis_off()
    ax.text(0.02, 0.97, "D027-C manuscript results map", transform=ax.transAxes, ha="left", va="top", fontsize=16, fontweight="bold", color=INK)
    ax.text(0.02, 0.91, "Results and Discussion are drafted from closed evidence only; no new experiment or Gate 6 authority is introduced.", transform=ax.transAxes, ha="left", va="top", fontsize=9.2, color=GRAY)
    _card(
        ax,
        0.05,
        0.64,
        0.25,
        0.19,
        "Results: Gate 5",
        f"Q01 failed against C06.\nQ01 NRMSE {d025['q01_mean_nrmse']:.4f}\nC06 NRMSE {d025['c06_mean_nrmse']:.4f}\nZero qualifying regimes.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.38,
        0.64,
        0.25,
        0.19,
        "Appendix: 5X QML",
        f"Q01b and FQK are negative.\nQ01b gap {d025['q01b_relative_gap_vs_c06']:.1f}x\nFQK recall {d025['fqk_mean_recall']:.4f}",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.71,
        0.64,
        0.22,
        0.19,
        "Discussion",
        f"CSAFE-RF is future design only.\nRecall {d025['recall_first_recall']:.4f}\nBrier {d025['recall_first_brier']:.4f}",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.16,
        0.32,
        0.30,
        0.19,
        "Conclusion",
        "No QML Gate 6 candidate\nis eligible from P001.\nA later Gate 6 needs a\nseparate human protocol.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.56,
        0.32,
        0.30,
        0.19,
        "Next artifacts",
        "Model card, simulator card,\ndata card, limitation appendix,\nand clean reproducibility audit.",
        GREEN,
        PALE_GREEN,
    )
    ax.annotate("", xy=(0.50, 0.53), xytext=(0.50, 0.62), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.2})
    _card(
        ax,
        0.20,
        0.08,
        0.60,
        0.10,
        "Claim control",
        "Every manuscript statement must trace to a registered figure/table and must retain the development-only or future-only evidence label.",
        GRAY,
        PALE_GRAY,
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
            "figure_id": "RFIG-046",
            "title": "D027-C manuscript results map",
            "phase": "Post-Gate-5 manuscript drafting",
            "paper_section": "Results and Discussion",
            "evidence_status": "manuscript_results_discussion_draft",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{MAP.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d027_manuscript_results.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D027-C maps closed Gate 5 and 5X evidence to manuscript Results and Discussion sections.",
            "claim_boundary": "Manuscript drafting only; no Gate 6 run, locked-data access, mission-loop execution, model fitting, QML invention, quantum advantage, or Gate 5 reinterpretation.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-046"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D027-C":
        raise ValueError("D027-C config required")
    d025 = json.loads(D025.read_text(encoding="utf-8"))
    d026 = json.loads(D026.read_text(encoding="utf-8"))
    if d025["official_status"] != "GATE5_CLOSED_NO_QML_GATE6_CANDIDATE":
        raise ValueError("D027-C requires completed D025-C closure")
    if d026["official_status"] != "MANUSCRIPT_SYNTHESIS_READY":
        raise ValueError("D027-C requires completed D026-C synthesis")
    for field in (
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "mission_loop_runs",
        "gate6_runs",
    ):
        if int(d025[field]) != 0 or int(d026[field]) != 0:
            raise PermissionError(f"locked counter is nonzero for {field}")
    _write_csv(GATE5_TABLE, _gate5_table(d025))
    _write_csv(CLAIM_TABLE, _claim_table(d026))
    _write_csv(MAP, _result_map())
    result = {
        "decision_id": "D027-C",
        "protocol_id": "P001",
        "official_status": config["outcome"]["official_status"],
        "source_d026_commit": config["source_evidence"]["d026_reporting_commit"],
        "manuscript_path": config["deliverables"]["manuscript"],
        "gate5_table": config["deliverables"]["gate5_table"],
        "claim_table": config["deliverables"]["claim_table"],
        "synthesis_doc": config["deliverables"]["synthesis_doc"],
        "next_recommended_step": config["outcome"]["next_recommended_step"],
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
    _register(png, svg, config["source_evidence"]["d026_reporting_commit"])
    print("Generated D027-C manuscript Results/Discussion draft")


if __name__ == "__main__":
    main()
