"""Generate the frozen Gate 5 model registry and trigger report."""

from pathlib import Path

from openqfuel.gate5_reporting import write_gate5_report


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    write_gate5_report(
        ROOT,
        ROOT / "experiments",
        ROOT / "data/processed/reporting",
    )
