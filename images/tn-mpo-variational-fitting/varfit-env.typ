// Mid-sweep state of variational MPO-MPS fitting, orthogonality center at site s.
// The overlap network <phi~ | W | psi> is split into three parts:
//   left environment  L_{s-1}  (collapse of sites 1..s-1)
//   active column      A^[s] (ket) / W^[s] (mpo) / M^[s] (bra, being solved)
//   right environment  R_{s+1}  (collapse of sites s+1..L)
#import "@preview/fletcher:0.5.8" as fletcher: diagram, edge, node

#set page(width: auto, height: auto, margin: 6pt)

// Japanese label helper (Gothic matches the sibling zip-up diagrams).
#let jp(content) = text(font: "BIZ UDPGothic")[#content]

#let site(pos, label, fill: white, name: none, stroke: 0.6pt + black) = node(
  pos,
  label,
  shape: rect,
  stroke: stroke,
  fill: fill,
  inset: 4pt,
  name: name,
)

#diagram(
  axes: (ltr, btt),
  spacing: (1.05cm, 1.05cm),

  // === Left environment (collapse of sites 1..s-1) ===
  site((0, 1), $L_(s-1)$, fill: orange.lighten(85%), name: <L>),

  // === Active column at site s ===
  site((2, 0), $A^([s])$, name: <A>),
  site((2, 1), $W^([s])$, name: <W>),
  // M^[s] is the unknown being solved for: dashed to mark it as "to be determined".
  site(
    (2, 2),
    $M^([s])$,
    fill: teal.lighten(85%),
    stroke: (paint: teal.darken(20%), thickness: 0.9pt, dash: "dashed"),
    name: <M>,
  ),

  // === Right environment (collapse of sites s+1..L) ===
  site((4, 1), $R_(s+1)$, fill: orange.lighten(85%), name: <R>),

  // L -> active column (three legs: to A, W, M)
  edge(<L>, <A>, label: $l$, label-side: right, "-"),
  edge(<L>, <W>, label: $b$, label-side: left, "-"),
  edge(<L>, <M>, label: $m_(s-1)$, label-side: left, "-"),

  // active column -> R (three legs)
  edge(<A>, <R>, label: $r$, label-side: right, "-"),
  edge(<W>, <R>, label: $b'$, label-side: right, "-"),
  edge(<M>, <R>, label: $m_s$, label-side: left, "-"),

  // vertical internal contractions
  edge(<A>, <W>, label: $sigma_s$, label-side: right, "-"),
  edge(<W>, <M>, label: $sigma'_s$, label-side: right, "-"),

  // annotations: each environment is a collapse of the outer chain
  node((0, 2.4), jp[左側$1..s-1$の縮約], name: <annoL>),
  edge((0, 1.6), <annoL>, stroke: 0.4pt + gray, "-"),
  node((4, 2.4), jp[右側$s+1..L$の縮約], name: <annoR>),
  edge((4, 1.6), <annoR>, stroke: 0.4pt + gray, "-"),
)
