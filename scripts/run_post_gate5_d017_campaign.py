"""Run the D017-C development-only CRES/CSAFE campaign."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from openqfuel.post_gate5_classical_campaign import run_d017_campaign  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    result = run_d017_campaign(ROOT)
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_commit": result["source_commit"],
                "development_rows_read": result["development_rows_read"],
                "calibration_rows_read": result["calibration_rows_read"],
                "final_test_rows_read": result["final_test_rows_read"],
                "cres_best_mean_nrmse_model": result["cres_best_mean_nrmse_model"],
                "csafe_best_mean_brier_model": result["csafe_best_mean_brier_model"],
            },
            indent=2,
            sort_keys=True,
        )
    )
