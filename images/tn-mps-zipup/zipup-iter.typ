// One iteration of the zip-up algorithm at site s+1:
//   (a) contract R_s, W^[s+1], A^[s+1]  ->  C^[s+1]
//   (b) SVD C^[s+1] = U S V^dagger
//   (c) identify M^[s+1] := U,  R_{s+1} := S V^dagger
#import "@preview/fletcher:0.5.8" as fletcher: diagram, edge, node
#import fletcher.shapes: circle as fcircle

#set page(width: auto, height: auto, margin: 8pt)

// Japanese label helper (Gothic matches the sibling zipup-state diagram).
#let jp(content) = text(font: "BIZ UDPGothic")[#content]

#let box-site(pos, label, fill: white, name: none) = node(
  pos,
  label,
  shape: rect,
  stroke: 0.6pt + black,
  fill: fill,
  inset: 4pt,
  name: name,
)

#let circ-site(pos, label, fill: white, name: none) = node(
  pos,
  label,
  shape: fcircle,
  stroke: 0.6pt + black,
  fill: fill,
  inset: 4pt,
  name: name,
)

#diagram(
  axes: (ltr, btt),
  spacing: (0.85cm, 0.85cm),

  // ============================================================
  // Panel 1 (top-left): local 3-tensor network around site s+1
  // ============================================================
  box-site((1, 7), $R_s$, fill: teal.lighten(85%), name: <p1-rs>),
  box-site((2.5, 8), $W^([s+1])$, name: <p1-w>),
  box-site((2.5, 6), $A^([s+1])$, name: <p1-a>),

  edge((-0.3, 7), <p1-rs>, label: $m_(s-1)$, label-pos: 0, "-"),
  edge(<p1-rs>, <p1-w>, "-"),
  edge(<p1-rs>, <p1-a>, "-"),
  edge(<p1-w>, <p1-a>, label: $sigma_(s+1)$, label-side: left, "-"),
  edge(<p1-w>, (2.5, 9.2), label: $sigma'_(s+1)$, label-pos: 1, "-"),
  edge(<p1-w>, (3.8, 8), label: $b'$, label-pos: 1, "-"),
  edge(<p1-a>, (3.8, 6), label: $r$, label-pos: 1, "-"),

  // Arrow Panel 1 -> Panel 2 (縮約/ contract)
  // Thicker than tensor edges to mark this as a procedural transition.
  edge((4.4, 7), (5.4, 7), label: jp[縮約], stroke: 1.2pt + black, "->"),

  // ============================================================
  // Panel 2 (top-right): C^[s+1] (contracted) with SVD partition
  // ============================================================
  circ-site((7, 7), $C^([s+1])$, name: <p2-c>),

  edge(<p2-c>, (5.6, 8.1), label: $m_(s-1)$, label-pos: 1, "-"),
  edge(<p2-c>, (6.5, 9.2), label: $sigma'_(s+1)$, label-pos: 1, "-"),
  edge(<p2-c>, (8.4, 8.1), label: $b'$, label-pos: 1, "-"),
  edge(<p2-c>, (8.4, 5.9), label: $r$, label-pos: 1, "-"),

  // Red dashed line: SVD partition cut.
  // Separates the upper-left index group (m_{s-1}, sigma'_{s+1})
  // from the lower-right group (b', r) — the matrix reshape boundary.
  edge(
    (6.6, 6.1),
    (7.4, 7.9),
    stroke: (paint: red, thickness: 1.2pt, dash: "dashed"),
    "-",
  ),

  // Arrow Panel 2 -> Panel 3 (SVD, downward)
  edge((7, 5.5), (7, 4.7), label: jp[SVD], stroke: 1.2pt + black, "->"),

  // ============================================================
  // Panel 3 (bottom-right): SVD result  U . S . V^dagger
  // ============================================================
  box-site((6, 3.5), $U^([s+1])$, name: <p3-u>),
  box-site((7, 3.5), $S^([s+1])$, name: <p3-s>),
  box-site((8, 3.5), $V^([s+1] dagger)$, name: <p3-v>),

  edge(<p3-u>, <p3-s>, "-"),
  edge(<p3-s>, <p3-v>, "-"),
  edge((4.7, 3.5), <p3-u>, label: $m_(s-1)$, label-pos: 0, "-"),
  edge(<p3-u>, (6, 4.7), label: $sigma'_(s+1)$, label-pos: 1, "-"),
  edge(<p3-v>, (9.3, 4.1), label: $b'$, label-pos: 1, "-"),
  edge(<p3-v>, (9.3, 2.9), label: $r$, label-pos: 1, "-"),

  // Underbrace under U:  = M^[s+1]
  // Verticals at x=5.3 and x=6.7 sit OUTSIDE the anno node's width,
  // so the horizontal arms bend INWARD toward the anno (proper U-shape).
  node(
    (6, 2.4),
    text(0.85em)[$M^([s+1])$],
    name: <p3-anno-m>,
  ),
  edge((5.5, 2.9), (5.5, 2.4), <p3-anno-m.west>, stroke: 0.5pt + gray, "-"),
  edge((6.5, 2.9), (6.5, 2.4), <p3-anno-m.east>, stroke: 0.5pt + gray, "-"),

  // Underbrace under S, V^dagger:  = R_{s+1}
  node(
    (7.5, 2.4),
    text(0.85em)[$R_(s+1)$],
    name: <p3-anno-r>,
  ),
  edge((6.7, 2.9), (6.7, 2.4), <p3-anno-r.west>, stroke: 0.5pt + gray, "-"),
  edge((8.3, 2.9), (8.3, 2.4), <p3-anno-r.east>, stroke: 0.5pt + gray, "-"),

  // Arrow Panel 3 -> Panel 4 (identify, leftward)
  edge((4.3, 3.5), (3.5, 3.5), stroke: 1.2pt + black, "->"),

  // ============================================================
  // Panel 4 (bottom-left): new MPS site M^[s+1] and carrier R_{s+1}
  // ============================================================
  box-site((1, 3.5), $M^([s+1])$, name: <p4-m>),
  box-site((2.5, 3.5), $R_(s+1)$, fill: teal.lighten(85%), name: <p4-r>),

  edge(<p4-m>, <p4-r>, label: $m_s$, "-"),
  edge((-0.3, 3.5), <p4-m>, label: $m_(s-1)$, label-pos: 0, "-"),
  edge(<p4-m>, (1, 4.7), label: $sigma'_(s+1)$, label-pos: 1, "-"),
  // Diagonal legs from R_{s+1}; label-anchor pins the label box so b' sits
  // due-north of the tip (anchor: bottom) and r sits due-east (anchor: left).
  edge(
    <p4-r>,
    (3.6, 4.1),
    label: $b'$,
    label-pos: 1,
    label-anchor: "south",
    "-",
  ),
  edge(
    <p4-r>,
    (3.6, 2.9),
    label: $r$,
    label-pos: 1,
    label-anchor: "west",
    "-",
  ),
)
