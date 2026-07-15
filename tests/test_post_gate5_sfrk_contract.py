"""Contract tests for the D043 bounded convex residual stack."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_post_gate5_d043_sfrk import _bounded_weight


def test_bounded_weight_recovers_convex_optimum() -> None:
    first = np.asarray([1.0, 2.0, 3.0])
    second = np.asarray([0.0, 0.0, 0.0])
    target = np.asarray([0.5, 1.0, 1.5])
    weight, numerator, denominator = _bounded_weight(first, second, target)
    assert weight == 0.5
    assert numerator > 0.0
    assert denominator > 0.0


def test_bounded_weight_handles_identical_experts_and_clips() -> None:
    identical = np.ones(3)
    weight, _, denominator = _bounded_weight(identical, identical, np.zeros(3))
    assert weight == 0.5
    assert denominator == 0.0
    weight, _, _ = _bounded_weight(np.asarray([2.0]), np.asarray([0.0]), np.asarray([3.0]))
    assert weight == 1.0
