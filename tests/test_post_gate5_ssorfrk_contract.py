"""Contract tests for D049 stage-separated gain selection."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_post_gate5_d049_ssorfrk import _select_second_stage_gain


def test_second_stage_gain_selection_uses_fixed_shared_gain() -> None:
    selected, losses = _select_second_stage_gain(np.asarray([0.25, 0.25]), np.asarray([1.0, 1.0]), np.asarray([1.0, 1.0]), 0.10, (0.05, 0.10, 0.15, 0.20))
    assert selected == 0.15
    assert len(losses) == 4


def test_second_stage_gain_selection_ties_to_smallest_value() -> None:
    values = np.asarray([1.0, -1.0])
    selected, _ = _select_second_stage_gain(values, np.zeros(2), np.zeros(2), 0.10, (0.05, 0.10, 0.15, 0.20))
    assert selected == 0.05


def test_second_stage_gain_selection_rejects_shape_mismatch() -> None:
    try:
        _select_second_stage_gain(np.ones(2), np.ones(3), np.ones(2), 0.10, (0.05, 0.10, 0.15, 0.20))
    except ValueError:
        return
    raise AssertionError("mismatched gain arrays were accepted")
