"""Contract tests for D041 fixed channel mixtures."""

import numpy as np


def test_candidate_and_control_use_fixed_complementary_channels() -> None:
    fidelity = np.asarray([1.0, -0.5, 0.25], dtype=float)
    rbf_25 = np.asarray([0.5, 0.5, -0.25], dtype=float)
    rbf_50 = np.asarray([0.25, 0.75, -0.5], dtype=float)
    eta = 0.50

    candidate = eta * fidelity + (1.0 - eta) * rbf_25
    control = eta * rbf_25 + (1.0 - eta) * rbf_50

    assert np.allclose(candidate, np.asarray([0.75, 0.0, 0.0]))
    assert np.allclose(control, np.asarray([0.375, 0.625, -0.375]))
    assert np.all(np.isfinite(candidate))
    assert np.all(np.isfinite(control))
