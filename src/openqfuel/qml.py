"""Small, auditable QML reference models for the frozen Phase 1 benchmark."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from typing import Mapping, Sequence

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin


@dataclass(frozen=True)
class NoiseSensitivity:
    """Hardware-agnostic sensitivity values, not a device calibration."""

    one_qubit_depolarizing_probability: float = 0.001
    two_qubit_depolarizing_probability: float = 0.01
    readout_bit_flip_probability: float = 0.02

    @classmethod
    def from_mapping(cls, value: Mapping[str, float]) -> "NoiseSensitivity":
        return cls(
            float(value["one_qubit_depolarizing_probability"]),
            float(value["two_qubit_depolarizing_probability"]),
            float(value["readout_bit_flip_probability"]),
        )

    def __post_init__(self) -> None:
        probabilities = (
            self.one_qubit_depolarizing_probability,
            self.two_qubit_depolarizing_probability,
            self.readout_bit_flip_probability,
        )
        if any(value < 0.0 or value >= 0.5 for value in probabilities):
            raise ValueError("Noise probabilities must lie in [0, 0.5)")


@dataclass(frozen=True)
class KernelPsdClipInfo:
    """Audit record for PSD clipping of a symmetric training kernel."""

    clipped_eigenvalues: int
    min_eigenvalue_before_clip: float
    max_negative_eigenvalue: float


def _ry(angle: float) -> np.ndarray:
    half = angle / 2.0
    return np.array(
        [[np.cos(half), -np.sin(half)], [np.sin(half), np.cos(half)]],
        dtype=complex,
    )


def _rz(angle: float) -> np.ndarray:
    half = angle / 2.0
    return np.array(
        [[np.exp(-1j * half), 0.0], [0.0, np.exp(1j * half)]],
        dtype=complex,
    )


def _apply_single_qubit(
    state: np.ndarray, gate: np.ndarray, qubit: int, n_qubits: int
) -> np.ndarray:
    tensor = state.reshape((2,) * n_qubits)
    front = np.moveaxis(tensor, qubit, 0).reshape(2, -1)
    updated = gate @ front
    restored = np.moveaxis(updated.reshape((2,) + (2,) * (n_qubits - 1)), 0, qubit)
    return restored.reshape(-1)


def _apply_cnot(
    state: np.ndarray, control: int, target: int, n_qubits: int
) -> np.ndarray:
    if control == target:
        raise ValueError("CNOT control and target must differ")
    indices = np.arange(state.size, dtype=np.int64)
    control_mask = 1 << (n_qubits - 1 - control)
    target_mask = 1 << (n_qubits - 1 - target)
    destinations = np.where(indices & control_mask, indices ^ target_mask, indices)
    updated = np.empty_like(state)
    updated[destinations] = state
    return updated


def _apply_ry_rz_batch(
    states: np.ndarray,
    first_angles: float | np.ndarray,
    second_angles: float | np.ndarray,
    qubit: int,
    n_qubits: int,
) -> None:
    """Apply one RY/RZ pair to every row without changing circuit ordering."""

    batch_size = states.shape[0]
    amplitudes = states.reshape(
        batch_size,
        1 << qubit,
        2,
        1 << (n_qubits - qubit - 1),
    )
    zero = amplitudes[:, :, 0, :]
    one = amplitudes[:, :, 1, :]
    original_zero = zero.copy()

    first_half = np.asarray(first_angles, dtype=float) / 2.0
    second_half = np.asarray(second_angles, dtype=float) / 2.0
    cosine = np.cos(first_half)
    sine = np.sin(first_half)
    phase_minus = np.exp(-1j * second_half)
    phase_plus = np.exp(1j * second_half)
    if first_half.ndim:
        cosine = cosine[:, None, None]
        sine = sine[:, None, None]
    if second_half.ndim:
        phase_minus = phase_minus[:, None, None]
        phase_plus = phase_plus[:, None, None]

    zero[...] = phase_minus * (cosine * zero - sine * one)
    one[...] = phase_plus * (sine * original_zero + cosine * one)


def _apply_cnot_batch(
    states: np.ndarray, control: int, target: int, n_qubits: int
) -> None:
    """Apply a CNOT in place across a leading batch dimension."""

    if control == target:
        raise ValueError("CNOT control and target must differ")
    tensor = states.reshape((states.shape[0],) + (2,) * n_qubits)
    zero_selector = [slice(None)] * (n_qubits + 1)
    one_selector = [slice(None)] * (n_qubits + 1)
    zero_selector[control + 1] = 1
    one_selector[control + 1] = 1
    zero_selector[target + 1] = 0
    one_selector[target + 1] = 1
    zero = tensor[tuple(zero_selector)]
    one = tensor[tuple(one_selector)]
    original_zero = zero.copy()
    zero[...] = one
    one[...] = original_zero


def _as_matrix(values: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("QML inputs must be a nonempty two-dimensional array")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("QML inputs must be finite")
    return matrix


def _validate_circuit(n_qubits: int, layers: int) -> None:
    if n_qubits not in {4, 6, 8, 10, 12}:
        raise ValueError("Qubit count must be one of 4, 6, 8, 10, or 12")
    if layers <= 0:
        raise ValueError("Circuit layers must be positive")


def _validate_feature_map(feature_scale: float, entangle: bool) -> None:
    if not np.isfinite(feature_scale) or feature_scale <= 0.0:
        raise ValueError("feature_scale must be positive and finite")
    if not isinstance(entangle, (bool, np.bool_)):
        raise ValueError("entangle must be boolean")


def circuit_state(
    features: Sequence[float],
    n_qubits: int,
    layers: int,
    parameters: np.ndarray | None = None,
    feature_scale: float = 1.0,
    entangle: bool = True,
) -> np.ndarray:
    """Return the frozen RY/RZ data-reuploading state."""

    _validate_circuit(n_qubits, layers)
    _validate_feature_map(feature_scale, entangle)
    values = np.asarray(features, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("Circuit features must be a finite one-dimensional vector")
    if parameters is not None and parameters.shape != (layers, n_qubits, 2):
        raise ValueError(
            f"Expected variational parameters with shape {(layers, n_qubits, 2)}"
        )

    state = np.zeros(2**n_qubits, dtype=complex)
    state[0] = 1.0
    for layer in range(layers):
        for qubit in range(n_qubits):
            first = feature_scale * values[(2 * qubit + 2 * layer) % values.size]
            second = feature_scale * values[(2 * qubit + 2 * layer + 1) % values.size]
            state = _apply_single_qubit(state, _ry(first), qubit, n_qubits)
            state = _apply_single_qubit(state, _rz(second), qubit, n_qubits)
        if entangle:
            for qubit in range(n_qubits):
                state = _apply_cnot(state, qubit, (qubit + 1) % n_qubits, n_qubits)
        if parameters is not None:
            for qubit in range(n_qubits):
                state = _apply_single_qubit(
                    state, _ry(parameters[layer, qubit, 0]), qubit, n_qubits
                )
                state = _apply_single_qubit(
                    state, _rz(parameters[layer, qubit, 1]), qubit, n_qubits
                )
    return state / np.linalg.norm(state)


def statevector_batch(
    values: Sequence[Sequence[float]] | np.ndarray,
    n_qubits: int,
    layers: int,
    parameters: np.ndarray | None = None,
    feature_scale: float = 1.0,
    entangle: bool = True,
) -> np.ndarray:
    matrix = _as_matrix(values)
    _validate_circuit(n_qubits, layers)
    _validate_feature_map(feature_scale, entangle)
    if parameters is not None and parameters.shape != (layers, n_qubits, 2):
        raise ValueError(
            f"Expected variational parameters with shape {(layers, n_qubits, 2)}"
        )

    states = np.zeros((matrix.shape[0], 2**n_qubits), dtype=complex)
    states[:, 0] = 1.0
    for layer in range(layers):
        for qubit in range(n_qubits):
            first = feature_scale * matrix[
                :, (2 * qubit + 2 * layer) % matrix.shape[1]
            ]
            second = feature_scale * matrix[
                :, (2 * qubit + 2 * layer + 1) % matrix.shape[1]
            ]
            _apply_ry_rz_batch(states, first, second, qubit, n_qubits)
        if entangle:
            for qubit in range(n_qubits):
                _apply_cnot_batch(
                    states, qubit, (qubit + 1) % n_qubits, n_qubits
                )
        if parameters is not None:
            for qubit in range(n_qubits):
                _apply_ry_rz_batch(
                    states,
                    parameters[layer, qubit, 0],
                    parameters[layer, qubit, 1],
                    qubit,
                    n_qubits,
                )
    states /= np.linalg.norm(states, axis=1, keepdims=True)
    return states


def quantum_kernel_matrix(
    left: Sequence[Sequence[float]] | np.ndarray,
    right: Sequence[Sequence[float]] | np.ndarray,
    n_qubits: int,
    layers: int,
    shots: int | None = None,
    seed: int = 0,
    noise: NoiseSensitivity | None = None,
    feature_scale: float = 1.0,
    entangle: bool = True,
) -> np.ndarray:
    """Return squared state overlaps, optionally sampled at finite shots."""

    left_matrix = _as_matrix(left)
    right_matrix = left_matrix if right is left else _as_matrix(right)
    left_states = statevector_batch(
        left_matrix,
        n_qubits,
        layers,
        feature_scale=feature_scale,
        entangle=entangle,
    )
    right_states = (
        left_states
        if right_matrix is left_matrix
        else statevector_batch(
            right_matrix,
            n_qubits,
            layers,
            feature_scale=feature_scale,
            entangle=entangle,
        )
    )
    probabilities = np.abs(left_states.conj() @ right_states.T) ** 2
    probabilities = np.clip(probabilities.real, 0.0, 1.0)
    if noise is not None:
        attenuation = _observable_attenuation(layers, noise, entangle)
        probabilities = 0.5 + attenuation * (probabilities - 0.5)
    if shots is None:
        return probabilities
    if shots <= 0:
        raise ValueError("shots must be positive")
    rng = np.random.default_rng(seed)
    return rng.binomial(shots, probabilities) / float(shots)


def _z_expectations(state: np.ndarray, n_qubits: int) -> np.ndarray:
    probabilities = np.abs(state) ** 2
    return probabilities @ _z_expectation_signs(n_qubits).T


@lru_cache(maxsize=None)
def _z_expectation_signs(n_qubits: int) -> np.ndarray:
    indices = np.arange(2**n_qubits, dtype=np.int64)
    signs = np.vstack(
        [
            np.where(
                indices & (1 << (n_qubits - 1 - qubit)),
                -1.0,
                1.0,
            )
            for qubit in range(n_qubits)
        ]
    )
    signs.setflags(write=False)
    return signs


def _as_state_matrix(states: Sequence[Sequence[complex]] | np.ndarray, n_qubits: int) -> np.ndarray:
    matrix = np.asarray(states, dtype=complex)
    if n_qubits <= 0:
        raise ValueError("n_qubits must be positive")
    if matrix.ndim == 1:
        matrix = matrix.reshape(1, -1)
    if matrix.ndim != 2 or matrix.shape[1] != 2**n_qubits:
        raise ValueError("Statevectors must have shape (rows, 2**n_qubits)")
    norms = np.linalg.norm(matrix, axis=1)
    if np.any(norms <= 0.0) or not np.all(np.isfinite(norms)):
        raise ValueError("Statevectors must be nonzero and finite")
    return matrix / norms[:, None]


def pauli_xyz_expectations(
    states: Sequence[Sequence[complex]] | np.ndarray, n_qubits: int
) -> np.ndarray:
    """Return Pauli X/Y/Z expectations for each one-qubit reduced state."""

    matrix = _as_state_matrix(states, n_qubits)
    tensor = matrix.reshape((matrix.shape[0],) + (2,) * n_qubits)
    projected = np.empty((matrix.shape[0], 3 * n_qubits), dtype=float)
    for qubit in range(n_qubits):
        moved = np.moveaxis(tensor, qubit + 1, 1).reshape(matrix.shape[0], 2, -1)
        zero = moved[:, 0, :]
        one = moved[:, 1, :]
        coherence = np.sum(np.conj(zero) * one, axis=1)
        projected[:, 3 * qubit] = 2.0 * coherence.real
        projected[:, 3 * qubit + 1] = 2.0 * coherence.imag
        projected[:, 3 * qubit + 2] = (
            np.sum(np.abs(zero) ** 2, axis=1) - np.sum(np.abs(one) ** 2, axis=1)
        )
    return np.clip(projected, -1.0, 1.0)


def projected_quantum_features(
    values: Sequence[Sequence[float]] | np.ndarray,
    n_qubits: int,
    layers: int,
    feature_scale: float = 1.0,
    entangle: bool = True,
) -> np.ndarray:
    """Encode inputs and project each state to one-qubit Bloch vectors."""

    states = statevector_batch(
        values,
        n_qubits,
        layers,
        feature_scale=feature_scale,
        entangle=entangle,
    )
    return pauli_xyz_expectations(states, n_qubits)


def _as_projected_features(values: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("Projected features must be a nonempty two-dimensional array")
    if matrix.shape[1] % 3:
        raise ValueError("Projected features must contain X/Y/Z values per qubit")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("Projected features must be finite")
    return matrix


def one_rdm_distance_matrix(
    left_features: Sequence[Sequence[float]] | np.ndarray,
    right_features: Sequence[Sequence[float]] | np.ndarray,
) -> np.ndarray:
    """Return summed one-RDM Frobenius distances between projected features."""

    left = _as_projected_features(left_features)
    right = left if right_features is left_features else _as_projected_features(right_features)
    if left.shape[1] != right.shape[1]:
        raise ValueError("Projected feature dimensions must match")
    left_sq = np.sum(left * left, axis=1)[:, None]
    right_sq = np.sum(right * right, axis=1)[None, :]
    squared_bloch = left_sq + right_sq - 2.0 * (left @ right.T)
    return np.maximum(0.5 * squared_bloch, 0.0)


def median_projected_kernel_gamma(
    training_features: Sequence[Sequence[float]] | np.ndarray,
    gamma_multiplier: float = 1.0,
) -> float:
    """Compute the fold-local D008 median-distance bandwidth."""

    if not np.isfinite(gamma_multiplier) or gamma_multiplier <= 0.0:
        raise ValueError("gamma_multiplier must be positive and finite")
    distances = one_rdm_distance_matrix(training_features, training_features)
    positive = distances[distances > 0.0]
    if positive.size == 0:
        raise ValueError("Projected-kernel median distance is zero")
    median = float(np.median(positive))
    if not np.isfinite(median) or median <= 0.0:
        raise ValueError("Projected-kernel median distance is zero")
    return float(gamma_multiplier / median)


def projected_quantum_kernel_from_features(
    left_features: Sequence[Sequence[float]] | np.ndarray,
    right_features: Sequence[Sequence[float]] | np.ndarray,
    gamma: float,
) -> np.ndarray:
    """Return exp(-gamma * one-RDM Frobenius distance)."""

    if not np.isfinite(gamma) or gamma <= 0.0:
        raise ValueError("Projected-kernel gamma must be positive and finite")
    distances = one_rdm_distance_matrix(left_features, right_features)
    return np.exp(-float(gamma) * distances)


def projected_quantum_kernel_matrix(
    left: Sequence[Sequence[float]] | np.ndarray,
    right: Sequence[Sequence[float]] | np.ndarray,
    n_qubits: int,
    layers: int,
    gamma: float | None = None,
    gamma_multiplier: float = 1.0,
    feature_scale: float = 1.0,
    entangle: bool = True,
) -> np.ndarray:
    """Return the D008 projected quantum kernel for already compressed inputs."""

    left_features = projected_quantum_features(
        left, n_qubits, layers, feature_scale=feature_scale, entangle=entangle
    )
    right_features = (
        left_features
        if right is left
        else projected_quantum_features(
            right, n_qubits, layers, feature_scale=feature_scale, entangle=entangle
        )
    )
    active_gamma = (
        median_projected_kernel_gamma(left_features, gamma_multiplier)
        if gamma is None
        else float(gamma)
    )
    return projected_quantum_kernel_from_features(
        left_features, right_features, active_gamma
    )


def deterministic_landmark_indices(
    row_ids: Sequence[str],
    projection_id: str,
    fold_id: str,
    seed_index: int,
    landmark_count: int,
) -> np.ndarray:
    """Select D008 Nystrom landmarks by SHA-256 rank from training rows only."""

    ids = [str(value) for value in row_ids]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Landmark row IDs must be nonempty and unique")
    if landmark_count <= 0 or landmark_count > len(ids):
        raise ValueError("landmark_count must be in [1, row_count]")
    ranked = sorted(
        range(len(ids)),
        key=lambda index: hashlib.sha256(
            "|".join(
                [
                    "post_gate5_landmark_v1",
                    ids[index],
                    str(projection_id),
                    str(fold_id),
                    str(seed_index),
                ]
            ).encode("utf-8")
        ).hexdigest(),
    )
    return np.asarray(ranked[:landmark_count], dtype=int)


def symmetrize_and_clip_psd(
    kernel: Sequence[Sequence[float]] | np.ndarray,
    floor: float = 1e-12,
) -> tuple[np.ndarray, KernelPsdClipInfo]:
    """Symmetrize a training kernel and clip eigenvalues below the floor."""

    matrix = np.asarray(kernel, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0:
        raise ValueError("Training kernel must be a nonempty square matrix")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("Training kernel must be finite")
    if not np.isfinite(floor) or floor <= 0.0:
        raise ValueError("PSD floor must be positive and finite")
    symmetric = 0.5 * (matrix + matrix.T)
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    clipped = np.clip(eigenvalues, floor, None)
    clipped_kernel = (eigenvectors * clipped) @ eigenvectors.T
    clipped_kernel = 0.5 * (clipped_kernel + clipped_kernel.T)
    minimum = float(np.min(eigenvalues))
    return clipped_kernel, KernelPsdClipInfo(
        clipped_eigenvalues=int(np.sum(eigenvalues < floor)),
        min_eigenvalue_before_clip=minimum,
        max_negative_eigenvalue=min(minimum, 0.0),
    )


def _observable_attenuation(
    layers: int, noise: NoiseSensitivity, entangle: bool = True
) -> float:
    one_qubit = (1.0 - 4.0 * noise.one_qubit_depolarizing_probability / 3.0) ** (
        4 * layers
    )
    two_qubit_exponent = 2 * layers if entangle else 0
    two_qubit = (
        1.0 - 16.0 * noise.two_qubit_depolarizing_probability / 15.0
    ) ** two_qubit_exponent
    readout = 1.0 - 2.0 * noise.readout_bit_flip_probability
    return float(np.clip(one_qubit * two_qubit * readout, 0.0, 1.0))


def circuit_features(
    values: Sequence[Sequence[float]] | np.ndarray,
    n_qubits: int,
    layers: int,
    parameters: np.ndarray,
    shots: int | None = None,
    seed: int = 0,
    noise: NoiseSensitivity | None = None,
    feature_scale: float = 1.0,
    entangle: bool = True,
) -> np.ndarray:
    """Return one Z expectation per qubit for each encoded row."""

    states = statevector_batch(
        values,
        n_qubits,
        layers,
        parameters,
        feature_scale,
        entangle,
    )
    exact = np.abs(states) ** 2 @ _z_expectation_signs(n_qubits).T
    if shots is None:
        return exact
    if shots <= 0:
        raise ValueError("shots must be positive")
    attenuation = (
        1.0 if noise is None else _observable_attenuation(layers, noise, entangle)
    )
    probabilities = np.clip((1.0 + attenuation * exact) / 2.0, 0.0, 1.0)
    rng = np.random.default_rng(seed)
    counts = rng.binomial(shots, probabilities)
    return 2.0 * counts / float(shots) - 1.0


class QuantumKernelRegressor(RegressorMixin, BaseEstimator):
    """Kernel ridge regression using the frozen quantum feature map."""

    def __init__(
        self,
        n_qubits: int = 4,
        layers: int = 2,
        alpha: float = 0.01,
        landmarks: int | None = None,
        seed: int = 0,
        feature_scale: float = 1.0,
        entangle: bool = True,
    ) -> None:
        self.n_qubits = n_qubits
        self.layers = layers
        self.alpha = alpha
        self.landmarks = landmarks
        self.seed = seed
        self.feature_scale = feature_scale
        self.entangle = entangle

    def fit(self, x: np.ndarray, y: Sequence[float]) -> "QuantumKernelRegressor":
        matrix = _as_matrix(x)
        targets = np.asarray(y, dtype=float)
        if targets.shape != (matrix.shape[0],):
            raise ValueError("Targets must contain one value per row")
        if self.alpha <= 0:
            raise ValueError("Kernel regularization must be positive")
        if self.landmarks is not None and self.landmarks <= 0:
            raise ValueError("landmarks must be positive when provided")
        if self.landmarks is None or matrix.shape[0] <= self.landmarks:
            kernel = quantum_kernel_matrix(
                matrix,
                matrix,
                self.n_qubits,
                self.layers,
                feature_scale=self.feature_scale,
                entangle=self.entangle,
            )
            self.x_fit_ = matrix.copy()
            self.dual_coef_ = np.linalg.solve(
                kernel + self.alpha * np.eye(kernel.shape[0]), targets
            )
            self.landmark_features_ = None
            return self

        rng = np.random.default_rng(self.seed)
        indices = np.sort(
            rng.choice(matrix.shape[0], size=self.landmarks, replace=False)
        )
        self.x_fit_ = matrix[indices].copy()
        landmark_kernel = quantum_kernel_matrix(
            self.x_fit_,
            self.x_fit_,
            self.n_qubits,
            self.layers,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
        )
        eigenvalues, eigenvectors = np.linalg.eigh(landmark_kernel)
        floor = max(self.alpha * 1e-6, 1e-12)
        inverse_root = (
            eigenvectors * (1.0 / np.sqrt(np.clip(eigenvalues, floor, None)))
        ) @ eigenvectors.T
        cross_kernel = quantum_kernel_matrix(
            matrix,
            self.x_fit_,
            self.n_qubits,
            self.layers,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
        )
        features = cross_kernel @ inverse_root
        self.landmark_features_ = inverse_root
        self.feature_coef_ = np.linalg.solve(
            features.T @ features + self.alpha * np.eye(features.shape[1]),
            features.T @ targets,
        )
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "x_fit_"):
            raise RuntimeError("QuantumKernelRegressor is not fitted")
        kernel = quantum_kernel_matrix(
            _as_matrix(x),
            self.x_fit_,
            self.n_qubits,
            self.layers,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
        )
        if self.landmark_features_ is None:
            return kernel @ self.dual_coef_
        return kernel @ self.landmark_features_ @ self.feature_coef_


class QuantumKernelClassifier(ClassifierMixin, BaseEstimator):
    """A deterministic kernel probability surrogate for feasibility."""

    def __init__(
        self,
        n_qubits: int = 4,
        layers: int = 2,
        alpha: float = 0.01,
        landmarks: int | None = None,
        seed: int = 0,
        feature_scale: float = 1.0,
        entangle: bool = True,
    ) -> None:
        self.n_qubits = n_qubits
        self.layers = layers
        self.alpha = alpha
        self.landmarks = landmarks
        self.seed = seed
        self.feature_scale = feature_scale
        self.entangle = entangle

    def fit(self, x: np.ndarray, y: Sequence[int]) -> "QuantumKernelClassifier":
        labels = np.asarray(y, dtype=float)
        if not set(np.unique(labels)).issubset({0.0, 1.0}):
            raise ValueError("Quantum feasibility labels must be binary")
        self.regressor_ = QuantumKernelRegressor(
            self.n_qubits,
            self.layers,
            self.alpha,
            self.landmarks,
            self.seed,
            self.feature_scale,
            self.entangle,
        ).fit(x, labels)
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "regressor_"):
            raise RuntimeError("QuantumKernelClassifier is not fitted")
        probability = np.clip(self.regressor_.predict(x), 0.0, 1.0)
        return np.column_stack((1.0 - probability, probability))

    def predict(self, x: np.ndarray) -> np.ndarray:
        return (self.predict_proba(x)[:, 1] >= 0.5).astype(int)


class ProjectedQuantumKernelRegressor(RegressorMixin, BaseEstimator):
    """D008 projected-kernel ridge regression with deterministic landmarks."""

    def __init__(
        self,
        n_qubits: int = 4,
        layers: int = 1,
        alpha: float = 0.01,
        landmarks: int = 256,
        gamma_multiplier: float = 1.0,
        projection_id: str = "synthetic",
        fold_id: str = "synthetic",
        seed_index: int = 1,
        feature_scale: float = 1.0,
        entangle: bool = True,
    ) -> None:
        self.n_qubits = n_qubits
        self.layers = layers
        self.alpha = alpha
        self.landmarks = landmarks
        self.gamma_multiplier = gamma_multiplier
        self.projection_id = projection_id
        self.fold_id = fold_id
        self.seed_index = seed_index
        self.feature_scale = feature_scale
        self.entangle = entangle

    @staticmethod
    def _default_row_ids(row_count: int) -> list[str]:
        return [f"synthetic-row-{index:06d}" for index in range(row_count)]

    def _project(self, x: np.ndarray) -> np.ndarray:
        return projected_quantum_features(
            x,
            self.n_qubits,
            self.layers,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
        )

    def fit(
        self,
        x: np.ndarray,
        y: Sequence[float],
        row_ids: Sequence[str] | None = None,
    ) -> "ProjectedQuantumKernelRegressor":
        matrix = _as_matrix(x)
        targets = np.asarray(y, dtype=float)
        if targets.shape != (matrix.shape[0],):
            raise ValueError("Targets must contain one value per row")
        if not np.all(np.isfinite(targets)):
            raise ValueError("Targets must be finite")
        if self.alpha <= 0.0:
            raise ValueError("Kernel regularization must be positive")
        if self.landmarks <= 0:
            raise ValueError("landmarks must be positive")

        ids = self._default_row_ids(matrix.shape[0]) if row_ids is None else list(row_ids)
        if len(ids) != matrix.shape[0]:
            raise ValueError("row_ids must contain one value per training row")
        projected = self._project(matrix)
        self.gamma_ = median_projected_kernel_gamma(
            projected, float(self.gamma_multiplier)
        )
        landmark_count = min(int(self.landmarks), matrix.shape[0])
        self.landmark_indices_ = deterministic_landmark_indices(
            ids,
            str(self.projection_id),
            str(self.fold_id),
            int(self.seed_index),
            landmark_count,
        )

        if landmark_count == matrix.shape[0]:
            kernel = projected_quantum_kernel_from_features(
                projected, projected, self.gamma_
            )
            clipped, info = symmetrize_and_clip_psd(kernel)
            self.psd_clip_info_ = info
            self.training_features_ = projected
            self.landmark_features_ = None
            self.nystrom_inverse_root_ = None
            self.dual_coef_ = np.linalg.solve(
                clipped + float(self.alpha) * np.eye(clipped.shape[0]),
                targets,
            )
            return self

        self.training_features_ = None
        self.landmark_features_ = projected[self.landmark_indices_]
        landmark_kernel = projected_quantum_kernel_from_features(
            self.landmark_features_, self.landmark_features_, self.gamma_
        )
        clipped, info = symmetrize_and_clip_psd(landmark_kernel)
        self.psd_clip_info_ = info
        eigenvalues, eigenvectors = np.linalg.eigh(clipped)
        inverse_root = (eigenvectors * (1.0 / np.sqrt(eigenvalues))) @ eigenvectors.T
        cross_kernel = projected_quantum_kernel_from_features(
            projected, self.landmark_features_, self.gamma_
        )
        features = cross_kernel @ inverse_root
        self.nystrom_inverse_root_ = inverse_root
        self.feature_coef_ = np.linalg.solve(
            features.T @ features + float(self.alpha) * np.eye(features.shape[1]),
            features.T @ targets,
        )
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "gamma_"):
            raise RuntimeError("ProjectedQuantumKernelRegressor is not fitted")
        projected = self._project(_as_matrix(x))
        if self.training_features_ is not None:
            kernel = projected_quantum_kernel_from_features(
                projected, self.training_features_, self.gamma_
            )
            return kernel @ self.dual_coef_
        kernel = projected_quantum_kernel_from_features(
            projected, self.landmark_features_, self.gamma_
        )
        return kernel @ self.nystrom_inverse_root_ @ self.feature_coef_


class ProjectedQuantumKernelClassifier(ClassifierMixin, BaseEstimator):
    """D008 feasibility-only projected-kernel least-squares classifier."""

    def __init__(
        self,
        n_qubits: int = 4,
        layers: int = 1,
        alpha: float = 0.01,
        landmarks: int = 256,
        gamma_multiplier: float = 1.0,
        projection_id: str = "synthetic",
        fold_id: str = "synthetic",
        seed_index: int = 1,
        feature_scale: float = 1.0,
        entangle: bool = True,
    ) -> None:
        self.n_qubits = n_qubits
        self.layers = layers
        self.alpha = alpha
        self.landmarks = landmarks
        self.gamma_multiplier = gamma_multiplier
        self.projection_id = projection_id
        self.fold_id = fold_id
        self.seed_index = seed_index
        self.feature_scale = feature_scale
        self.entangle = entangle

    def fit(
        self,
        x: np.ndarray,
        y: Sequence[int],
        row_ids: Sequence[str] | None = None,
    ) -> "ProjectedQuantumKernelClassifier":
        labels = np.asarray(y, dtype=float)
        if labels.ndim != 1 or not set(np.unique(labels)).issubset({0.0, 1.0}):
            raise ValueError("Projected-kernel feasibility labels must be binary")
        self.regressor_ = ProjectedQuantumKernelRegressor(
            n_qubits=self.n_qubits,
            layers=self.layers,
            alpha=self.alpha,
            landmarks=self.landmarks,
            gamma_multiplier=self.gamma_multiplier,
            projection_id=self.projection_id,
            fold_id=self.fold_id,
            seed_index=self.seed_index,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
        ).fit(x, labels, row_ids=row_ids)
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "regressor_"):
            raise RuntimeError("ProjectedQuantumKernelClassifier is not fitted")
        probability = np.clip(self.regressor_.predict(x), 0.0, 1.0)
        return np.column_stack((1.0 - probability, probability))

    def predict(self, x: np.ndarray) -> np.ndarray:
        return (self.predict_proba(x)[:, 1] >= 0.5).astype(int)


class PhysicsAnchoredProjectedQuantumKernelRegressor(
    RegressorMixin, BaseEstimator
):
    """Projected quantum-kernel ridge model for residuals over a physics baseline.

    The final column is a standardized low-fidelity cost.  It is never encoded
    by the circuit; it is added back after the kernel predicts the residual.
    """

    def __init__(
        self,
        n_qubits: int = 4,
        layers: int = 1,
        alpha: float = 0.01,
        landmarks: int = 256,
        gamma_multiplier: float = 1.0,
        projection_id: str = "synthetic",
        fold_id: str = "synthetic",
        seed_index: int = 1,
        feature_scale: float = 1.0,
        entangle: bool = True,
        low_fidelity_column: int = -1,
    ) -> None:
        self.n_qubits = n_qubits
        self.layers = layers
        self.alpha = alpha
        self.landmarks = landmarks
        self.gamma_multiplier = gamma_multiplier
        self.projection_id = projection_id
        self.fold_id = fold_id
        self.seed_index = seed_index
        self.feature_scale = feature_scale
        self.entangle = entangle
        self.low_fidelity_column = low_fidelity_column

    @staticmethod
    def _default_row_ids(row_count: int) -> list[str]:
        return [f"synthetic-row-{index:06d}" for index in range(row_count)]

    def _split_input(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        matrix = _as_matrix(x)
        column = self.low_fidelity_column
        if not -matrix.shape[1] <= column < matrix.shape[1]:
            raise ValueError("low_fidelity_column is outside the input matrix")
        return np.delete(matrix, column, axis=1), matrix[:, column]

    def _fit_projected(
        self,
        projected: np.ndarray,
        baseline: np.ndarray,
        targets: np.ndarray,
        row_ids: Sequence[str] | None,
    ) -> "PhysicsAnchoredProjectedQuantumKernelRegressor":
        features = _as_projected_features(projected)
        baseline_values = np.asarray(baseline, dtype=float)
        if baseline_values.shape != (features.shape[0],):
            raise ValueError("Residual baseline must contain one value per row")
        if not np.all(np.isfinite(baseline_values)):
            raise ValueError("Residual baseline must be finite")
        if targets.shape != (features.shape[0],) or not np.all(np.isfinite(targets)):
            raise ValueError("Targets must contain finite values per row")
        if self.alpha <= 0.0 or self.landmarks <= 0:
            raise ValueError("Kernel regularization and landmarks must be positive")

        ids = (
            self._default_row_ids(features.shape[0])
            if row_ids is None
            else list(row_ids)
        )
        if len(ids) != features.shape[0] or len(set(ids)) != len(ids):
            raise ValueError("row_ids must be unique and match training rows")
        self.gamma_ = median_projected_kernel_gamma(
            features, float(self.gamma_multiplier)
        )
        landmark_count = min(int(self.landmarks), features.shape[0])
        self.landmark_indices_ = deterministic_landmark_indices(
            ids,
            str(self.projection_id),
            str(self.fold_id),
            int(self.seed_index),
            landmark_count,
        )
        residual = targets - baseline_values
        self.baseline_train_ = baseline_values.copy()
        self.projected_training_features_ = features.copy()
        if landmark_count == features.shape[0]:
            kernel = projected_quantum_kernel_from_features(
                features, features, self.gamma_
            )
            clipped, info = symmetrize_and_clip_psd(kernel)
            self.psd_clip_info_ = info
            self.training_features_ = features
            self.landmark_features_ = None
            self.nystrom_inverse_root_ = None
            self.dual_coef_ = np.linalg.solve(
                clipped + float(self.alpha) * np.eye(clipped.shape[0]),
                residual,
            )
            return self

        self.training_features_ = None
        self.landmark_features_ = features[self.landmark_indices_]
        landmark_kernel = projected_quantum_kernel_from_features(
            self.landmark_features_, self.landmark_features_, self.gamma_
        )
        clipped, info = symmetrize_and_clip_psd(landmark_kernel)
        self.psd_clip_info_ = info
        eigenvalues, eigenvectors = np.linalg.eigh(clipped)
        inverse_root = (eigenvectors * (1.0 / np.sqrt(eigenvalues))) @ eigenvectors.T
        cross_kernel = projected_quantum_kernel_from_features(
            features, self.landmark_features_, self.gamma_
        )
        embedding = cross_kernel @ inverse_root
        self.nystrom_inverse_root_ = inverse_root
        self.feature_coef_ = np.linalg.solve(
            embedding.T @ embedding + float(self.alpha) * np.eye(embedding.shape[1]),
            embedding.T @ residual,
        )
        return self

    def fit_projected(
        self,
        projected: np.ndarray,
        baseline: Sequence[float],
        y: Sequence[float],
        row_ids: Sequence[str] | None = None,
    ) -> "PhysicsAnchoredProjectedQuantumKernelRegressor":
        features = _as_projected_features(projected)
        return self._fit_projected(
            features,
            np.asarray(baseline, dtype=float),
            np.asarray(y, dtype=float),
            row_ids,
        )

    def fit(
        self,
        x: np.ndarray,
        y: Sequence[float],
        row_ids: Sequence[str] | None = None,
    ) -> "PhysicsAnchoredProjectedQuantumKernelRegressor":
        circuit_input, baseline = self._split_input(x)
        projected = projected_quantum_features(
            circuit_input,
            self.n_qubits,
            self.layers,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
        )
        return self._fit_projected(
            projected, baseline, np.asarray(y, dtype=float), row_ids
        )

    def _predict_residual(self, projected: np.ndarray) -> np.ndarray:
        if not hasattr(self, "gamma_"):
            raise RuntimeError(
                "PhysicsAnchoredProjectedQuantumKernelRegressor is not fitted"
            )
        features = _as_projected_features(projected)
        if self.training_features_ is not None:
            kernel = projected_quantum_kernel_from_features(
                features, self.training_features_, self.gamma_
            )
            return kernel @ self.dual_coef_
        kernel = projected_quantum_kernel_from_features(
            features, self.landmark_features_, self.gamma_
        )
        return kernel @ self.nystrom_inverse_root_ @ self.feature_coef_

    def predict_projected(
        self, projected: np.ndarray, baseline: Sequence[float]
    ) -> np.ndarray:
        features = _as_projected_features(projected)
        baseline_values = np.asarray(baseline, dtype=float)
        if baseline_values.shape != (features.shape[0],):
            raise ValueError("Prediction baseline must contain one value per row")
        return baseline_values + self._predict_residual(features)

    def predict(self, x: np.ndarray) -> np.ndarray:
        circuit_input, baseline = self._split_input(x)
        projected = projected_quantum_features(
            circuit_input,
            self.n_qubits,
            self.layers,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
        )
        return self.predict_projected(projected, baseline)


class PhysicsAnchoredProjectedQuantumKernelClassifier(
    ClassifierMixin, BaseEstimator
):
    """Feasibility head using the same projected map without encoding cost."""

    def __init__(
        self,
        n_qubits: int = 4,
        layers: int = 1,
        alpha: float = 0.01,
        landmarks: int = 256,
        gamma_multiplier: float = 1.0,
        projection_id: str = "synthetic",
        fold_id: str = "synthetic",
        seed_index: int = 1,
        feature_scale: float = 1.0,
        entangle: bool = True,
        low_fidelity_column: int = -1,
    ) -> None:
        self.n_qubits = n_qubits
        self.layers = layers
        self.alpha = alpha
        self.landmarks = landmarks
        self.gamma_multiplier = gamma_multiplier
        self.projection_id = projection_id
        self.fold_id = fold_id
        self.seed_index = seed_index
        self.feature_scale = feature_scale
        self.entangle = entangle
        self.low_fidelity_column = low_fidelity_column

    def fit(
        self,
        x: np.ndarray,
        y: Sequence[int],
        row_ids: Sequence[str] | None = None,
    ) -> "PhysicsAnchoredProjectedQuantumKernelClassifier":
        labels = np.asarray(y, dtype=float)
        if labels.ndim != 1 or not set(np.unique(labels)).issubset({0.0, 1.0}):
            raise ValueError("Projected-kernel feasibility labels must be binary")
        model = PhysicsAnchoredProjectedQuantumKernelRegressor(
            n_qubits=self.n_qubits,
            layers=self.layers,
            alpha=self.alpha,
            landmarks=self.landmarks,
            gamma_multiplier=self.gamma_multiplier,
            projection_id=self.projection_id,
            fold_id=self.fold_id,
            seed_index=self.seed_index,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
            low_fidelity_column=self.low_fidelity_column,
        )
        circuit_input, baseline = model._split_input(x)
        projected = projected_quantum_features(
            circuit_input,
            model.n_qubits,
            model.layers,
            feature_scale=model.feature_scale,
            entangle=model.entangle,
        )
        self.regressor_ = model.fit_projected(
            projected, np.zeros_like(baseline), labels, row_ids=row_ids
        )
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "regressor_"):
            raise RuntimeError(
                "PhysicsAnchoredProjectedQuantumKernelClassifier is not fitted"
            )
        circuit_input, baseline = self.regressor_._split_input(x)
        projected = projected_quantum_features(
            circuit_input,
            self.regressor_.n_qubits,
            self.regressor_.layers,
            feature_scale=self.regressor_.feature_scale,
            entangle=self.regressor_.entangle,
        )
        probability = np.clip(
            self.regressor_.predict_projected(projected, np.zeros_like(baseline)),
            0.0,
            1.0,
        )
        return np.column_stack((1.0 - probability, probability))

    def predict(self, x: np.ndarray) -> np.ndarray:
        return (self.predict_proba(x)[:, 1] >= 0.5).astype(int)


class VariationalQuantumRegressor(RegressorMixin, BaseEstimator):
    """Data-reuploading variational circuit with a trainable linear head."""

    def __init__(
        self,
        n_qubits: int = 4,
        layers: int = 2,
        regularization: float = 0.0001,
        maximum_optimizer_iterations: int = 100,
        seed: int = 0,
        feature_scale: float = 1.0,
        entangle: bool = True,
    ) -> None:
        self.n_qubits = n_qubits
        self.layers = layers
        self.regularization = regularization
        self.maximum_optimizer_iterations = maximum_optimizer_iterations
        self.seed = seed
        self.feature_scale = feature_scale
        self.entangle = entangle

    @property
    def _circuit_parameter_count(self) -> int:
        return self.layers * self.n_qubits * 2

    def _unpack(self, values: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
        stop = self._circuit_parameter_count
        parameters = values[:stop].reshape(self.layers, self.n_qubits, 2)
        head = values[stop : stop + self.n_qubits]
        bias = float(values[-1])
        return parameters, head, bias

    def fit(self, x: np.ndarray, y: Sequence[float]) -> "VariationalQuantumRegressor":
        matrix = _as_matrix(x)
        targets = np.asarray(y, dtype=float)
        if targets.shape != (matrix.shape[0],):
            raise ValueError("Targets must contain one value per row")
        _validate_circuit(self.n_qubits, self.layers)
        if self.regularization < 0 or self.maximum_optimizer_iterations <= 0:
            raise ValueError("Invalid VQR optimization settings")

        rng = np.random.default_rng(self.seed)
        initial = rng.uniform(
            -0.05,
            0.05,
            self._circuit_parameter_count + self.n_qubits + 1,
        )

        def objective(values: np.ndarray) -> float:
            parameters, head, bias = self._unpack(values)
            encoded = circuit_features(
                matrix,
                self.n_qubits,
                self.layers,
                parameters,
                feature_scale=self.feature_scale,
                entangle=self.entangle,
            )
            residual = encoded @ head + bias - targets
            penalty = self.regularization * float(np.dot(values[:-1], values[:-1]))
            return float(np.mean(residual * residual) + penalty)

        self.initial_loss_ = objective(initial)
        result = minimize(
            objective,
            initial,
            method="L-BFGS-B",
            options={"maxiter": self.maximum_optimizer_iterations},
        )
        self.parameters_, self.head_, self.bias_ = self._unpack(result.x)
        self.optimization_success_ = bool(result.success)
        self.optimization_message_ = str(result.message)
        self.training_loss_ = float(result.fun)
        self.loss_improvement_ = self.initial_loss_ - self.training_loss_
        self.optimizer_iterations_ = int(getattr(result, "nit", 0))
        self.objective_evaluations_ = int(getattr(result, "nfev", 0))
        jacobian = getattr(result, "jac", None)
        self.gradient_norm_proxy_ = (
            float(np.linalg.norm(np.asarray(jacobian, dtype=float)))
            if jacobian is not None
            else None
        )
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "parameters_"):
            raise RuntimeError("VariationalQuantumRegressor is not fitted")
        encoded = circuit_features(
            _as_matrix(x),
            self.n_qubits,
            self.layers,
            self.parameters_,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
        )
        return encoded @ self.head_ + self.bias_

    def predict_finite_shot(
        self,
        x: np.ndarray,
        shots: int,
        seed: int,
        noise: NoiseSensitivity | None = None,
    ) -> np.ndarray:
        if not hasattr(self, "parameters_"):
            raise RuntimeError("VariationalQuantumRegressor is not fitted")
        encoded = circuit_features(
            _as_matrix(x),
            self.n_qubits,
            self.layers,
            self.parameters_,
            shots=shots,
            seed=seed,
            noise=noise,
            feature_scale=self.feature_scale,
            entangle=self.entangle,
        )
        return encoded @ self.head_ + self.bias_


class VariationalQuantumClassifier(ClassifierMixin, BaseEstimator):
    """Feasibility head sharing the variational regressor implementation."""

    def __init__(
        self,
        n_qubits: int = 4,
        layers: int = 2,
        regularization: float = 0.0001,
        maximum_optimizer_iterations: int = 100,
        seed: int = 0,
        feature_scale: float = 1.0,
        entangle: bool = True,
    ) -> None:
        self.n_qubits = n_qubits
        self.layers = layers
        self.regularization = regularization
        self.maximum_optimizer_iterations = maximum_optimizer_iterations
        self.seed = seed
        self.feature_scale = feature_scale
        self.entangle = entangle

    def fit(self, x: np.ndarray, y: Sequence[int]) -> "VariationalQuantumClassifier":
        labels = np.asarray(y, dtype=float)
        if not set(np.unique(labels)).issubset({0.0, 1.0}):
            raise ValueError("Quantum feasibility labels must be binary")
        clipped = np.clip(labels, 0.05, 0.95)
        logits = np.log(clipped / (1.0 - clipped))
        self.regressor_ = VariationalQuantumRegressor(
            self.n_qubits,
            self.layers,
            self.regularization,
            self.maximum_optimizer_iterations,
            self.seed,
            self.feature_scale,
            self.entangle,
        ).fit(x, logits)
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "regressor_"):
            raise RuntimeError("VariationalQuantumClassifier is not fitted")
        probability = expit(self.regressor_.predict(x))
        return np.column_stack((1.0 - probability, probability))

    def predict(self, x: np.ndarray) -> np.ndarray:
        return (self.predict_proba(x)[:, 1] >= 0.5).astype(int)


class HybridQuantumResidualRegressor(RegressorMixin, BaseEstimator):
    """Learn a quantum residual over a frozen low-fidelity feature column."""

    def __init__(
        self,
        low_fidelity_column: int = -1,
        n_qubits: int = 4,
        layers: int = 2,
        regularization: float = 0.0001,
        maximum_optimizer_iterations: int = 100,
        seed: int = 0,
        feature_scale: float = 1.0,
        entangle: bool = True,
    ) -> None:
        self.low_fidelity_column = low_fidelity_column
        self.n_qubits = n_qubits
        self.layers = layers
        self.regularization = regularization
        self.maximum_optimizer_iterations = maximum_optimizer_iterations
        self.seed = seed
        self.feature_scale = feature_scale
        self.entangle = entangle

    def fit(
        self, x: np.ndarray, y: Sequence[float]
    ) -> "HybridQuantumResidualRegressor":
        matrix = _as_matrix(x)
        targets = np.asarray(y, dtype=float)
        baseline = matrix[:, self.low_fidelity_column]
        circuit_matrix = np.delete(matrix, self.low_fidelity_column, axis=1)
        self.residual_model_ = VariationalQuantumRegressor(
            self.n_qubits,
            self.layers,
            self.regularization,
            self.maximum_optimizer_iterations,
            self.seed,
            self.feature_scale,
            self.entangle,
        ).fit(circuit_matrix, targets - baseline)
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "residual_model_"):
            raise RuntimeError("HybridQuantumResidualRegressor is not fitted")
        matrix = _as_matrix(x)
        baseline = matrix[:, self.low_fidelity_column]
        circuit_matrix = np.delete(matrix, self.low_fidelity_column, axis=1)
        return baseline + self.residual_model_.predict(circuit_matrix)
