"""Generate the article figures into ../../images/intro-matrix-manifold-optimization/.

Run: uv run --group viz python figures.py

Series identity is kept consistent across figures:
  blue = multiplicative (Lie-algebra exp) update, aqua = retraction-based update,
  red = naive additive update (leaves the manifold).
Iteration progress is encoded with a light->dark one-hue ramp (blue for the
iterate/first column, aqua for the second frame column).
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from descent import (
    gd_additive,
    gd_unitary,
    offdiag_cost_grad,
    polar,
    procrustes_cost_grad,
    rot2,
    s1_gd,
)

OUT = pathlib.Path(__file__).resolve().parents[2] / "images" / "intro-matrix-manifold-optimization"

BLUE, AQUA, RED = "#2a78d6", "#1baf7a", "#e34948"
INK, SEC, MUT = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUES = LinearSegmentedColormap.from_list(
    "blues", ["#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
)
AQUAS = LinearSegmentedColormap.from_list("aquas", ["#8fdec0", "#3cc492", "#1baf7a", "#0f7a54", "#08533a"])

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.labelcolor": SEC,
        "axes.titlecolor": INK,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.color": MUT,
        "ytick.color": MUT,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "font.size": 10,
        "mathtext.fontset": "dejavusans",
    }
)

# Shared S^1 problem instance: f(z) = |z - b|^2 on |z| = 1. The start point is
# placed ~145 deg away from the optimum so single steps are large enough to see.
B_TARGET = 1.4 * np.exp(1j * np.deg2rad(-25))
Z0 = np.exp(1j * np.deg2rad(120))


def clean_geometry_axes(ax, lim=1.75):
    ax.set_aspect("equal")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axhline(0, color=GRID, lw=0.8, zorder=0)
    ax.axvline(0, color=GRID, lw=0.8, zorder=0)


def draw_circle(ax, color=AXIS, lw=1.4):
    t = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(t), np.sin(t), color=color, lw=lw, zorder=1)


def arrow(ax, p, q, color, lw=1.8, ls="-", zorder=5, mutation=13):
    ax.annotate(
        "",
        xy=(q.real, q.imag),
        xytext=(p.real, p.imag),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, linestyle=ls, mutation_scale=mutation, shrinkA=0, shrinkB=0),
        zorder=zorder,
    )


def draw_arc(ax, a0, a1, color, lw=2.0, r=1.0, zorder=6):
    """Arc on the circle of radius r from angle a0 to a1, with an arrowhead at the end."""
    t = np.linspace(a0, a1, 60)
    ax.plot(r * np.cos(t[:-1]), r * np.sin(t[:-1]), color=color, lw=lw, zorder=zorder, solid_capstyle="round")
    p, q = r * np.exp(1j * t[-2]), r * np.exp(1j * t[-1])
    arrow(ax, p, q, color, lw=lw, zorder=zorder)


def fig1_two_steps():
    """(a) additive step + projection back vs (b) tangent projection + exp step."""
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.9))
    eta = 0.25  # large on purpose, so the off-manifold drift is visible
    z = Z0
    G = 2 * (z - B_TARGET)  # Euclidean gradient of |z-b|^2
    w = z - eta * G  # naive additive step (lands off the circle)

    for ax in axes:
        clean_geometry_axes(ax)
        draw_circle(ax)
        ax.plot(z.real, z.imag, "o", ms=8, color=INK, zorder=7)
        ax.annotate("$z$", (z.real, z.imag), textcoords="offset points", xytext=(-15, 5), color=INK, fontsize=12)

    # (a) naive additive step, then pull back onto the circle.
    ax = axes[0]
    ax.plot(B_TARGET.real, B_TARGET.imag, marker="*", ms=13, color=SEC, zorder=6)
    ax.annotate("$b$", (B_TARGET.real, B_TARGET.imag), textcoords="offset points", xytext=(8, 2), color=SEC, fontsize=11)
    arrow(ax, z, w, RED)
    ax.plot(w.real, w.imag, "o", ms=8, mfc="white", mec=RED, mew=1.8, zorder=6)
    ax.annotate("$w=z-\\eta\\nabla f$", (w.real, w.imag), textcoords="offset points", xytext=(4, -16), color=RED, fontsize=11)
    wn = w / abs(w)
    arrow(ax, w, wn, AQUA, ls="--", lw=1.6)
    ax.plot(wn.real, wn.imag, "o", ms=8, color=AQUA, zorder=6)
    ax.annotate("$w/|w|$", (wn.real, wn.imag), textcoords="offset points", xytext=(4, 8), color=AQUA, fontsize=11)
    ax.set_title("(a) additive step, then project back", color=SEC)

    # (b) project the gradient onto the tangent line, walk along the circle by exp.
    ax = axes[1]
    th0 = np.angle(z)
    tangent = 1j * z  # unit tangent at z
    # tangent lines at the identity 1 and at z (the translated copy of u(1))
    s = np.linspace(-0.7, 0.7, 2)
    ax.plot(1 + 0 * s, s, color=AXIS, lw=1.0, ls=":", zorder=2)
    ax.plot([1], [0], "o", ms=5, mfc="white", mec=MUT, mew=1.2, zorder=4)
    ax.annotate("$1$", (1, 0), textcoords="offset points", xytext=(6, -12), color=MUT, fontsize=11)
    ax.annotate("$T_1S^1=\\mathfrak{u}(1)$", (1.06, -0.62), color=MUT, fontsize=10)
    line = z + s * tangent
    ax.plot(line.real, line.imag, color=AXIS, lw=1.0, ls=":", zorder=2)
    ax.annotate("$T_zS^1=z\\,\\mathfrak{u}(1)$", (line[-1].real - 0.28, line[-1].imag - 0.3), color=MUT, fontsize=10)
    # full Euclidean gradient step (faint, ties to panel (a)) and its tangential part
    arrow(ax, z, w, RED, ls=":", lw=1.2, mutation=10)
    vtan = np.real(np.conj(tangent) * (-eta * G)) * tangent  # tangential component
    q = z + vtan
    ax.plot([w.real, q.real], [w.imag, q.imag], color=GRID, lw=1.0, ls=":", zorder=3)
    arrow(ax, z, q, BLUE, lw=2.0)
    ax.plot(q.real, q.imag, "o", ms=6, mfc="white", mec=BLUE, mew=1.6, zorder=7)
    ax.annotate("$-\\eta\\,\\mathrm{grad}f(z)$", (0.5 * (z + q).real, 0.5 * (z + q).imag), textcoords="offset points", xytext=(10, 22), color=BLUE, fontsize=11, ha="center")
    # exp step: walk along the circle by the same arc length
    dth = np.real(np.conj(tangent) * (-eta * G))  # = -eta f'(theta)
    draw_arc(ax, th0, th0 + dth, BLUE, lw=2.2)
    zn = np.exp(1j * (th0 + dth))
    ax.plot(zn.real, zn.imag, "o", ms=7, color=BLUE, zorder=7)
    ax.annotate("$\\mathrm{e}^{-\\eta S}z$", (zn.real, zn.imag), textcoords="offset points", xytext=(30, -22), color=BLUE, fontsize=11, ha="center")
    ax.set_title("(b) tangent projection + exp step", color=SEC)

    fig.tight_layout()
    fig.savefig(OUT / "s1-two-steps.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def fig2_s1_descent():
    """(a) iterates on the circle, (b) the same iterates on the angle landscape."""
    eta, iters = 0.15, 25
    zs = np.array(s1_gd(B_TARGET, Z0, eta=eta, iters=iters))
    ks = np.arange(len(zs))
    colors = BLUES(ks / ks[-1])

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4), gridspec_kw={"width_ratios": [1, 1.25]})
    ax = axes[0]
    clean_geometry_axes(ax)
    draw_circle(ax)
    ax.plot(B_TARGET.real, B_TARGET.imag, marker="*", ms=13, color=SEC, zorder=6)
    ax.annotate("$b$", (B_TARGET.real, B_TARGET.imag), textcoords="offset points", xytext=(8, 2), color=SEC, fontsize=11)
    zopt = B_TARGET / abs(B_TARGET)
    ax.plot(zopt.real, zopt.imag, "o", ms=12, mfc="none", mec=SEC, mew=1.4, zorder=6)
    ax.annotate("$b/|b|$", (zopt.real, zopt.imag), textcoords="offset points", xytext=(-14, 14), color=SEC, fontsize=11)
    ax.scatter(zs.real, zs.imag, c=colors, s=26, zorder=5)
    ax.annotate("$z_0$", (zs[0].real, zs[0].imag), textcoords="offset points", xytext=(-16, 6), color=BLUES(0.2), fontsize=11)
    ax.set_title("(a) iterates on $S^1$", color=SEC)

    ax = axes[1]
    th = np.linspace(-np.pi, np.pi, 500)
    f = np.abs(np.exp(1j * th) - B_TARGET) ** 2
    ax.plot(th, f, color=MUT, lw=1.8, zorder=2)
    ths = np.angle(zs)
    fs = np.abs(zs - B_TARGET) ** 2
    ax.scatter(ths, fs, c=colors, s=26, zorder=5)
    ax.axvline(np.angle(B_TARGET), color=GRID, lw=1.0)
    ax.annotate("$\\theta^*=\\arg b$", (np.angle(B_TARGET), np.max(f) * 0.96), color=MUT, fontsize=10, ha="center")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, axis="y")
    ax.set_xlabel("$\\theta$")
    ax.set_ylabel("$f(\\mathrm{e}^{\\mathrm{i}\\theta})$")
    ax.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi], ["$-\\pi$", "$-\\pi/2$", "$0$", "$\\pi/2$", "$\\pi$"])
    ax.set_title("(b) the same descent, seen in the angle", color=SEC)

    fig.tight_layout()
    fig.savefig(OUT / "s1-descent.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def fig3_o2_diagonalize():
    """(a) frame columns aligning with the principal axes, (b) angle landscape."""
    H = np.array([[2.0, 0.8], [0.8, 1.0]])
    lam, V = np.linalg.eigh(H)  # ascending eigenvalues
    v = V[:, 1] if V[0, 1] > 0 else -V[:, 1]  # leading eigenvector, angle in (-pi/2, pi/2)
    th_star = np.arctan2(v[1], v[0])

    th0 = th_star - np.deg2rad(38)
    Q0 = rot2(th0)
    eta, iters = 0.4, 60
    Qs = [np.real(Q) for Q in gd_unitary(lambda Q: offdiag_cost_grad(np.real(Q), H)[1], Q0, eta=eta, iters=iters)]

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4), gridspec_kw={"width_ratios": [1, 1.25]})
    ax = axes[0]
    clean_geometry_axes(ax, lim=1.45)
    # level set x^T H x = 1: the unit circle mapped through V diag(1/sqrt(lam)) V^T
    t = np.linspace(0, 2 * np.pi, 400)
    pts = (V * (1 / np.sqrt(lam))) @ np.array([np.cos(t), np.sin(t)])
    ax.plot(pts[0], pts[1], color=AXIS, lw=1.4, zorder=1)
    k_lab = 330
    ax.annotate("$x^\\top H x = 1$", (pts[0, k_lab], pts[1, k_lab]), textcoords="offset points", xytext=(20, -12), color=MUT, fontsize=10, ha="center")
    # principal axes
    for j in (0, 1):
        d = V[:, j]
        ax.plot([-1.35 * d[0], 1.35 * d[0]], [-1.35 * d[1], 1.35 * d[1]], color=GRID, lw=1.0, ls="--", zorder=0)
    # frames along the descent
    show = [0, 2, 4, 7, 11, 16, 25, 60]
    for i, k in enumerate(show):
        c1, c2 = BLUES(0.1 + 0.9 * i / (len(show) - 1)), AQUAS(0.1 + 0.9 * i / (len(show) - 1))
        q = Qs[k]
        arrow(ax, 0j, q[0, 0] + 1j * q[1, 0], c1, lw=1.7, mutation=11)
        arrow(ax, 0j, q[0, 1] + 1j * q[1, 1], c2, lw=1.7, mutation=11)
    q = Qs[-1]
    ax.annotate("$q_1$", (q[0, 0] * 1.16, q[1, 0] * 1.16), color=BLUES(1.0), fontsize=11, ha="center", va="center")
    ax.annotate("$q_2$", (q[0, 1] * 1.16, q[1, 1] * 1.16), color=AQUAS(1.0), fontsize=11, ha="center", va="center")
    ax.set_title("(a) frame $Q=(q_1\\ q_2)$ aligning with the axes", color=SEC)

    ax = axes[1]
    th = np.linspace(-np.pi / 2, np.pi / 2, 500)
    fs = [offdiag_cost_grad(rot2(a), H)[0] for a in th]
    ax.plot(th, fs, color=MUT, lw=1.8, zorder=2)
    ths = np.array([np.arctan2(Q[1, 0], Q[0, 0]) for Q in Qs])
    fqs = np.array([offdiag_cost_grad(Q, H)[0] for Q in Qs])
    ks = np.arange(len(Qs))
    ax.scatter(ths, fqs, c=BLUES(0.1 + 0.9 * ks / ks[-1]), s=24, zorder=5)
    for a in (th_star, th_star - np.pi / 2):
        ax.axvline(a, color=GRID, lw=1.0)
    ax.annotate("$\\theta^*$", (th_star, np.max(fs) * 0.96), color=MUT, fontsize=10, ha="center")
    ax.annotate("$\\theta^*-\\pi/2$", (th_star - np.pi / 2, np.max(fs) * 0.96), color=MUT, fontsize=10, ha="center")
    ax.set_xlim(-np.pi / 2, np.pi / 2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, axis="y")
    ax.set_xlabel("$\\theta$ (rotation angle of $Q$)")
    ax.set_ylabel("$f(Q(\\theta))$")
    ax.set_xticks([-np.pi / 2, -np.pi / 4, 0, np.pi / 4, np.pi / 2], ["$-\\pi/2$", "$-\\pi/4$", "$0$", "$\\pi/4$", "$\\pi/2$"])
    ax.set_title("(b) landscape on $SO(2)$: minima every $\\pi/2$", color=SEC)

    fig.tight_layout()
    fig.savefig(OUT / "o2-diagonalize.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def fig4_u2_procrustes():
    """(a) cost curves for the three update rules, (b) unitarity error."""
    rng = np.random.default_rng(7)
    A = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    B = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    grad = lambda U: procrustes_cost_grad(U, A, B)[1]
    eta, iters = 0.15, 120  # same step size as the code snippet in the article
    U0 = np.eye(2)

    runs = [
        ("multiplicative (exp)", gd_unitary(grad, U0, eta=eta, iters=iters), BLUE, "-"),
        ("additive + polar", gd_additive(grad, U0, eta=eta, iters=iters, retract=polar), AQUA, "--"),
        ("additive (naive)", gd_additive(grad, U0, eta=eta, iters=iters), RED, "-"),
    ]
    f_opt = procrustes_cost_grad(polar(B @ A.conj().T), A, B)[0]

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
    ax = axes[0]
    for label, Us, color, ls in runs:
        fs = [procrustes_cost_grad(U, A, B)[0] for U in Us]
        ax.plot(fs, color=color, lw=1.9, ls=ls)
    # direct labels, staggered to avoid the pile-up where two curves coincide
    fs_exp = [procrustes_cost_grad(U, A, B)[0] for U in runs[0][1]]
    ax.annotate("multiplicative (exp)", (iters * 0.25, fs_exp[int(iters * 0.25)]), textcoords="offset points", xytext=(0, 10), color=BLUE, fontsize=9, ha="center")
    ax.annotate("additive + polar", (iters * 0.88, fs_exp[int(iters * 0.88)]), textcoords="offset points", xytext=(0, 10), color=AQUA, fontsize=9, ha="center")
    fs_naive = [procrustes_cost_grad(U, A, B)[0] for U in runs[2][1]]
    ax.annotate("additive (naive)", (iters * 0.7, fs_naive[int(iters * 0.7)]), textcoords="offset points", xytext=(0, -16), color=RED, fontsize=9, ha="center")
    ax.axhline(f_opt, color=MUT, lw=1.2, ls=":")
    ax.annotate("$f(U_{\\mathrm{SVD}})$", (iters * 1.0, f_opt), textcoords="offset points", xytext=(4, -14), color=MUT, fontsize=10)
    ax.set_xlim(0, iters * 1.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, axis="y")
    ax.set_xlabel("iteration $k$")
    ax.set_ylabel("$f(U_k)=\\|U_kA-B\\|_\\mathrm{F}^2$")
    ax.set_title("(a) cost along the three update rules", color=SEC)

    ax = axes[1]
    for label, Us, color, ls in runs:
        errs = np.array([np.linalg.norm(U.conj().T @ U - np.eye(2)) for U in Us])
        ax.semilogy(np.maximum(errs, 1e-16), color=color, lw=1.9, ls=ls)
    ax.annotate("multiplicative (exp)", (iters * 0.42, 1.2e-15), textcoords="offset points", xytext=(0, 10), color=BLUE, fontsize=9, ha="center")
    ax.annotate("additive + polar", (iters * 0.8, 8e-16), textcoords="offset points", xytext=(0, -18), color=AQUA, fontsize=9, ha="center")
    ax.annotate("additive (naive)", (iters * 0.6, 1.6), textcoords="offset points", xytext=(0, 8), color=RED, fontsize=9, ha="center")
    ax.set_xlim(0, iters * 1.3)
    ax.set_ylim(3e-17, 3e1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, axis="y")
    ax.set_xlabel("iteration $k$")
    ax.set_ylabel("$\\|U_k^\\dagger U_k - I\\|_\\mathrm{F}$")
    ax.set_title("(b) distance from the manifold", color=SEC)

    fig.tight_layout()
    fig.savefig(OUT / "u2-procrustes.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig1_two_steps()
    fig2_s1_descent()
    fig3_o2_diagonalize()
    fig4_u2_procrustes()
    print(f"wrote figures to {OUT}")
