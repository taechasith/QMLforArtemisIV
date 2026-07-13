"""Validate and export compact D011 development-only reporting evidence."""

from __future__ import annotations

import json
from pathlib import Path

from openqfuel.post_gate5_reporting import write_d011_report


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    result = write_d011_report(ROOT)
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_commit": result["source_commit"],
                "track_decisions": result["track_decisions"],
                "future_discussion_records_added": result[
                    "future_discussion_records_added"
                ],
                "calibration_rows_read": result["calibration_rows_read"],
                "final_test_rows_read": result["final_test_rows_read"],
            },
            indent=2,
            sort_keys=True,
        )
    )
