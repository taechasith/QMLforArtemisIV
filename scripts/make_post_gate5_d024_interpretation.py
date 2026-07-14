"""Generate D024-C recall-first interpretation evidence and RFIG-043."""

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
CONFIG = ROOT / "configs/post_gate5_d024_recall_first_interpretation.yaml"
D023_RESULT = ROOT / "data/processed/reporting/post_gate5_d023_recall_first_development.json"
D023_SCORES = ROOT / "data/processed/reporting/post_gate5_d023_recall_first_development_scores.csv"
RESULT = ROOT / "data/processed/reporting/post_gate5_d024_recall_first_interpretation.json"
MATRIX = ROOT / "data/processed/reporting/post_gate5_d024_recall_first_interpretation_matrix.csv"
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
        "svg.hashsalt": "qmlforartemisiv-d024-interpretation-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _interpretation_matrix(d023: dict[str, Any], scores: list[dict[str, str]]) -> list[dict[str, str]]:
    qml = next(row for row in scores if row["model_id"] == "a02_exact_rbf_feasibility")
    tree = next(row for row in scores if row["model_id"] == "class_weighted_tree")
    selected = next(row for row in scores if row["selected"] == "true")
    return [
        {
            "finding": "Recall recovery signal",
            "evidence": f"{selected['model_id']} mean recall {float(selected['mean_recall']):.4f}",
            "interpretation": "Useful future safety-objective signal",
            "pipeline_effect": "Can inform a new prospective protocol only",
        },
        {
            "finding": "Calibration tradeoff",
            "evidence": (
                f"{selected['model_id']} Brier {float(selected['mean_brier']):.4f}; "
                f"{tree['model_id']} Brier {float(tree['mean_brier']):.4f}"
            ),
            "interpretation": "Recall-first improves missed-case behavior but does not solve probability quality",
            "pipeline_effect": "Future protocol must freeze calibration or false-negative-cost constraints",
        },
        {
            "finding": "QML contribution",
            "evidence": (
                f"{qml['model_id']} recall {float(qml['mean_recall']):.4f}; "
                f"Brier {float(qml['mean_brier']):.4f}"
            ),
            "interpretation": "QML-style exact-RBF feasibility remains non-advancing",
            "pipeline_effect": "Keep QML evidence in appendix/future-work discussion",
        },
        {
            "finding": "Authority boundary",
            "evidence": (
                f"fits {d023['new_model_fits']}; thresholds "
                f"{d023['threshold_applications_to_real_data']}; locked reads 0"
            ),
            "interpretation": "D023/D024 are reporting-only after D017",
            "pipeline_effect": "No calibration, final-test, mission-loop, or Gate 6 authority",
        },
    ]


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d024_recall_first_interpretation.png"
    svg = OUTPUT / "post_gate5_d024_recall_first_interpretation.svg"
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
    ax.text(x + 0.018, y + h - 0.035, title, transform=ax.transAxes, ha="left", va="top", fontsize=10.5, fontweight="bold", color=INK)
    ax.text(x + 0.018, y + h - 0.086, body, transform=ax.transAxes, ha="left", va="top", fontsize=8.2, color=INK, linespacing=1.25)


def _draw(result: dict[str, Any]) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.4, 6.8))
    ax.set_axis_off()
    ax.text(0.02, 0.97, "D024-C interpretation: recall-first signal stays future-only", transform=ax.transAxes, ha="left", va="top", fontsize=16, fontweight="bold", color=INK)
    ax.text(0.02, 0.91, "D023-C is useful for scientific design, but remains post-D017-informed development evidence with no locked-data or Gate 6 authority.", transform=ax.transAxes, ha="left", va="top", fontsize=9.2, color=GRAY)
    _card(
        ax,
        0.04,
        0.59,
        0.27,
        0.22,
        "What improved",
        f"Recall-first selected\n{result['selected_model_id']}.\n\nMean recall: {result['selected_mean_recall']:.4f}\nFNR: {result['selected_mean_false_negative_rate']:.4f}",
        GREEN,
        PALE_GREEN,
    )
    _card(
        ax,
        0.37,
        0.59,
        0.27,
        0.22,
        "What did not improve",
        f"Brier remains worse than the\nbest-Brier tree.\n\nSelected Brier: {result['selected_mean_brier']:.4f}\nScientific issue: calibration.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.70,
        0.59,
        0.25,
        0.22,
        "QML status",
        "A02 exact-RBF feasibility did\nnot dominate the logistic head.\n\nKeep QML in appendix and\nfuture-work discussion.",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.08,
        0.23,
        0.38,
        0.20,
        "Protocol effect",
        "No refit, rerank, retry, threshold application,\ncalibration/final-test read, mission-loop work,\nGate 5 reinterpretation, or Gate 6 follows.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.54,
        0.23,
        0.38,
        0.20,
        "Next valid use",
        "Close this branch into manuscript discussion.\nA future cycle may freeze recall, calibration,\nand false-negative-cost rules prospectively.",
        GRAY,
        PALE_GRAY,
    )
    ax.annotate("", xy=(0.50, 0.46), xytext=(0.50, 0.57), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.2})
    return _save(fig)


def _register(png: Path, svg: Path, source_commit: str) -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_id = {row["figure_id"]: row for row in rows}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-043",
            "title": "D024-C recall-first interpretation boundary",
            "phase": "Post-Gate-5 CSAFE-RF interpretation",
            "paper_section": "Discussion: future safety objective",
            "evidence_status": "recall_first_interpretation_no_advance",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{MATRIX.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d024_interpretation.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D024-C interprets the D023-C recall-first audit as future-useful but non-advancing evidence.",
            "claim_boundary": "Interpretation only; no new experiment, refit, threshold application, locked-data access, mission-loop work, Gate 5 reinterpretation, QML invention, quantum advantage, or Gate 6.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-043"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D024-C":
        raise ValueError("D024-C config required")
    d023 = json.loads(D023_RESULT.read_text(encoding="utf-8"))
    if d023["decision_id"] != "D023-C" or d023["official_status"] != "DEVELOPMENT_AUDIT_COMPLETE":
        raise ValueError("D024-C requires completed D023-C evidence")
    for field in (
        "new_model_fits",
        "threshold_applications_to_real_data",
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs",
        "gpu_hours",
        "gate6_runs",
    ):
        if float(d023[field]) != 0:
            raise PermissionError(f"D023 source violates locked counter {field}")
    scores = _read_csv(D023_SCORES)
    matrix = _interpretation_matrix(d023, scores)
    _write_csv(MATRIX, matrix)
    result = {
        "decision_id": "D024-C",
        "protocol_id": "P001",
        "official_status": config["interpretation"]["official_status"],
        "source_d023_commit": config["source_evidence"]["d023_reporting_commit"],
        "selected_model_id": d023["selected_model_id"],
        "selected_mean_recall": d023["selected_mean_recall"],
        "selected_mean_false_negative_rate": d023["selected_mean_false_negative_rate"],
        "selected_mean_brier": d023["selected_mean_brier"],
        "core_result": config["interpretation"]["core_result"],
        "primary_scientific_lesson": config["interpretation"]["primary_scientific_lesson"],
        "qml_lesson": config["interpretation"]["qml_lesson"],
        "next_recommended_step": config["interpretation"]["next_recommended_step"],
        "new_model_fits": 0,
        "threshold_applications_to_real_data": 0,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs": 0,
        "gpu_hours": 0,
        "gate6_runs": 0,
        "claim_boundary": config["claim_boundary"],
    }
    _write_json(RESULT, result)
    png, svg = _draw(result)
    _register(png, svg, config["source_evidence"]["d023_reporting_commit"])
    print("Generated D024-C recall-first interpretation")


if __name__ == "__main__":
    main()
