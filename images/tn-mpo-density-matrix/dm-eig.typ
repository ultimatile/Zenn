// Eigendecomposition of the reduced density matrix:
//   rho^[s] = U Lambda U^dagger, keep the D' largest eigenvalues.
//   The kept eigenvectors U become the new left-canonical site tensor M^[s].
#import "@preview/fletcher:0.5.8" as fletcher: diagram, edge, node

#set page(width: auto, height: auto, margin: 8pt)

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
  spacing: (0.95cm, 0.95cm),

  // rho with its two composite legs
  site((0, 1), $rho^([s])$, fill: orange.lighten(85%), name: <rho>),
  edge(<rho>, (-1.1, 2), label: $(m_(s-1) sigma'_s)$, label-pos: 1, "-"),
  edge(<rho>, (-1.1, 0), label: $(tilde(m)_(s-1) tilde(sigma)'_s)$, label-pos: 1, "-"),

  // procedural arrow
  edge((1, 1), (2.2, 1), label: jp[対角化], stroke: 1.2pt + black, "->"),

  // U Lambda U^dagger
  site((3.2, 1), $U$, fill: teal.lighten(85%), name: <U>),
  site((4.2, 1), $Lambda$, name: <L>),
  site((5.2, 1), $U^dagger$, name: <Ud>),
  edge(<U>, <L>, "-"),
  edge(<L>, <Ud>, "-"),
  edge(<U>, (3.2, 2.1), "-"),
  edge(<Ud>, (5.2, 2.1), "-"),

  // underbrace: kept U = M^[s]
  node(
    (3.2, 0.1),
    text(0.85em)[$= M^([s])$],
    name: <anno>,
  ),
  edge((2.85, 0.6), (2.85, 0.1), <anno.west>, stroke: 0.5pt + gray, "-"),
  edge((3.55, 0.6), (3.55, 0.1), <anno.east>, stroke: 0.5pt + gray, "-"),
)
