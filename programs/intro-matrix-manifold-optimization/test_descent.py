"""Numerical checks for every formula quoted in the article."""

import numpy as np
import pytest
import scipy.linalg

from descent import (
    expm_aherm2,
    gd_additive,
    gd_unitary,
    offdiag_cost_grad,
    polar,
    procrustes_cost_grad,
    rot2,
    s1_gd,
    skew,
)

RNG = np.random.default_rng(0)


def rand_c(*shape):
    return RNG.normal(size=shape) + 1j * RNG.normal(size=shape)


def unitarity_error(U):
    return np.linalg.norm(U.conj().T @ U - np.eye(U.shape[0]))


# --- closed-form 2x2 exponential -------------------------------------------------


@pytest.mark.parametrize("trial", range(20))
def test_expm_aherm2_matches_scipy(trial):
    S = skew(rand_c(2, 2))
    np.testing.assert_allclose(expm_aherm2(S), scipy.linalg.expm(S), atol=1e-12)


def test_expm_aherm2_real_antisymmetric_is_rotation():
    S = 0.7 * np.array([[0.0, -1.0], [1.0, 0.0]])
    np.testing.assert_allclose(expm_aherm2(S), rot2(0.7), atol=1e-12)


def test_expm_aherm2_zero():
    np.testing.assert_allclose(expm_aherm2(np.zeros((2, 2))), np.eye(2), atol=1e-15)


# --- Euclidean gradients via finite differences ----------------------------------


def test_procrustes_gradient_finite_difference():
    A, B, U = rand_c(2, 2), rand_c(2, 2), rand_c(2, 2)
    f0, G = procrustes_cost_grad(U, A, B)
    h = 1e-6
    for _ in range(5):
        dX = rand_c(2, 2)
        fp, _ = procrustes_cost_grad(U + h * dX, A, B)
        fm, _ = procrustes_cost_grad(U - h * dX, A, B)
        num = (fp - fm) / (2 * h)
        ana = np.real(np.trace(G.conj().T @ dX))
        np.testing.assert_allclose(num, ana, rtol=1e-5, atol=1e-6)


def test_offdiag_gradient_finite_difference():
    H = np.array([[2.0, 0.8], [0.8, 1.0]])
    Q = RNG.normal(size=(2, 2))
    _, G = offdiag_cost_grad(Q, H)
    h = 1e-6
    for _ in range(5):
        dX = RNG.normal(size=(2, 2))
        fp, _ = offdiag_cost_grad(Q + h * dX, H)
        fm, _ = offdiag_cost_grad(Q - h * dX, H)
        num = (fp - fm) / (2 * h)
        ana = np.trace(G.T @ dX)
        np.testing.assert_allclose(num, ana, rtol=1e-5, atol=1e-8)


# --- multiplicative updates stay on the manifold ----------------------------------


def test_unitarity_preserved_over_many_iterations():
    A, B = rand_c(2, 2), rand_c(2, 2)
    Us = gd_unitary(lambda U: procrustes_cost_grad(U, A, B)[1], np.eye(2), eta=0.05, iters=500)
    assert max(unitarity_error(U) for U in Us) < 1e-13


def test_additive_step_leaves_the_manifold():
    A, B = rand_c(2, 2), rand_c(2, 2)
    Us = gd_additive(lambda U: procrustes_cost_grad(U, A, B)[1], np.eye(2), eta=0.05, iters=200)
    assert unitarity_error(Us[-1]) > 1e-2  # drifts to O(1), not rounding noise


# --- convergence to the known closed-form answers ---------------------------------


def test_procrustes_converges_to_svd_polar_factor():
    A, B = rand_c(2, 2), rand_c(2, 2)
    grad = lambda U: procrustes_cost_grad(U, A, B)[1]
    Us = gd_unitary(grad, np.eye(2), eta=0.05, iters=3000)
    U_opt = polar(B @ A.conj().T)  # exact answer from the Procrustes article
    assert np.linalg.norm(Us[-1] - U_opt) < 1e-6
    fs = [procrustes_cost_grad(U, A, B)[0] for U in Us]
    assert all(f1 <= f0 + 1e-12 for f0, f1 in zip(fs, fs[1:]))  # monotone descent


def test_offdiag_converges_to_eigenvector_frame():
    H = np.array([[2.0, 0.8], [0.8, 1.0]])
    grad = lambda Q: offdiag_cost_grad(np.real(Q), H)[1]
    Qs = gd_unitary(grad, np.eye(2), eta=0.5, iters=200)
    Q = np.real(Qs[-1])
    D = Q.T @ H @ Q
    assert abs(D[0, 1]) < 1e-8
    np.testing.assert_allclose(sorted(np.diag(D)), sorted(np.linalg.eigvalsh(H)), atol=1e-8)


def test_s1_converges_to_polar_factor_of_b():
    b = 1.5 * np.exp(1j * 2.4)
    zs = s1_gd(b, np.exp(-1j * 2.0), eta=0.2, iters=100)
    assert abs(zs[-1] - b / abs(b)) < 1e-8
    assert all(abs(abs(z) - 1) < 1e-14 for z in zs)  # never leaves the circle
