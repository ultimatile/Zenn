"""Render the Weyl chamber (canonical-class space) as a static 3D figure.

The figure visualizes the full Weyl chamber tetrahedron OA1A2A3 in
(cx, cy, cz) space described in the article. Gate marker positions are not
hard-coded: they are produced by running the actual `kak_decompose` PoC on
CNOT / sqrt(CNOT) / SWAP / iSWAP, so the figure and the text cannot drift.

Most named gates live on the cz = 0 base, so a single fixed viewpoint already
shows them clearly; rotation would add little. Color encodes the minimum CNOT
count needed to realize each locus:
  - segment O-B (CNOT) : 1 CNOT
  - base face cz = 0    : 2 CNOT (SO(4) class)
  - chamber interior    : 3 CNOT (generic SU(4))

Run with the `viz` dependency group:
    uv run --group viz python weyl_chamber.py
"""

from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection

from kak import CNOT, SWAP, kak_decompose, sqrt_cnot

OUT = "../../images/intro-kak-decomposition/weyl-chamber.png"

# iSWAP = exp(i (pi/4)(XX + YY)); its canonical class is the A2 vertex.
ISWAP = np.array(
    [
        [1, 0, 0, 0],
        [0, 0, 1j, 0],
        [0, 1j, 0, 0],
        [0, 0, 0, 1],
    ],
    dtype=complex,
)


def class_vector(U: np.ndarray) -> np.ndarray:
    r = kak_decompose(U)
    return np.array([r.cx, r.cy, r.cz])


# Full Weyl chamber tetrahedron vertices (pi/2 > cx >= cy >= cz >= 0,
# cx + cy <= pi/2).
O = np.array([0.0, 0.0, 0.0])
A1 = np.array([np.pi / 2, 0.0, 0.0])
A2 = np.array([np.pi / 4, np.pi / 4, 0.0])
A3 = np.array([np.pi / 4, np.pi / 4, np.pi / 4])

# Gate markers from the actual decomposition (label, point, text-offset).
gates = [
    (r"$O\,(=I)$", class_vector(np.eye(4)), (-0.26, 0.0, -0.03)),
    (r"$\sqrt{\mathrm{CNOT}}$", class_vector(sqrt_cnot()), (-0.18, 0.0, 0.10)),
    (r"$\mathrm{CNOT}$", class_vector(CNOT), (-0.02, 0.0, 0.09)),
    (r"$\mathrm{iSWAP}$", class_vector(ISWAP), (0.05, 0.04, 0.0)),
    (r"$\mathrm{SWAP}$", class_vector(SWAP), (0.05, 0.0, 0.06)),
]

B = class_vector(CNOT)  # = A1 midpoint; endpoint of the 1-CNOT segment.

C1 = "#d6336c"  # 1 CNOT
C2 = "#1c7ed6"  # 2 CNOT (SO(4) base face)
C3 = "#adb5bd"  # 3 CNOT (chamber edges)

fig = plt.figure(figsize=(6.4, 5.6))
ax = fig.add_subplot(111, projection="3d")

# Chamber edges.
edges = [(O, A1), (O, A2), (O, A3), (A1, A2), (A1, A3), (A2, A3)]
ax.add_collection3d(
    Line3DCollection([(a, b) for a, b in edges], colors=C3, linewidths=1.3)
)

# Base face cz = 0 (the SO(4) / 2-CNOT region).
base = Poly3DCollection(
    [[O, A1, A2]], facecolor=C2, edgecolor="none", alpha=0.18
)
ax.add_collection3d(base)

# 1-CNOT locus: segment O--B.
ax.plot(*np.array([O, B]).T, color=C1, linewidth=3.2, solid_capstyle="round")

# Gate markers + labels.
for label, p, off in gates:
    ax.scatter(*p, color="black", s=28, depthshade=False)
    ax.text(p[0] + off[0], p[1] + off[1], p[2] + off[2], label, fontsize=12)

# Vertex labels (A1 only; A2, A3 coincide with iSWAP/SWAP markers).
ax.text(A1[0] + 0.03, A1[1], A1[2] - 0.06, r"$A_1$", fontsize=10, color="#868e96")

ax.set_xlabel(r"$c_x$", labelpad=8)
ax.set_ylabel(r"$c_y$", labelpad=4)
ax.set_zlabel(r"$c_z$", labelpad=2)
ax.tick_params(labelsize=8, pad=1)
ax.set_xticks([0, np.pi / 4, np.pi / 2])
ax.set_xticklabels(["$0$", r"$\pi/4$", r"$\pi/2$"])
ax.set_yticks([np.pi / 4])
ax.set_yticklabels([r"$\pi/4$"])
ax.set_zticks([np.pi / 4])
ax.set_zticklabels([r"$\pi/4$"])
ax.set_xlim(0, np.pi / 2)
ax.set_ylim(0, np.pi / 4)
ax.set_zlim(0, np.pi / 4)
# Truthful geometry: box aspect matches the coordinate ranges.
ax.set_box_aspect([2, 1, 1])

# Legend (proxy artists).
ax.plot([], [], color=C1, linewidth=3.2, label="1 CNOT (segment $OB$)")
ax.plot([], [], color=C2, linewidth=8, alpha=0.4, label="2 CNOT ($c_z=0$, $SO(4)$)")
ax.plot([], [], color=C3, linewidth=1.3, label="3 CNOT (interior)")
ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.96), fontsize=9, framealpha=0.92)

# No in-figure title; the article caption describes the chamber. This avoids
# the legend/title collision in the cramped 3D bounding box.
fig.subplots_adjust(left=0.0, right=1.0, bottom=0.02, top=1.0)

# Fixed viewpoint chosen so all named gates and the OB segment read cleanly.
ax.view_init(elev=22, azim=35)
fig.savefig(OUT, dpi=140)
print(f"wrote {OUT}")
print("gate class vectors (cx, cy, cz):")
for label, p, _ in gates:
    print(f"  {label:>22}: ({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f})")
