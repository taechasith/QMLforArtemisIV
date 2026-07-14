"""Generate D032-C release-candidate manifest evidence and RFIG-051."""

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
CONFIG = ROOT / "configs/post_gate5_d032_release_candidate_manifest.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d032_release_candidate_manifest.json"
FILES = ROOT / "data/processed/reporting/post_gate5_d032_release_candidate_files.csv"
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
        "svg.hashsalt": "qmlforartemisiv-d032-release-candidate-manifest-v1",
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


def _manifest_rows(config: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for relative in config["manifest_files"]:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        rows.append(
            {
                "path": relative,
                "sha256": _sha256(path),
                "bytes": str(path.stat().st_size),
                "release_role": "candidate_manifest_member",
            }
        )
    return rows


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d032_release_candidate_manifest_ready.png"
    svg = OUTPUT / "post_gate5_d032_release_candidate_manifest_ready.svg"
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


def _draw(config: dict[str, Any], rows: list[dict[str, str]]) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    ax.set_axis_off()
    ax.text(
        0.02,
        0.97,
        "D032-C release-candidate manifest: READY",
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
        "The release candidate is packaged for decision, but no release action is authorized.",
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
        "Candidate base",
        config["candidate"]["candidate_base_commit"][:12]
        + "\nD031 claim-reviewed package.\n\nVersion candidate: "
        + config["candidate"]["package_version_candidate"],
        GREEN,
        PALE_GREEN,
    )
    _card(
        ax,
        0.38,
        0.62,
        0.25,
        0.19,
        "Manifest",
        f"{len(rows)} files hashed.\nREADME, protocol,\nmanuscript, release cards,\nand figure registry included.",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.70,
        0.62,
        0.23,
        0.19,
        "Still locked",
        "No tag.\nNo archive or DOI.\nNo CITATION update.\nNo Gate 6.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.13,
        0.28,
        0.35,
        0.22,
        "Release claim",
        "Development-only negative\nQML benchmark.\n\nNo P001 QML Gate-6\ncandidate claim only.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.56,
        0.28,
        0.32,
        0.22,
        "After acceptance",
        "Create tag, archive/DOI,\nand citation metadata only\nafter explicit human release\nacceptance.",
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
        "D032-C is a candidate manifest only; no release, tag, archive, DOI, locked data, Gate 6, or advantage claim.",
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
            "figure_id": "RFIG-051",
            "title": "D032-C release-candidate manifest READY",
            "phase": "Release decision preparation",
            "paper_section": "Reproducibility and release notes",
            "evidence_status": "release_candidate_manifest_ready",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{FILES.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d032_release_candidate_manifest.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D032-C records a release-candidate manifest while keeping all release actions unauthorized.",
            "claim_boundary": "Release-candidate manifest only; no release, tag, archive, DOI, CITATION update, locked-data access, mission-loop run, Gate 6, QML invention claim, or quantum-advantage claim.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-051"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D032-C":
        raise ValueError("D032-C config required")
    d031 = _read_json(ROOT / "data/processed/reporting/post_gate5_d031_claim_release_review.json")
    if d031["official_status"] != "CLAIM_RELEASE_REVIEW_READY":
        raise ValueError("D032-C requires D031-C claim review READY")
    if d031["release_authorized"] is not False:
        raise ValueError("D032-C must not inherit release authorization")
    rows = _manifest_rows(config)
    _write_csv(FILES, rows)
    result = {
        "decision_id": "D032-C",
        "protocol_id": "P001",
        "official_status": "RELEASE_CANDIDATE_MANIFEST_READY",
        "candidate_base_commit": config["candidate"]["candidate_base_commit"],
        "candidate_label": config["candidate"]["candidate_label"],
        "package_version_candidate": config["candidate"]["package_version_candidate"],
        "citation_version_current": config["candidate"]["citation_version_current"],
        "manifest_file_count": len(rows),
        "manifest_total_bytes": sum(int(row["bytes"]) for row in rows),
        "release_ready_for_human_decision": True,
        "release_authorized": False,
        "tag_authorized": False,
        "archive_authorized": False,
        "doi_authorized": False,
        "citation_update_authorized": False,
        "gate6_authorized": False,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs": 0,
        "gpu_hours": 0,
        "mission_loop_runs": 0,
        "gate6_runs": 0,
        "next_human_decision": "Accept release package, request revisions, or reject release.",
        "claim_boundary": config["claim_boundary"],
    }
    _write_json(RESULT, result)
    png, svg = _draw(config, rows)
    _register(png, svg, config["candidate"]["candidate_base_commit"])
    print("Generated D032-C release-candidate manifest READY")


if __name__ == "__main__":
    main()
