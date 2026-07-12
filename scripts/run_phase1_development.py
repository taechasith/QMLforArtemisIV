"""Prepare, audit, and execute the fail-closed Gate 5 development workflow."""

from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

from openqfuel.gate5 import (
    execute_trial,
    gate5_preflight,
    initial_execution_plan,
    write_csv_rows,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("preflight", help="Audit data and locks without fitting")
    prepare = subparsers.add_parser(
        "prepare-contract",
        help="Write the label-agnostic CV assignment and preflight evidence",
    )
    prepare.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data/processed/reporting",
    )
    execute = subparsers.add_parser(
        "execute-trial", help="Run one accepted, resumable development CV task"
    )
    execute.add_argument("trial_id")
    execute.add_argument("--rung-samples", type=int)
    execute.add_argument("--matched-qubits", type=int)
    execute.add_argument(
        "--view", choices=("primary", "compressed_c05"), default="primary"
    )
    execute.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command in {"preflight", "prepare-contract"}:
        audit, folds = gate5_preflight(ROOT)
        if args.command == "prepare-contract":
            args.output_dir.mkdir(parents=True, exist_ok=True)
            write_csv_rows(args.output_dir / "gate5_cv_fold_manifest.csv", folds)
            write_csv_rows(
                args.output_dir / "gate5_initial_execution_plan.csv",
                initial_execution_plan(ROOT),
            )
            path = args.output_dir / "gate5_preflight_audit.json"
            path.write_text(
                json.dumps(audit, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(audit, indent=2, sort_keys=True))
        return

    try:
        summary = execute_trial(
            ROOT,
            args.trial_id,
            args.output_dir,
            rung_samples=args.rung_samples,
            matched_qubits=args.matched_qubits,
            view=args.view,
        )
    except Exception as error:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        failure = {
            "status": "failed",
            "trial_id": args.trial_id,
            "view": args.view,
            "rung_samples": args.rung_samples,
            "matched_qubits": args.matched_qubits,
            "exception_type": type(error).__name__,
            "exception_message": str(error),
            "traceback": traceback.format_exc(),
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
        }
        (args.output_dir / "failure.json").write_text(
            json.dumps(failure, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        raise
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
