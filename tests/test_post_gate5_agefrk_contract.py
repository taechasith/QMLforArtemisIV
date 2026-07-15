"""Contract tests for the D042 outcome-blind adaptive gate."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_post_gate5_d042_agefrk import _adaptive_eta


def test_adaptive_eta_is_bounded_and_monotone() -> None:
    probability = np.asarray([0.0, 0.25, 0.5, 0.75, 1.0])
    eta = _adaptive_eta(probability)
    np.testing.assert_allclose(eta, [0.75, 0.625, 0.5, 0.375, 0.25])
    assert np.all((eta >= 0.25) & (eta <= 0.75))
    assert np.all(np.diff(eta) < 0.0)


def test_adaptive_eta_rejects_non_probability_values() -> None:
    for values in ([-0.1], [1.1], [float("nan")]):
        try:
            _adaptive_eta(np.asarray(values))
        except ValueError:
            continue
        raise AssertionError("invalid probability was accepted")
