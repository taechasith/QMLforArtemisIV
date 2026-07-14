"""Generate D025-C Gate 5 closure and Gate 6 recommendation evidence."""

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
CONFIG = ROOT / "configs/post_gate5_d025_gate6_recommendation.yaml"
GATE5_MODELS = ROOT / "data/processed/reporting/gate5_model_summary.csv"
GATE5_REGIMES = ROOT / "data/processed/reporting/gate5_regime_trigger.csv"
EXPLORATORY = ROOT / "data/processed/reporting/post_gate5_p001/exploratory_decision.json"
D024 = ROOT / "data/processed/reporting/post_gate5_d024_recall_first_interpretation.json"
RESULT = ROOT / "data/processed/reporting/post_gate5_d025_gate6_recommendation.json"
MATRIX = ROOT / "data/processed/reporting/post_gate5_d025_gate6_recommendation_matrix.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GOLD = "#E69F00"
RED = "#B24A3B"
GREEN = "#1B7F5A"
GRAY = "#68737D"
PALE_BLUE = "#EAF3F8"
PALE_GOLD = "#FFF4D6"
PALE_RED = "#FBEDEA"
PALE_GREEN = "#E8F4EF"
PALE_GRAY = "#F2F4F6"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d025-gate6-recommendation-v1",
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


def _model(rows: list[dict[str, str]], family_id: str) -> dict[str, str]:
    return next(row for row in rows if row["family_id"] == family_id)


def _bool(value: str) -> bool:
    return value.lower() == "true"


def _build_matrix(models: list[dict[str, str]], exploratory: dict[str, Any], d024: dict[str, Any]) -> list[dict[str, str]]:
    c06 = _model(models, "C06")
    q01 = _model(models, "Q01")
    q01b = exploratory["tracks"]["Q01b"]
    fqk = exploratory["tracks"]["FQK"]
    return [
        {
            "evidence_block": "Preregistered Gate 5",
            "observed_result": f"Q01 NRMSE {float(q01['mean_pooled_oof_nrmse']):.4f} vs C06 {float(c06['mean_pooled_oof_nrmse']):.4f}",
            "gate6_effect": "No QML mission candidate",
            "recommended_action": "Report technical FAIL; do not rescue Q01/Q02/Q03",
        },
        {
            "evidence_block": "Post-Gate-5 Q01b",
            "observed_result": f"Q01b NRMSE {q01b['mean_pooled_oof_nrmse']:.4f} vs C06 {q01b['c06_mean_pooled_oof_nrmse']:.4f}",
            "gate6_effect": "Exploratory negative",
            "recommended_action": "Keep projected-kernel result in appendix/future work",
        },
        {
            "evidence_block": "Post-Gate-5 FQK",
            "observed_result": f"FQK AUROC {fqk['mean_auroc']:.4f}, recall {fqk['mean_recall_at_0_5']:.4f}",
            "gate6_effect": "Exploratory negative",
            "recommended_action": "Do not promote feasibility kernel to mission safety filter",
        },
        {
            "evidence_block": "CSAFE-RF recall-first",
            "observed_result": f"{d024['selected_model_id']} recall {d024['selected_mean_recall']:.4f}, Brier {d024['selected_mean_brier']:.4f}",
            "gate6_effect": "Future-useful but non-advancing",
            "recommended_action": "Use only to design a future prospective safety protocol",
        },
        {
            "evidence_block": "Gate 6 recommendation",
            "observed_result": "No advancing QML candidate and no locked-data authority",
            "gate6_effect": "Do not open QML Gate 6 from P001",
            "recommended_action": "If opened later, use a separately accepted baseline/safety mission protocol",
        },
    ]


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d025_gate6_recommendation.png"
    svg = OUTPUT / "post_gate5_d025_gate6_recommendation.svg"
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


def _draw(result: dict[str, Any]) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.6, 7.0))
    ax.set_axis_off()
    ax.text(0.02, 0.97, "D025-C Gate 5 closure: no QML candidate for Gate 6", transform=ax.transAxes, ha="left", va="top", fontsize=16, fontweight="bold", color=INK)
    ax.text(0.02, 0.91, "All Gate 5 and post-Gate-5 evidence is development-only or reporting-only; Gate 6 remains locked.", transform=ax.transAxes, ha="left", va="top", fontsize=9.2, color=GRAY)
    _card(
        ax,
        0.04,
        0.62,
        0.27,
        0.20,
        "Gate 5 trigger",
        f"Q01 NRMSE {result['q01_mean_nrmse']:.4f}\nC06 NRMSE {result['c06_mean_nrmse']:.4f}\n\nOfficial outcome: FAIL.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.37,
        0.62,
        0.27,
        0.20,
        "Exploratory QML",
        f"Q01b gap vs C06: {result['q01b_relative_gap_vs_c06']:.1f}x\nFQK recall: {result['fqk_mean_recall']:.4f}\n\nBoth tracks negative.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.70,
        0.62,
        0.25,
        0.20,
        "Recall-first lesson",
        f"{result['recall_first_model']} recall {result['recall_first_recall']:.4f}\nBrier {result['recall_first_brier']:.4f}\n\nFuture design only.",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.12,
        0.25,
        0.33,
        0.21,
        "Gate 6 recommendation",
        "Do not proceed to a QML\nmission experiment from P001.\n\nNo QML model earned locked-data\nor mission-loop authority.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.55,
        0.25,
        0.33,
        0.21,
        "If Gate 6 is opened later",
        "Use a separate human-accepted\nbaseline/safety mission protocol.\n\nNo QML advantage claim; no Gate 5\nreinterpretation.",
        GREEN,
        PALE_GREEN,
    )
    ax.annotate("", xy=(0.50, 0.49), xytext=(0.50, 0.60), xycoords="axes fraction", arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.2})
    _card(
        ax,
        0.20,
        0.05,
        0.60,
        0.10,
        "Manuscript position",
        "Report a valid negative QML benchmark, appendix the exploratory negatives, and use recall-first CSAFE-RF only as future protocol design evidence.",
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
            "figure_id": "RFIG-044",
            "title": "D025-C Gate 5 closure and Gate 6 recommendation",
            "phase": "Post-Gate-5 closure",
            "paper_section": "Discussion: Gate 6 recommendation",
            "evidence_status": "gate5_closure_no_qml_gate6_candidate",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{MATRIX.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d025_gate6_recommendation.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D025-C closes Gate 5 and 5X evidence with no QML candidate eligible for Gate 6.",
            "claim_boundary": "Closure recommendation only; no Gate 6 run, calibration/final-test access, mission-loop execution, model fitting, Gate 5 reinterpretation, QML invention, or quantum advantage.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-044"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D025-C":
        raise ValueError("D025-C config required")
    models = _read_csv(GATE5_MODELS)
    regimes = _read_csv(GATE5_REGIMES)
    exploratory = json.loads(EXPLORATORY.read_text(encoding="utf-8"))
    d024 = json.loads(D024.read_text(encoding="utf-8"))
    c06 = _model(models, "C06")
    q01 = _model(models, "Q01")
    if _bool(q01["all_twenty_seeds_eligible"]) is not True:
        raise ValueError("D025-C expects completed Q01 Gate 5 evidence")
    if exploratory["gate6_authorized"] is not False:
        raise PermissionError("Exploratory evidence cannot authorize Gate 6")
    if d024["official_status"] != "INTERPRETATION_COMPLETE_NO_ADVANCE":
        raise ValueError("D025-C requires completed D024-C interpretation")
    for field in ("calibration_rows_read", "final_test_rows_read"):
        if int(q01[field]) != 0 or int(c06[field]) != 0 or int(exploratory[field]) != 0 or int(d024[field]) != 0:
            raise PermissionError(f"Locked data counter is nonzero for {field}")
    qualified_regimes = sum(1 for row in regimes if row["qualified_residual_regime"].lower() == "true")
    q01b = exploratory["tracks"]["Q01b"]
    fqk = exploratory["tracks"]["FQK"]
    matrix = _build_matrix(models, exploratory, d024)
    _write_csv(MATRIX, matrix)
    result = {
        "decision_id": "D025-C",
        "protocol_id": "P001",
        "official_status": config["recommendation"]["official_status"],
        "gate6_recommendation": config["recommendation"]["gate6_recommendation"],
        "if_human_opens_gate6": config["recommendation"]["if_human_opens_gate6"],
        "manuscript_action": config["recommendation"]["manuscript_action"],
        "q01_mean_nrmse": float(q01["mean_pooled_oof_nrmse"]),
        "c06_mean_nrmse": float(c06["mean_pooled_oof_nrmse"]),
        "gate5_qualified_regimes": qualified_regimes,
        "q01b_mean_nrmse": float(q01b["mean_pooled_oof_nrmse"]),
        "q01b_c06_mean_nrmse": float(q01b["c06_mean_pooled_oof_nrmse"]),
        "q01b_relative_gap_vs_c06": float(q01b["mean_relative_nrmse_gap_vs_c06"]),
        "fqk_mean_auroc": float(fqk["mean_auroc"]),
        "fqk_mean_brier": float(fqk["mean_pooled_oof_brier"]),
        "fqk_mean_recall": float(fqk["mean_recall_at_0_5"]),
        "recall_first_model": d024["selected_model_id"],
        "recall_first_recall": d024["selected_mean_recall"],
        "recall_first_false_negative_rate": d024["selected_mean_false_negative_rate"],
        "recall_first_brier": d024["selected_mean_brier"],
        "gate6_authorized": False,
        "qml_gate6_candidate": False,
        "baseline_gate6_candidate": "requires_separate_human_protocol",
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs": 0,
        "gpu_hours": 0,
        "mission_loop_runs": 0,
        "gate6_runs": 0,
        "claim_boundary": config["claim_boundary"],
    }
    _write_json(RESULT, result)
    png, svg = _draw(result)
    _register(png, svg, config["source_evidence"]["d024_reporting_commit"])
    print("Generated D025-C Gate 5 closure and Gate 6 recommendation")


if __name__ == "__main__":
    main()
