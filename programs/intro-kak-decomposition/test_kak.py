"""Tests for `kak_decompose`.

Pinned cases:
- Identity, CNOT, SWAP, sqrt(CNOT) -> Cartan parameters at chamber loci.
- 100 Haar-random SU(4) inputs -> chamber containment + round-trip < 1e-9.
- Dressed Weyl-edge inputs (cx = cy resonance) -> covered by the 2-step
  cluster-restricted eigh path.
- Non-unitary input -> ValueError.
"""

from __future__ import annotations

import numpy as np
import pytest

from kak import (
    CNOT,
    SWAP,
    BOUNDARY_ATOL,
    KAKResult,
    equal_up_to_phase,
    in_reduced_weyl_chamber,
    kak_decompose,
    random_unitary,
    sqrt_cnot,
)


def _check_full_invariants(U: np.ndarray, atol: float = 1e-9) -> KAKResult:
    """Run the decomposition and assert chamber + round-trip + 2x2 factors."""
    res = kak_decompose(U)
    assert in_reduced_weyl_chamber(res.cx, res.cy, res.cz), (
        f"Cartan triple ({res.cx}, {res.cy}, {res.cz}) outside reduced Weyl chamber"
    )
    # Single-qubit factors are 2x2 unitary up to global phase (after det^{1/4}
    # normalisation, the product as a whole agrees with the input up to a
    # global phase).
    for K in (res.k1_left, res.k1_right, res.k2_left, res.k2_right):
        err = np.linalg.norm(K @ K.conj().T - np.eye(2))
        assert err < 1e-8, f"single-qubit factor not unitary: ||K K^dagger - I||_F = {err:.3e}"
    # Round-trip must agree up to a global phase.
    U_rec = res.reconstruct()
    assert equal_up_to_phase(U, U_rec, atol=atol), (
        f"round-trip mismatch: max |U - phi U_rec| = {np.max(np.abs(U - U_rec)):.3e}"
    )
    return res


def test_identity():
    res = _check_full_invariants(np.eye(4, dtype=complex))
    assert abs(res.cx) < BOUNDARY_ATOL
    assert abs(res.cy) < BOUNDARY_ATOL
    assert abs(res.cz) < BOUNDARY_ATOL


def test_cnot():
    res = _check_full_invariants(CNOT)
    assert abs(res.cx - np.pi / 4) < 1e-10
    assert abs(res.cy) < 1e-10
    assert abs(res.cz) < 1e-10


def test_swap():
    # SWAP has det = -1; pre-multiply by a global phase to bring it into U(4).
    res = _check_full_invariants(np.exp(1j * np.pi / 4) * SWAP)
    assert abs(res.cx - np.pi / 4) < 1e-9
    assert abs(res.cy - np.pi / 4) < 1e-9
    assert abs(res.cz - np.pi / 4) < 1e-9


def test_sqrt_cnot():
    res = _check_full_invariants(sqrt_cnot())
    assert abs(res.cx - np.pi / 8) < 1e-10
    assert abs(res.cy) < 1e-10
    assert abs(res.cz) < 1e-10


@pytest.mark.parametrize("seed", range(100))
def test_random_su4(seed: int):
    U = random_unitary(4, seed=seed)
    _check_full_invariants(U)


def _random_su2(seed: int) -> np.ndarray:
    return random_unitary(2, seed=seed)


@pytest.mark.parametrize("seed", range(20))
def test_dressed_resonance_cx_eq_cy(seed: int):
    """Dressed inputs on the cx = cy = pi/8 resonance ridge.

    These hit the 2-step eigh path at the H1 3-fold degeneracy point that
    motivated the cluster-restricted simultaneous diagonalization.
    """
    from kak import B  # noqa: PLC0415

    rng = np.random.default_rng(seed)
    cz = rng.uniform(-np.pi / 8, np.pi / 8)
    d_magic = np.array(
        [
            np.pi / 8 - np.pi / 8 + cz,  # cx - cy + cz
            -np.pi / 8 + np.pi / 8 + cz,  # -cx + cy + cz
            np.pi / 8 + np.pi / 8 - cz,  # cx + cy - cz
            -np.pi / 8 - np.pi / 8 - cz,  # -cx - cy - cz
        ]
    )
    Ud = B @ np.diag(np.exp(1j * d_magic)) @ B.conj().T
    K1L = _random_su2(seed)
    K1R = _random_su2(seed + 1000)
    K2L = _random_su2(seed + 2000)
    K2R = _random_su2(seed + 3000)
    U = np.kron(K1L, K1R) @ Ud @ np.kron(K2L, K2R)
    _check_full_invariants(U, atol=1e-8)


def test_non_unitary_input_rejected():
    with pytest.raises(ValueError, match="not unitary"):
        kak_decompose(np.eye(4) + 0.1)


def test_wrong_shape_rejected():
    with pytest.raises(ValueError, match=r"expected"):
        kak_decompose(np.eye(2, dtype=complex))


def test_slot_encoding_self_consistency():
    """Sanity check: slot encoding agrees with B^dagger XX/YY/ZZ B diagonals."""
    from kak import B, X, Y, Z  # noqa: PLC0415

    XX = np.kron(X, X)
    YY = np.kron(Y, Y)
    ZZ = np.kron(Z, Z)
    Bdag = B.conj().T
    dxx = np.diag(Bdag @ XX @ B).real
    dyy = np.diag(Bdag @ YY @ B).real
    dzz = np.diag(Bdag @ ZZ @ B).real
    np.testing.assert_allclose(dxx, [+1, -1, +1, -1], atol=1e-12)
    np.testing.assert_allclose(dyy, [-1, +1, +1, -1], atol=1e-12)
    np.testing.assert_allclose(dzz, [+1, +1, -1, -1], atol=1e-12)
