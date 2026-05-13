# intro-kak-decomposition

PoC implementation of KAK (Weyl) decomposition for 2-qubit unitary gates,
companion to the Zenn article *KAK分解入門*.

## Run

```sh
uv sync
uv run python example.py     # worked examples (CNOT, SWAP, sqrt(CNOT), random)
uv run pytest -q              # full test suite
```

## Files

- `kak.py` — implementation
  - magic basis $\mathcal{B}$
  - `_simultaneous_eigenbasis` — 2-step Hermitian trick with cluster-restricted second `eigh`
  - `_decompose_product` — tensor-product splitting $K = A \otimes B$
  - `_weyl_reduce` — Weyl chamber reduction (port of Cirq's `kak_canonicalize_vector`)
  - `kak_decompose` — top-level entry point with diagonal-M bypass
- `test_kak.py` — pinned chamber loci + 100 Haar-random + dressed resonance + error paths
- `example.py` — print Cartan parameters and round-trip error for representative inputs

## Algorithm steps

1. SU(4) normalization: $U \leftarrow U / \det(U)^{1/4}$
2. Magic-basis transform: $M = \mathcal{B}^\dagger U \mathcal{B}$
3. $N = M^T M$ (transpose, not adjoint); $N$ is symmetric unitary
4. Hermitian trick: $H_1 = \mathrm{Re}(N) + \mathrm{Im}(N)$ -> first `eigh`
5. Cluster-restricted second `eigh` on $H_2 = \mathrm{Re}(N) - \mathrm{Im}(N)$ within each $H_1$ eigenvalue cluster -> $V$
6. Slot encoding: $d_k = \arg((V^\dagger N V)_{kk})/2$, then $c_x = (d_0 + d_2)/2$ etc.
7. Reconstruct $K_1 = \mathcal{B} M V D^{-1} \mathcal{B}^\dagger$, $K_2 = \mathcal{B} V^T \mathcal{B}^\dagger$
8. Tensor-product split $K = A \otimes B$ via pivot
9. Weyl-chamber reduction (Cirq-style shift / sort / negate / half-edge tiebreak)

A `diagonal-M bypass` short-circuits steps 4-5 when $M$ is already diagonal
in the magic basis (canonical-equivalent inputs, SWAP vertex, Weyl-chamber
edges) — the eigh path is unstable in that regime.

## References

- F. Vatan, C. Williams, *Phys. Rev. A* **69**, 032315 (2004). arXiv: quant-ph/0308006
- Cirq `kak_canonicalize_vector` (Apache-2.0)
- Qiskit `TwoQubitWeylDecomposition`
