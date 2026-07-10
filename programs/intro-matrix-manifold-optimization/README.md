# intro-matrix-manifold-optimization

Companion code for the Zenn article 「手を動かして学ぶ行列多様体上の最適化入門」.

- `descent.py` — multiplicative (Lie-algebra) gradient descent on U(2)/O(2)/S^1, plus the additive and retraction-based baselines and the cost functions used in the article.
- `figures.py` — regenerates the article figures into `../../images/intro-matrix-manifold-optimization/`.
- `test_descent.py` — numerical checks for every formula quoted in the article: gradients against finite differences, the closed-form 2x2 `expm` against `scipy.linalg.expm`, unitarity preservation, and convergence to the closed-form answers (SVD polar factor, eigenvector frame).

Run the tests:

```sh
uv run --group dev pytest
```

Regenerate the figures:

```sh
uv run --group viz python figures.py
```
