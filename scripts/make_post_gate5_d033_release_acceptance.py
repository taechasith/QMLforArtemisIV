"""Generate D033-C release acceptance evidence and RFIG-052."""

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
CONFIG = ROOT / "configs/post_gate5_d033_release_acceptance.yaml"
RESULT = ROOT / "data/processed/reporting/post_gate5_d033_release_acceptance.json"
FILES = ROOT / "data/processed/reporting/post_gate5_d033_release_acceptance_files.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#172026"
BLUE = "#246A8D"
GOLD = "#B7791F"
OLIVE = "#6F7F3A"
RED = "#A8483D"
GRAY = "#5E6A71"
PALE_BLUE = "#E7F0F5"
PALE_GOLD = "#FFF4D8"
PALE_OLIVE = "#EEF3DF"
PALE_RED = "#F9E7E4"
PALE_GRAY = "#F1F4F5"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d033-release-acceptance-v1",
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


def _release_file_rows(config: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for relative in config["release_files"]:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        rows.append(
            {
                "path": relative,
                "sha256": _sha256(path),
                "bytes": str(path.stat().st_size),
                "release_role": "accepted_release_package_member",
            }
        )
    return rows


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d033_release_accepted.png"
    svg = OUTPUT / "post_gate5_d033_release_accepted.svg"
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
    release = config["release"]
    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    ax.set_axis_off()
    ax.text(
        0.02,
        0.97,
        "D033-C release package: ACCEPTED",
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
        "Acceptance authorizes the v0.3.0 tag, source archive, and citation update under the D031-C negative-claim boundary.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        color=GRAY,
    )
    _card(
        ax,
        0.06,
        0.63,
        0.25,
        0.18,
        "Release identity",
        f"Version: {release['release_version']}\nTag: {release['release_tag']}\nAccepted source:\n{release['accepted_prerelease_commit'][:12]}",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.38,
        0.63,
        0.25,
        0.18,
        "Accepted package",
        f"{len(rows)} files hashed.\nCitation, README,\nprotocol, manuscript,\nand release notes included.",
        OLIVE,
        PALE_OLIVE,
    )
    _card(
        ax,
        0.70,
        0.63,
        0.23,
        0.18,
        "Authorized",
        "Release package.\nTag and source archive.\nCITATION metadata.\nNo score changes.",
        GOLD,
        PALE_GOLD,
    )
    _card(
        ax,
        0.10,
        0.31,
        0.38,
        0.22,
        "Allowed claim",
        "Development-only negative\nQML benchmark.\n\nNo tested QML Gate 6\ncandidate from P001.",
        BLUE,
        PALE_BLUE,
    )
    _card(
        ax,
        0.56,
        0.31,
        0.34,
        0.22,
        "Still locked",
        "No DOI minting.\nNo calibration/final reads.\nNo mission loop or Gate 6.\nNo advantage/invention claim.",
        RED,
        PALE_RED,
    )
    _card(
        ax,
        0.18,
        0.05,
        0.64,
        0.17,
        "Strict D031-C boundary",
        "Negative benchmark evidence only.\nNot NASA, flight-ready, final-test, mission-loop,\nadvantage, or proven-invention evidence.",
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
            "figure_id": "RFIG-052",
            "title": "D033-C release package ACCEPTED",
            "phase": "Release acceptance",
            "paper_section": "Reproducibility and release notes",
            "evidence_status": "release_package_accepted",
            "source_data": f"{RESULT.relative_to(ROOT).as_posix()};{FILES.relative_to(ROOT).as_posix()}",
            "generator": "scripts/make_post_gate5_d033_release_acceptance.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D033-C records human acceptance of the release package under the strict D031-C negative-claim boundary.",
            "claim_boundary": "Release package accepted only for the development-only negative QML benchmark; no DOI minting, locked-data access, mission-loop run, Gate 6, QML invention claim, or quantum-advantage claim.",
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-052"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if config["decision_id"] != "D033-C":
        raise ValueError("D033-C config required")
    d032 = _read_json(ROOT / "data/processed/reporting/post_gate5_d032_release_candidate_manifest.json")
    if d032["official_status"] != "RELEASE_CANDIDATE_MANIFEST_READY":
        raise ValueError("D033-C requires D032-C release-candidate manifest READY")
    if d032["release_ready_for_human_decision"] is not True:
        raise ValueError("D032-C did not expose a release decision")
    rows = _release_file_rows(config)
    _write_csv(FILES, rows)
    scope = config["scope"]
    result = {
        "decision_id": "D033-C",
        "protocol_id": "P001",
        "official_status": "RELEASE_PACKAGE_ACCEPTED",
        "human_acceptance": True,
        "accepted_prerelease_commit": config["release"]["accepted_prerelease_commit"],
        "release_version": config["release"]["release_version"],
        "release_tag": config["release"]["release_tag"],
        "citation_previous_version": config["release"]["citation_previous_version"],
        "citation_release_date": config["release"]["citation_release_date"],
        "release_file_count": len(rows),
        "release_total_bytes": sum(int(row["bytes"]) for row in rows),
        "accepted_claim": config["accepted_claim"],
        "release_authorized": scope["release_authorized"],
        "tag_authorized": scope["tag_authorized"],
        "citation_update_authorized": scope["citation_update_authorized"],
        "source_archive_authorized": scope["source_archive_authorized"],
        "doi_minting_authorized": scope["doi_minting_authorized"],
        "model_release_authorized": scope["model_release_authorized"],
        "gate6_authorized": scope["gate6_authorized"],
        "locked_data_access_authorized": scope["locked_data_access_authorized"],
        "mission_loop_authorized": scope["mission_loop_authorized"],
        "model_fitting_authorized": scope["model_fitting_authorized"],
        "qml_invention_claim_authorized": scope["qml_invention_claim_authorized"],
        "quantum_advantage_claim_authorized": scope["quantum_advantage_claim_authorized"],
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs": 0,
        "gpu_hours": 0,
        "mission_loop_runs": 0,
        "gate6_runs": 0,
        "claim_boundary": config["claim_boundary"],
    }
    _write_json(RESULT, result)
    png, svg = _draw(config, rows)
    _register(png, svg, config["release"]["accepted_prerelease_commit"])
    print("Generated D033-C release package ACCEPTED")


if __name__ == "__main__":
    main()
