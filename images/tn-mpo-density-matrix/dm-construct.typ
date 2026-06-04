// Reduced density matrix of the target state phi = W|psi> at bond s.
//   rho^[s] = Phi^[s] . G^[s] . (Phi^[s])^dagger, traced over the right block.
//   Phi^[s]  (ket): site-s tensor of phi in the truncated-left basis; open legs (m_{s-1}, sigma'_s)
//   G^[s]         : right environment = norm of the right block (the trace over sites s+1..L)
//   Phi^[s]* (bra): conjugate; open legs (m~_{s-1}, sigma~'_s)
// The four open legs are the two composite indices of rho^[s].
#import "@preview/fletcher:0.5.8" as fletcher: diagram, edge, node

#set page(width: auto, height: auto, margin: 6pt)

#let jp(content) = text(font: "BIZ UDPGothic")[#content]

#let site(pos, label, fill: white, name: none) = node(
  pos,
  label,
  shape: rect,
  stroke: 0.6pt + black,
  fill: fill,
  inset: 4pt,
  name: name,
)

#diagram(
  axes: (ltr, btt),
  spacing: (1.15cm, 1.0cm),

  // ket Phi (bottom) and bra Phi* (top)
  site((1, 0), $Phi^([s])$, fill: blue.lighten(88%), name: <ket>),
  site((1, 2), $Phi^([s]*)$, fill: blue.lighten(88%), name: <bra>),

  // right environment G (trace over the right block), shared by bra and ket
  site((3, 1), $G^([s])$, fill: orange.lighten(85%), name: <G>),

  // ket open legs (these become one composite index of rho)
  edge(<ket>, (-0.3, 0), label: $m_(s-1)$, label-pos: 1, "-"),
  edge(<ket>, (1, -1), label: $sigma'_s$, label-pos: 1, "-"),
  // bra open legs (the other composite index of rho)
  edge(<bra>, (-0.3, 2), label: $tilde(m)_(s-1)$, label-pos: 1, "-"),
  edge(<bra>, (1, 3), label: $tilde(sigma)'_s$, label-pos: 1, "-"),

  // ket/bra -> G via the fat right bond a_s = (r, b')
  edge(<ket>, <G>, label: $(r, b')$, label-side: right, "-"),
  edge(<bra>, <G>, label: $(tilde(r), tilde(b)')$, label-side: left, "-"),

  // annotation under G
  node(
    (3, -0.5),
    jp[右ブロックのトレース],
    name: <anno>,
  ),
  edge((3, 0.5), <anno>, stroke: 0.4pt + gray, "-"),
)
