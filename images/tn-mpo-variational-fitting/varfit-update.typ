// Local update of variational MPO-MPS fitting at site s.
// With the overlap network put in mixed-canonical gauge (norm matrix = identity),
// the optimal M^[s] is obtained by a single contraction:
//   M^[s] = L_{s-1} . A^[s] . W^[s] . R_{s+1}
// The three open legs (m_{s-1}, sigma'_s, m_s) become the legs of the new tensor.
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
  spacing: (0.9cm, 0.9cm),

  // ============================================================
  // Panel 1 (left): contraction network with M^[s] removed
  // ============================================================
  site((0, 1), $L_(s-1)$, fill: orange.lighten(85%), name: <L>),
  site((1.5, 0), $A^([s])$, name: <A>),
  site((1.5, 1), $W^([s])$, name: <W>),
  site((3, 1), $R_(s+1)$, fill: orange.lighten(85%), name: <R>),

  // internal contracted bonds
  edge(<L>, <A>, label: $l$, label-side: right, "-"),
  edge(<L>, <W>, label: $b$, label-side: left, "-"),
  edge(<A>, <R>, label: $r$, label-side: right, "-"),
  edge(<W>, <R>, label: $b'$, label-side: right, "-"),
  edge(<A>, <W>, label: $sigma_s$, label-side: right, "-"),

  // open legs (where the solved M^[s] will attach)
  edge(<L>, (-1.0, 2), label: $m_(s-1)$, label-pos: 1, "-"),
  edge(<W>, (1.5, 2.3), label: $sigma'_s$, label-pos: 1, "-"),
  edge(<R>, (4.0, 2), label: $m_s$, label-pos: 1, "-"),

  // Procedural arrow (thicker than tensor edges)
  edge((4.7, 1), (5.7, 1), label: jp[縮約], stroke: 1.2pt + black, "->"),

  // ============================================================
  // Panel 2 (right): resulting new MPS site tensor M^[s]
  // ============================================================
  site((7, 1), $M^([s])$, fill: teal.lighten(85%), name: <M>),
  edge(<M>, (6.0, 2), label: $m_(s-1)$, label-pos: 1, "-"),
  edge(<M>, (7, 2.3), label: $sigma'_s$, label-pos: 1, "-"),
  edge(<M>, (8.0, 2), label: $m_s$, label-pos: 1, "-"),
)
