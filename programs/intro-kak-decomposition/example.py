"""Worked examples: print the Cartan parameters and round-trip error for
each of the four chamber loci (Identity, CNOT, sqrt(CNOT), SWAP) plus a
Haar-random SU(4) input.
"""

from __future__ import annotations

import numpy as np

from kak import (
    CNOT,
    SWAP,
    equal_up_to_phase,
    kak_decompose,
    random_unitary,
    sqrt_cnot,
)


def report(name: str, U: np.ndarray) -> None:
    res = kak_decompose(U)
    U_rec = res.reconstruct()
    # Strip the global phase before measuring agreement: U = e^{i phi} U_rec.
    idx = np.unravel_index(int(np.argmax(np.abs(U_rec))), U_rec.shape)
    phase = U[idx] / U_rec[idx]
    err = np.max(np.abs(U - phase * U_rec))
    matches = equal_up_to_phase(U, U_rec)
    print(
        f"{name:>18s}: (cx, cy, cz) = "
        f"({res.cx:+.10f}, {res.cy:+.10f}, {res.cz:+.10f})    "
        f"max|U - phi U_rec| = {err:.2e}    up_to_phase = {matches}"
    )


def main() -> None:
    print("Locus probes:")
    report("Identity", np.eye(4, dtype=complex))
    report("CNOT", CNOT)
    report("sqrt(CNOT)", sqrt_cnot())
    # SWAP itself has det = -1; multiply by a global phase to land in SU(4).
    report("SWAP * e^{ipi/4}", np.exp(1j * np.pi / 4) * SWAP)
    print()
    print("Haar-random SU(4) probes:")
    for seed in range(5):
        report(f"random[seed={seed}]", random_unitary(4, seed=seed))


if __name__ == "__main__":
    main()
