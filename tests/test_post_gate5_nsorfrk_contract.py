"""Contract tests for D048 nested shrinkage selection."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_post_gate5_d048_nsorfrk import _select_shrinkage


def test_shrinkage_selection_uses_declared_grid() -> None:
    selected, losses = _select_shrinkage(np.asarray([0.1, 0.1]), np.asarray([2.0, 2.0]), np.asarray([0.0, 0.0]), (0.05, 0.10, 0.15))
    assert selected == 0.05
    assert len(losses) == 3


def test_shrinkage_selection_ties_to_smallest_value() -> None:
    values = np.asarray([1.0, -1.0])
    selected, _ = _select_shrinkage(values, np.zeros(2), np.zeros(2), (0.05, 0.10, 0.15))
    assert selected == 0.05


def test_shrinkage_selection_rejects_shape_mismatch() -> None:
    try:
        _select_shrinkage(np.ones(2), np.ones(3), np.ones(2), (0.05, 0.10, 0.15))
    except ValueError:
        return
    raise AssertionError("mismatched shrinkage arrays were accepted")
