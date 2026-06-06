// Bond-dimension blow-up of the MPO-MPS product.
// Top:    MPO W (chain) applied to MPS psi (chain), joined by physical legs sigma.
// Bottom: the product psi' = W|psi>, a single MPS whose horizontal bonds are the
//   COMBINED (D_MPS * D_MPO) "fat" bonds -- drawn thick to mark the blow-up.
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

  // ===== Top: MPO W over MPS psi =====
  site((0, 4), $W^([1])$, fill: orange.lighten(85%), name: <w1>),
  site((1, 4), $W^([2])$, fill: orange.lighten(85%)),
  node((2, 4), $dots.h$),
  site((3, 4), $W^([L])$, fill: orange.lighten(85%), name: <wL>),

  site((0, 3), $A^([1])$, fill: blue.lighten(90%), name: <a1>),
  site((1, 3), $A^([2])$, fill: blue.lighten(90%)),
  node((2, 3), $dots.h$),
  site((3, 3), $A^([L])$, fill: blue.lighten(90%), name: <aL>),

  // sigma' legs up from W (output physical)
  edge((0, 4), (0, 5), label: $sigma'_1$, label-pos: 1, "-"),
  edge((1, 4), (1, 5), label: $sigma'_2$, label-pos: 1, "-"),
  edge((3, 4), (3, 5), label: $sigma'_L$, label-pos: 1, "-"),

  // sigma legs between W and A (contracted)
  edge((0, 4), (0, 3), label: $sigma_1$, label-side: right, "-"),
  edge((1, 4), (1, 3), "-"),
  edge((3, 4), (3, 3), label: $sigma_L$, label-side: left, "-"),

  // MPO bonds (bond-dim labelled inline on the first bond)
  edge((0, 4), (1, 4), label: $D_"MPO"$, label-side: left, label-sep: 0.6em, "-"),
  edge((1, 4), (2, 4), "-"),
  edge((2, 4), (3, 4), "-"),
  // MPS bonds (bond-dim labelled inline on the first bond)
  edge((0, 3), (1, 3), label: $D_"MPS"$, label-side: left, label-sep: 0.6em, "-"),
  edge((1, 3), (2, 3), "-"),
  edge((2, 3), (3, 3), "-"),

  // ===== arrow: contract W with psi =====
  edge((2, 2.6), (2, 1.6), label: jp[縮約], label-side: right, stroke: 1.2pt + black, "->"),

  // ===== Bottom: product psi' with fat bonds =====
  site((0, 1), $B^([1])$, fill: teal.lighten(85%), name: <b1>),
  site((1, 1), $B^([2])$, fill: teal.lighten(85%)),
  node((2, 1), $dots.h$),
  site((3, 1), $B^([L])$, fill: teal.lighten(85%), name: <bL>),

  // sigma' legs up
  edge((0, 1), (0, 2), label: $sigma'_1$, label-pos: 1, "-"),
  edge((1, 1), (1, 2), label: $sigma'_2$, label-pos: 1, "-"),
  edge((3, 1), (3, 2), label: $sigma'_L$, label-pos: 1, "-"),

  // fat bonds (thick), bond-dim labelled inline on the first bond
  edge((0, 1), (1, 1), label: $D_"MPS" D_"MPO"$, label-side: right, label-sep: 0.9em, stroke: 1.7pt + black, "-"),
  edge((1, 1), (2, 1), stroke: 1.7pt + black, "-"),
  edge((2, 1), (3, 1), stroke: 1.7pt + black, "-"),
)
