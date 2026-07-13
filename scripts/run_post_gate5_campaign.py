"""Run or resume the single source-bound D011 development campaign."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from openqfuel.post_gate5_campaign import run_d011_campaign  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    result = run_d011_campaign(ROOT)
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_commit": result["source_commit"],
                "selected_projection_ids": result["tuning"]["selected_projection_ids"],
                "terminal_nonadvancement": result["tuning"]["terminal_nonadvancement"],
                "calibration_rows_read": result["calibration_rows_read"],
                "final_test_rows_read": result["final_test_rows_read"],
            },
            indent=2,
            sort_keys=True,
        )
    )
