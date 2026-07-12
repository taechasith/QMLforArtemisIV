"""Run or resume Gate 5 after the development-only campaign is accepted."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from openqfuel.gate5 import validate_development_output_path
from openqfuel.gate5_campaign import (
    campaign_lock,
    export_result_tables,
    load_seed_authorization_chain,
    load_tuning_authorization_chain,
    run_campaign_benchmark,
    run_seed_reruns,
    run_tuning_campaign,
    select_finalists,
    verify_campaign_contract,
)
from openqfuel.gate5_reporting import write_gate5_report


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("benchmark", "tune", "seed-reruns", "export", "all")
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/gate5")
    parser.add_argument("--experiment-dir", type=Path, default=ROOT / "experiments")
    parser.add_argument("--classical-workers", type=int, default=4)
    parser.add_argument("--seeds", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    experiment_dir = args.experiment_dir.resolve()
    validate_development_output_path(ROOT, output_dir)
    validate_development_output_path(ROOT, experiment_dir)
    with campaign_lock(output_dir):
        verify_campaign_contract(ROOT)
        if args.command in {"benchmark", "all"}:
            run_campaign_benchmark(
                ROOT,
                output_dir,
                classical_workers=min(args.classical_workers, 2),
            )
        if args.command == "benchmark":
            return
        if args.command in {"tune", "all"}:
            tuning_tasks = run_tuning_campaign(
                ROOT, output_dir, classical_workers=args.classical_workers
            )
        else:
            tuning_tasks = load_tuning_authorization_chain(ROOT, output_dir)

        finalists, tuned_controls = select_finalists(ROOT, output_dir, tuning_tasks)
        if args.command in {"seed-reruns", "all"}:
            seed_tasks = run_seed_reruns(
                ROOT,
                output_dir,
                finalists,
                tuned_controls,
                classical_workers=args.classical_workers,
                seeds=args.seeds,
            )
        else:
            seed_path = output_dir / "authorizations" / "seed_reruns.csv"
            seed_tasks = (
                load_seed_authorization_chain(ROOT, output_dir)
                if seed_path.is_file()
                else []
            )

        if args.command in {"export", "all"}:
            if not seed_tasks:
                raise RuntimeError("Seed rerun authorization is missing")
            export_result_tables(
                ROOT, output_dir, experiment_dir, tuning_tasks, seed_tasks
            )
            write_gate5_report(
                ROOT,
                experiment_dir,
                ROOT / "data/processed/reporting",
            )
            subprocess.check_call(
                [
                    sys.executable,
                    str(ROOT / "scripts/make_gate5_result_figures.py"),
                    "--experiment-dir",
                    str(experiment_dir),
                    "--reporting-dir",
                    str(ROOT / "data/processed/reporting"),
                ],
                cwd=ROOT,
            )


if __name__ == "__main__":
    main()
