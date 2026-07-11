"""Small, auditable QML reference models for the frozen Phase 1 benchmark."""

from __future__ import annotations

from dataclasses import dataclass
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
    return np.vstack(
        [
            circuit_state(
                row,
                n_qubits,
                layers,
                parameters,
                feature_scale,
                entangle,
            )
            for row in matrix
        ]
    )


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

    left_states = statevector_batch(
        left, n_qubits, layers, feature_scale=feature_scale, entangle=entangle
    )
    right_states = statevector_batch(
        right, n_qubits, layers, feature_scale=feature_scale, entangle=entangle
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
    indices = np.arange(state.size, dtype=np.int64)
    expectations = []
    for qubit in range(n_qubits):
        mask = 1 << (n_qubits - 1 - qubit)
        signs = np.where(indices & mask, -1.0, 1.0)
        expectations.append(float(np.dot(probabilities, signs)))
    return np.asarray(expectations)


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
    exact = np.vstack([_z_expectations(state, n_qubits) for state in states])
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
        self.residual_model_ = VariationalQuantumRegressor(
            self.n_qubits,
            self.layers,
            self.regularization,
            self.maximum_optimizer_iterations,
            self.seed,
            self.feature_scale,
            self.entangle,
        ).fit(matrix, targets - baseline)
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "residual_model_"):
            raise RuntimeError("HybridQuantumResidualRegressor is not fitted")
        matrix = _as_matrix(x)
        return matrix[:, self.low_fidelity_column] + self.residual_model_.predict(
            matrix
        )
