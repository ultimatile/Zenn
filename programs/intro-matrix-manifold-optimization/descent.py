"""Riemannian gradient descent on S^1, O(2), U(2) via Lie-algebra updates.

Companion code for the Zenn article
「手を動かして学ぶ行列多様体上の最適化入門」.

The central update is multiplicative:

    U <- expm(-eta * S) @ U,   S = skew(G @ U^dagger) in u(n),

where G is the Euclidean gradient of the cost (df = Re tr(G^dagger dU)).
Because expm of an anti-Hermitian matrix is exactly unitary, the iterate
never leaves the manifold, regardless of step size or iteration count.
"""

from __future__ import annotations

import numpy as np

I2 = np.eye(2)
# Generator of so(2): expm(t*J) is the rotation by angle t.
J = np.array([[0.0, -1.0], [1.0, 0.0]])


def skew(M: np.ndarray) -> np.ndarray:
    """Anti-Hermitian part of M, i.e. the projection onto u(n) w.r.t. Re<.,.>."""
    return (M - M.conj().T) / 2


def rot2(t: float) -> np.ndarray:
    """expm(t*J): the 2x2 rotation matrix by angle t."""
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s], [s, c]])


def expm_aherm2(S: np.ndarray) -> np.ndarray:
    """Closed-form matrix exponential of a 2x2 anti-Hermitian S.

    Split S = i*a*I + T with a real and T traceless anti-Hermitian.
    Then T @ T = -theta^2 * I, which gives the 2x2 Euler formula
    exp(T) = cos(theta) I + (sin(theta)/theta) T, and exp(S) = e^{ia} exp(T).
    Works for real antisymmetric S as well (then a = 0 and exp(S) = rot2).
    """
    S = np.asarray(S, dtype=complex)
    a = (S[0, 0] + S[1, 1]).imag / 2
    T = S - 1j * a * np.eye(2)
    theta = np.sqrt(max(-(T @ T)[0, 0].real, 0.0))
    # np.sinc(x) = sin(pi x)/(pi x), so sinc(theta/pi) = sin(theta)/theta (=1 at 0).
    return np.exp(1j * a) * (np.cos(theta) * np.eye(2) + np.sinc(theta / np.pi) * T)


def gd_unitary(grad, U0: np.ndarray, eta: float = 0.1, iters: int = 200) -> list[np.ndarray]:
    """Multiplicative gradient descent on U(2)/O(2); returns all iterates.

    grad(U) must return the Euclidean gradient G at U. For n > 2 replace
    expm_aherm2 by scipy.linalg.expm; the update formula is unchanged.
    """
    Us = [np.asarray(U0, dtype=complex)]
    for _ in range(iters):
        U = Us[-1]
        S = skew(grad(U) @ U.conj().T)
        Us.append(expm_aherm2(-eta * S) @ U)
    return Us


def gd_additive(grad, U0: np.ndarray, eta: float = 0.1, iters: int = 200, retract=None) -> list[np.ndarray]:
    """Additive gradient descent U <- U - eta*G, optionally retracted back.

    retract=None reproduces the naive unconstrained step (leaves the manifold);
    retract=polar re-projects onto U(n) after each step (projection retraction).
    """
    Us = [np.asarray(U0, dtype=complex)]
    for _ in range(iters):
        U = Us[-1] - eta * grad(Us[-1])
        Us.append(U if retract is None else retract(U))
    return Us


def polar(M: np.ndarray) -> np.ndarray:
    """Unitary polar factor of M: the closest unitary matrix to M."""
    W, _, Vh = np.linalg.svd(M)
    return W @ Vh


# --- costs used in the article -------------------------------------------------


def procrustes_cost_grad(U: np.ndarray, A: np.ndarray, B: np.ndarray):
    """Unitary Procrustes cost f(U) = ||U A - B||_F^2 and its gradient 2(UA-B)A^dagger."""
    R = U @ A - B
    return np.sum(np.abs(R) ** 2), 2 * R @ A.conj().T


def offdiag_cost_grad(Q: np.ndarray, H: np.ndarray):
    """Diagonalization cost f(Q) = (1/4)||offdiag(Q^T H Q)||_F^2, gradient H Q E.

    H must be real symmetric and Q real (an O(2) frame); E := offdiag(Q^T H Q).
    """
    Aq = Q.T @ H @ Q
    E = Aq - np.diag(np.diag(Aq))
    return 0.25 * np.sum(E**2), H @ Q @ E


def s1_gd(b: complex, z0: complex, eta: float = 0.2, iters: int = 40) -> list[complex]:
    """Gradient descent of f(z) = |z - b|^2 on the unit circle; returns iterates.

    The scalar case of the multiplicative update: G = 2(z - b),
    S = skew(G * conj(z)) = i Im(G conj(z)), z <- exp(-eta*S) * z.
    """
    zs = [z0]
    for _ in range(iters):
        z = zs[-1]
        G = 2 * (z - b)
        S = 1j * (G * np.conj(z)).imag
        zs.append(np.exp(-eta * S) * z)
    return zs
