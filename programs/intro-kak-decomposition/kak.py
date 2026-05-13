"""KAK decomposition for 2-qubit unitary gates.

Decomposes any U in SU(4) into

    U = (K1L o K1R) . exp(i (cx XX + cy YY + cz ZZ)) . (K2L o K2R)

where K_iL, K_iR in SU(2) are single-qubit gates and (cx, cy, cz) are the
canonical (Weyl) parameters living in the reduced Weyl chamber

    pi/4 >= cx >= cy >= |cz| >= 0,   cz >= 0 if cx = pi/4.

Algorithm: Qiskit-style Weyl decomposition via magic basis, with the
cluster-restricted 2-step `eigh` trick from cirq for handling the
degenerate-eigenspace case.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import eigh

# Pauli matrices.
I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)

# Magic basis (Qiskit convention). Columns are entangled Bell-state variants;
# the matrix is unitary.
B = (1 / np.sqrt(2)) * np.array(
    [
        [1, 1j, 0, 0],
        [0, 0, 1j, 1],
        [0, 0, 1j, -1],
        [1, -1j, 0, 0],
    ],
    dtype=complex,
)

# Cluster gap thresholds for the 2-step eigh restriction. Sized to capture
# both the truly-degenerate case and the regime where eigh's eigenvector
# accuracy degrades (eigenvector error ~ ulp * ||A|| / gap).
CLUSTER_REL_TOL = 1e-4
CLUSTER_ABS_FLOOR = 1e-12

# Boundary tolerance for the cx = pi/4 half-edge tiebreak. Empirically
# validated against the cytnx LAPACK backend (see article footnotes).
BOUNDARY_ATOL = 100.0 * np.finfo(float).eps / CLUSTER_REL_TOL  # ~ 2.2e-10

UNITARY_TOL = 1e-8
DIAG_TOL = 1e-10


@dataclass
class KAKResult:
    """Result of `kak_decompose`. K = K1L ⊗ K1R style."""

    cx: float
    cy: float
    cz: float
    k1_left: np.ndarray  # 2x2
    k1_right: np.ndarray  # 2x2
    k2_left: np.ndarray  # 2x2
    k2_right: np.ndarray  # 2x2

    def reconstruct(self) -> np.ndarray:
        """Reconstruct U = (K1L o K1R) . exp(i Hc) . (K2L o K2R)."""
        Hc = self.cx * np.kron(X, X) + self.cy * np.kron(Y, Y) + self.cz * np.kron(Z, Z)
        # Diagonalize Hc analytically via magic basis: B^dagger Hc B is diagonal.
        d_magic = np.array(
            [
                self.cx - self.cy + self.cz,
                -self.cx + self.cy + self.cz,
                self.cx + self.cy - self.cz,
                -self.cx - self.cy - self.cz,
            ]
        )
        Ud = B @ np.diag(np.exp(1j * d_magic)) @ B.conj().T
        K1 = np.kron(self.k1_left, self.k1_right)
        K2 = np.kron(self.k2_left, self.k2_right)
        return K1 @ Ud @ K2


# ---------------------------------------------------------------------------
# Step 4-helpers: simultaneous diagonalization of N = M^T M.
# ---------------------------------------------------------------------------


def _find_eigenvalue_clusters(eigenvalues: np.ndarray) -> list[list[int]]:
    """Group sorted eigenvalues into near-degenerate clusters.

    Returns a list of clusters, each a list of original (pre-sort) column
    indices into the eigenvector matrix.
    """
    order = np.argsort(eigenvalues)
    clusters: list[list[int]] = [[int(order[0])]]
    for k in range(1, len(order)):
        a = float(eigenvalues[order[k - 1]])
        b = float(eigenvalues[order[k]])
        thresh = max(CLUSTER_REL_TOL * max(abs(a), abs(b)), CLUSTER_ABS_FLOOR)
        if abs(a - b) < thresh:
            clusters[-1].append(int(order[k]))
        else:
            clusters.append([int(order[k])])
    return clusters


def _simultaneous_eigenbasis(N: np.ndarray) -> np.ndarray:
    """Compute V such that V^T N V is diagonal with N symmetric unitary.

    Uses the 2-step Hermitian trick:
      H1 = Re(N) + Im(N) (real symmetric) -> first eigh -> V_tmp
      H2 = Re(N) - Im(N), restricted to each H1 eigenvalue cluster -> R
      V = V_tmp @ R.

    The cluster restriction is essential at points where H1 has a degenerate
    block: a global second eigh would mix V_tmp columns across H1 blocks and
    fail to simultaneously diagonalize.
    """
    H1 = (N.real + N.imag).astype(float)
    H2 = (N.real - N.imag).astype(float)

    eigvals, V_tmp = eigh(H1)  # V_tmp is real orthogonal.
    clusters = _find_eigenvalue_clusters(eigvals)

    R = np.eye(4, dtype=complex)
    for cluster in clusters:
        if len(cluster) < 2:
            continue
        idx = np.array(cluster)
        Vg = V_tmp[:, idx]  # 4 x m
        H2_g = Vg.T @ H2 @ Vg  # m x m, real symmetric (up to ulp noise).
        H2_g = 0.5 * (H2_g + H2_g.T)  # enforce exact symmetry.
        _, Rg = eigh(H2_g)
        # Scatter Rg into the (cluster x cluster) block of R, overwriting the
        # identity placed there at construction.
        for a, ia in enumerate(cluster):
            for b, ib in enumerate(cluster):
                R[ia, ib] = Rg[a, b]
    return V_tmp.astype(complex) @ R


def _phase_normalize_columns(V: np.ndarray) -> np.ndarray:
    """Make each column real by removing the phase of its largest entry."""
    V = V.copy()
    for c in range(V.shape[1]):
        idx = int(np.argmax(np.abs(V[:, c])))
        if abs(V[idx, c]) <= 1e-14:
            continue
        phase_corr = np.conj(V[idx, c]) / abs(V[idx, c])
        V[:, c] *= phase_corr
    return V


def _enforce_so4(V: np.ndarray) -> np.ndarray:
    """Negate column 0 if det(V) < 0 so V in SO(4)."""
    if np.linalg.det(V).real >= 0:
        return V
    V = V.copy()
    V[:, 0] *= -1
    return V


# ---------------------------------------------------------------------------
# Step 7: tensor-product decomposition K = A o B for K in SU(2) o SU(2).
# ---------------------------------------------------------------------------


def _decompose_product(K: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Find A, B with K = A ⊗ B given that K is a tensor product."""
    # K[2i+j, 2k+l] = A[i,k] * B[j,l]; pick the largest entry as pivot.
    ar, ac = np.unravel_index(int(np.argmax(np.abs(K))), K.shape)
    bi, bk = ar // 2, ac // 2
    # Extract B (up to scale) from the (bi, bk) block.
    B_raw = K[2 * bi : 2 * bi + 2, 2 * bk : 2 * bk + 2].copy()
    # Pivot inside B for numerical stability when extracting A.
    bj, bl = np.unravel_index(int(np.argmax(np.abs(B_raw))), B_raw.shape)
    bp = B_raw[bj, bl]
    A = K[bj::2, bl::2] / bp
    # Renormalize so A o B = K exactly.
    a_pivot = A[bi, bk]
    B_out = B_raw / a_pivot
    # Make each factor unitary. A_ext = A_true / c (with c = A_true[bi, bk]),
    # so ||A_ext||_F^2 = 2/|c|^2; rescaling by ||A_ext||_F / sqrt(2) brings
    # A_ext's columns to unit norm. The reciprocal scalar absorbs into B so
    # A_final ⊗ B_final = K is preserved.
    scale = np.linalg.norm(A, ord="fro") / np.sqrt(2)
    return A / scale, B_out * scale


# ---------------------------------------------------------------------------
# Step 8: Weyl-chamber reduction (port of Cirq's `kak_canonicalize_vector`).
# ---------------------------------------------------------------------------


def _i_pauli(k: int) -> np.ndarray:
    """i*sigma_k for k in {0,1,2}."""
    return 1j * [X, Y, Z][k]


def _i_pauli_pow(k: int, step: int) -> np.ndarray:
    step = step % 4
    out = np.eye(2, dtype=complex)
    base = _i_pauli(k)
    for _ in range(step):
        out = base @ out
    return out


def _swapper(idx: int) -> np.ndarray:
    """Single-qubit Clifford that swaps two Cartan axes by conjugation.

    `idx` is the third axis (the one held fixed): pass 3 - k1 - k2 for a
    swap of axes k1, k2. Each swapper is i*sqrt(1/2) * M with M an
    involutive Pauli mixer; the resulting matrix is in SU(2).
    """
    f = 1j / np.sqrt(2)
    if idx == 0:  # swap y,z
        return f * np.array([[1, -1j], [1j, -1]], dtype=complex)
    if idx == 1:  # swap x,z
        return f * np.array([[1, 1], [1, -1]], dtype=complex)
    if idx == 2:  # swap x,y
        return f * np.array([[0, 1 - 1j], [1 + 1j, 0]], dtype=complex)
    raise ValueError(idx)


@dataclass
class _WeylState:
    v: np.ndarray  # shape (3,)
    k1l: np.ndarray
    k1r: np.ndarray
    k2l: np.ndarray
    k2r: np.ndarray


def _weyl_shift(s: _WeylState, k: int, step: int) -> None:
    s.v[k] += step * (np.pi / 2)
    sp = _i_pauli_pow(k, step)
    s.k2l = sp @ s.k2l
    s.k2r = sp @ s.k2r


def _weyl_negate(s: _WeylState, k1: int, k2: int) -> None:
    s.v[k1] = -s.v[k1]
    s.v[k2] = -s.v[k2]
    k3 = 3 - k1 - k2
    sp = _i_pauli(k3)
    s.k1l = s.k1l @ sp  # right-multiply on after-side
    s.k2l = sp @ s.k2l  # left-multiply on before-side


def _weyl_swap(s: _WeylState, k1: int, k2: int) -> None:
    s.v[k1], s.v[k2] = s.v[k2], s.v[k1]
    sp = _swapper(3 - k1 - k2)
    s.k1l = s.k1l @ sp
    s.k1r = s.k1r @ sp
    s.k2l = sp @ s.k2l
    s.k2r = sp @ s.k2r


def _weyl_canonical_shift(s: _WeylState, k: int) -> None:
    while s.v[k] <= -np.pi / 4:
        _weyl_shift(s, k, +1)
    while s.v[k] > np.pi / 4:
        _weyl_shift(s, k, -1)


def _weyl_sort(s: _WeylState) -> None:
    if abs(s.v[0]) < abs(s.v[1]):
        _weyl_swap(s, 0, 1)
    if abs(s.v[1]) < abs(s.v[2]):
        _weyl_swap(s, 1, 2)
    if abs(s.v[0]) < abs(s.v[1]):
        _weyl_swap(s, 0, 1)


def _weyl_reduce(
    cx: float,
    cy: float,
    cz: float,
    k1l: np.ndarray,
    k1r: np.ndarray,
    k2l: np.ndarray,
    k2r: np.ndarray,
) -> tuple[float, float, float, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    s = _WeylState(np.array([cx, cy, cz], dtype=float), k1l, k1r, k2l, k2r)
    _weyl_canonical_shift(s, 0)
    _weyl_canonical_shift(s, 1)
    _weyl_canonical_shift(s, 2)
    _weyl_sort(s)
    if s.v[0] < 0:
        _weyl_negate(s, 0, 2)
    if s.v[1] < 0:
        _weyl_negate(s, 1, 2)
    _weyl_canonical_shift(s, 2)
    if s.v[0] > np.pi / 4 - BOUNDARY_ATOL and s.v[2] < 0:
        _weyl_shift(s, 0, -1)
        _weyl_negate(s, 0, 2)
    return float(s.v[0]), float(s.v[1]), float(s.v[2]), s.k1l, s.k1r, s.k2l, s.k2r


# ---------------------------------------------------------------------------
# Main entry point.
# ---------------------------------------------------------------------------


def kak_decompose(U: np.ndarray) -> KAKResult:
    """Compute the KAK (Weyl) decomposition of a 4x4 unitary.

    Raises ValueError if U is not unitary within UNITARY_TOL.
    """
    U = np.asarray(U, dtype=complex)
    if U.shape != (4, 4):
        raise ValueError(f"expected (4, 4), got {U.shape}")
    err = np.linalg.norm(U @ U.conj().T - np.eye(4))
    if err > UNITARY_TOL:
        raise ValueError(f"not unitary: ||U U^dagger - I||_F = {err:.3e}")

    # SU(4) normalization: U /= det(U)^(1/4).
    U = U / np.linalg.det(U) ** 0.25

    # Magic-basis transform.
    M = B.conj().T @ U @ B

    # N = M^T M (transpose, not adjoint).
    N = M.T @ M

    # Step 4: simultaneous eigenbasis of N (and N^dagger).
    if np.max(np.abs(M - np.diag(np.diag(M)))) < DIAG_TOL:
        # Diagonal-M bypass: handles SWAP vertex (N propto I) and Weyl-chamber
        # edges (cx = cy etc.) where the 2-step eigh path leaves a degenerate
        # subspace ambiguous.
        V = np.eye(4, dtype=complex)
        d = np.angle(np.diag(M))
    else:
        V = _simultaneous_eigenbasis(N)
        V = _phase_normalize_columns(V)
        V = _enforce_so4(V)
        # General path: d_k = arg((V^dagger N V)[k,k]) / 2, with branch
        # correction to keep det(D) = +1.
        VNV = V.conj().T @ N @ V
        d = np.angle(np.diag(VNV)) / 2
        if np.cos(d.sum()) < 0:
            d[0] += np.pi

    # Step 5: Cartan parameters from slot encoding pair-sums.
    cx = (d[0] + d[2]) / 2
    cy = (d[1] + d[2]) / 2
    cz = (d[0] + d[1]) / 2

    # Step 6: reconstruct K1, K2 in computational basis.
    D_inv = np.diag(np.exp(-1j * d))
    K2 = B @ V.T @ B.conj().T
    K1 = B @ (M @ V @ D_inv) @ B.conj().T

    # Step 7: tensor-product decomposition.
    k1l, k1r = _decompose_product(K1)
    k2l, k2r = _decompose_product(K2)

    # Step 8: Weyl-chamber reduction (absorbs Cliffords into the 2x2 factors).
    cx, cy, cz, k1l, k1r, k2l, k2r = _weyl_reduce(cx, cy, cz, k1l, k1r, k2l, k2r)

    return KAKResult(cx, cy, cz, k1l, k1r, k2l, k2r)


# ---------------------------------------------------------------------------
# Helpers for tests / examples.
# ---------------------------------------------------------------------------


CNOT = np.array(
    [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ],
    dtype=complex,
)

SWAP = np.array(
    [
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ],
    dtype=complex,
)


def sqrt_cnot() -> np.ndarray:
    """sqrt(CNOT) via spectral decomposition."""
    eigvals, eigvecs = np.linalg.eig(CNOT)
    return eigvecs @ np.diag(np.sqrt(eigvals.astype(complex))) @ np.linalg.inv(eigvecs)


def random_unitary(n: int, seed: int | None = None) -> np.ndarray:
    """Random unitary via QR of a complex Ginibre matrix."""
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    Q, R = np.linalg.qr(A)
    # Fix QR sign ambiguity to produce Haar-random Q.
    D = np.diag(R) / np.abs(np.diag(R))
    return Q @ np.diag(D)


def equal_up_to_phase(A: np.ndarray, B: np.ndarray, atol: float = 1e-9) -> bool:
    """Check A == e^{i phi} B for some phi."""
    # Find an entry with non-trivial magnitude to read off the phase.
    idx = np.unravel_index(int(np.argmax(np.abs(B))), B.shape)
    if abs(B[idx]) < 1e-12:
        return np.allclose(A, B, atol=atol)
    phase = A[idx] / B[idx]
    return np.allclose(A, phase * B, atol=atol)


def in_reduced_weyl_chamber(
    cx: float, cy: float, cz: float, atol: float = 1e-9
) -> bool:
    """Check (cx, cy, cz) in pi/4 >= cx >= cy >= |cz| >= 0 (with cx <=
    pi/4 + boundary atol; cz >= 0 if cx = pi/4)."""
    if not all(np.isfinite([cx, cy, cz])):
        return False
    if cx < -atol or cy < -atol:
        return False
    if cx > np.pi / 4 + BOUNDARY_ATOL + atol:
        return False
    if cy > cx + atol:
        return False
    if abs(cz) > cy + atol:
        return False
    if abs(cx - np.pi / 4) < BOUNDARY_ATOL + atol and cz < -atol:
        return False
    return True
