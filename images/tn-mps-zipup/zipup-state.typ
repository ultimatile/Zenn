// Mid-sweep state of the zip-up algorithm at site s.
// Three regions joined by the carrier tensor R_s:
//   (1) processed new MPS chain M^[1..s] (top-left)
//   (2) carrier R_s (boundary, 3 legs)
//   (3) unprocessed remainder: W^[s+1..L] (top-right) stacked over A^[s+1..L] (bottom-right)
#import "@preview/fletcher:0.5.8" as fletcher: diagram, edge, node

#set page(width: auto, height: auto, margin: 6pt)

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

  // === New MPS chain (already processed, left-canonical) ===
  site((0, 2), $M^([1])$, name: <m1>),
  site((1, 2), $M^([2])$),
  node((2, 2), $dots.h$),
  site((3, 2), $M^([s])$, name: <ms>),

  // === Carrier tensor R_s (3-leg) ===
  site((4, 1), $R_s$, fill: teal.lighten(85%)),

  // === MPO chain (unprocessed) — top of remainder ===
  site((5, 2), $W^([s+1])$),
  node((6, 2), $dots.h$),
  site((7, 2), $W^([L])$),

  // === Original MPS chain (unprocessed) — bottom of remainder ===
  site((5, 0), $A^([s+1])$),
  node((6, 0), $dots.h$),
  site((7, 0), $A^([L])$),

  // M chain horizontal bonds
  edge((0, 2), (1, 2), "-"),
  edge((1, 2), (2, 2), "-"),
  edge((2, 2), (3, 2), "-"),

  // M_s -> R_s -> {W_{s+1}, A_{s+1}}
  edge((3, 2), (4, 1), "-"),
  edge((4, 1), (5, 2), "-"),
  edge((4, 1), (5, 0), "-"),

  // W chain horizontal bonds
  edge((5, 2), (6, 2), "-"),
  edge((6, 2), (7, 2), "-"),

  // A chain horizontal bonds
  edge((5, 0), (6, 0), "-"),
  edge((6, 0), (7, 0), "-"),

  // W <-> A internal contractions (sigma)
  edge((5, 2), (5, 0), label: $sigma_(s+1)$, label-side: left, "-"),
  edge((7, 2), (7, 0), label: $sigma_L$, label-side: left, "-"),

  // Physical (sigma') legs above M chain
  edge((0, 2), (0, 3), label: $sigma'_1$, label-pos: 1, "-"),
  edge((1, 2), (1, 3), label: $sigma'_2$, label-pos: 1, "-"),
  edge((3, 2), (3, 3), label: $sigma'_s$, label-pos: 1, "-"),

  // Physical (sigma') legs above W chain
  edge((5, 2), (5, 3), label: $sigma'_(s+1)$, label-pos: 1, "-"),
  edge((7, 2), (7, 3), label: $sigma'_L$, label-pos: 1, "-"),

  // === Bracket annotation: "left-canonical up to here" under M^[1..s] ===
  // L-shaped underbrace from M_1 and M_s converging on a center annotation.
  // Start at floating coordinates below the M boxes (NOT <m1.south>/<ms.south>)
  // so the bracket is visually disjoint from the tensors — otherwise the reader
  // can mistake the bracket arms for additional tensor bonds (a "ring").
  node(
    (1.5, 1.3),
    text(0.85em, font: "BIZ UDPGothic")[ここまで左標準形],
    name: <anno>,
  ),
  edge((0, 1.5), (0, 1.3), <anno.west>, stroke: 0.5pt + gray, "-"),
  edge((3, 1.5), (3, 1.3), <anno.east>, stroke: 0.5pt + gray, "-"),
)
