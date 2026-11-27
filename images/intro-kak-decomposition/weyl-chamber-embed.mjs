// html-embed version of the Weyl chamber figure (replaces weyl-chamber.png).
//
// The tetrahedron is built from CSS 3D transforms (no JS runs in html-embed):
// edges and faces are divs placed with matrix3d, and every point label sits in
// a "billboard" that applies the inverse of the scene rotation so the MathML
// stays facing the reader. Two independent radio groups drive it: the
// viewpoint (oblique / top / front) and the legend rows, which leave only the
// region of one CNOT count visible.
//
// Class vectors are the exact values; kak.py reproduces them for
// I, CNOT, sqrt(CNOT), iSWAP and SWAP.
//
// usage: node images/intro-kak-decomposition/weyl-chamber-embed.mjs
//   writes images/intro-kak-decomposition/weyl-chamber.embed.html
import temml from "temml";
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const OUT_DIR = dirname(fileURLToPath(import.meta.url));

// Same Temml post-fix as kak-tn-embed.mjs (stretchy big operators sit low in Chrome).
const m = (tex) =>
  temml.renderToString(tex).replace(/<mo stretchy="true">([∑∏∐⋃⋂⨁⨂])<\/mo>/g, "<mo>$1</mo>");

// ---------------------------------------------------------------- geometry
const PI = Math.PI;
const S = 165; // px per radian
const MOBILE_ZOOM = 0.66;

const P = {
  O: [0, 0, 0],
  A1: [PI / 2, 0, 0],
  A2: [PI / 4, PI / 4, 0],
  A3: [PI / 4, PI / 4, PI / 4],
  B: [PI / 4, 0, 0],
  R: [PI / 8, 0, 0], // sqrt(CNOT)
};
const CENTER = [PI / 4, PI / 8, PI / 16];

// (cx, cy, cz) -> CSS px: cx to the right, cz up, cy away from the reader.
const w = ([cx, cy, cz]) => [S * (cx - CENTER[0]), -S * (cz - CENTER[2]), -S * (cy - CENTER[1])];

const sub = (a, b) => a.map((v, i) => v - b[i]);
const add = (a, b) => a.map((v, i) => v + b[i]);
const mul = (a, k) => a.map((v) => v * k);
const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const len = (a) => Math.hypot(...a);
const unit = (a) => mul(a, 1 / len(a));
const f = (x) => +x.toFixed(3);

// Local (x, y, 0) of a div -> t + x e1 + y e2 (column-major matrix3d).
const mat = (e1, e2, e3, t) => `matrix3d(${[...e1, 0, ...e2, 0, ...e3, 0, ...t, 1].map(f).join(",")})`;

// A line is two crossed thin strips so it never vanishes when seen edge-on.
function line(p, q, cls, thick = 2) {
  const a = w(p);
  const d = sub(w(q), a);
  const L = len(d);
  const e1 = unit(d);
  const ref = Math.abs(e1[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0];
  const e2 = unit(cross(e1, ref));
  const e3 = cross(e1, e2);
  return [
    [e2, e3],
    [e3, mul(e2, -1)],
  ]
    .map(
      ([u, n]) =>
        `<i class="${cls}" style="width:${f(L)}px;height:${thick}px;transform:${mat(e1, u, n, add(a, mul(u, -thick / 2)))}"></i>`,
    )
    .join("");
}

function face(p0, p1, p2, cls) {
  const [a, b, c] = [p0, p1, p2].map(w);
  const e1 = unit(sub(b, a));
  const v = sub(c, a);
  const n = unit(cross(e1, v));
  const e2 = cross(n, e1);
  const x1 = len(sub(b, a));
  const [x2, y2] = [dot(v, e1), dot(v, e2)];
  const x0 = Math.min(0, x2);
  const width = Math.max(x1, x2) - x0;
  const poly = [
    [-x0, 0],
    [x1 - x0, 0],
    [x2 - x0, y2],
  ]
    .map(([x, y]) => `${f(x)}px ${f(y)}px`)
    .join(",");
  return `<i class="f ${cls}" style="width:${f(width)}px;height:${f(y2)}px;clip-path:polygon(${poly});transform:${mat(e1, e2, n, add(a, mul(e1, x0)))}"></i>`;
}

// A point marker + label that always faces the reader.
function point(p, cls, label, pos, hollow = false) {
  const [x, y, z] = w(p).map(f);
  return `<div class="pt" style="transform:translate3d(${x}px,${y}px,${z}px)"><div class="bb"><div class="z"><i class="dot ${cls}${hollow ? " ho" : ""}"></i>${label ? `<span class="lb ${pos} ${cls}">${label}</span>` : ""}</div></div></div>`;
}

const AX = 0.24; // how far the dashed axes stick out of the chamber
const sceneBody = [
  // faces: base cz = 0 is the 2-CNOT region, the rest bounds the 3-CNOT interior
  face(P.O, P.A1, P.A2, "k2"),
  face(P.O, P.A1, P.A3, "k3"),
  face(P.O, P.A2, P.A3, "k3"),
  face(P.A1, P.A2, P.A3, "k3"),
  // edges
  ...[
    [P.O, P.A1],
    [P.O, P.A2],
    [P.O, P.A3],
    [P.A1, P.A2],
    [P.A1, P.A3],
    [P.A2, P.A3],
  ].map(([a, b]) => line(a, b, "e")),
  // axes (dashed) and a guide showing that A2 sits straight behind B
  // (A3 straight above A2 is already the edge A2A3)
  line(P.A1, [PI / 2 + AX, 0, 0], "ax", 1.5),
  line(P.O, [0, PI / 4 + AX, 0], "ax", 1.5),
  line(P.O, [0, 0, PI / 4 + AX], "ax", 1.5),
  line(P.A2, P.B, "gd", 1.5),
  // points
  point(P.O, "k0", `${m("O")}<small>（${m("I")}）</small>`, "l"),
  point(P.A1, "k0", `${m("A_1")}<small>（${m("\\equiv O")}）</small>`, "tr", true),
  point(P.R, "k2", m("\\sqrt{\\mathrm{CNOT}}"), "bl"),
  point(P.B, "k1", `${m("B")}<small>（CNOT）</small>`, "b"),
  point(P.A2, "k2", `${m("A_2")}<small>（iSWAP）</small>`, "r"),
  point(P.A3, "k3", `${m("A_3")}<small>（SWAP）</small>`, "t"),
  // axis names
  point([PI / 2 + AX, 0, 0], "kx", m("c_x"), "b"),
  point([0, PI / 4 + AX, 0], "kx ky", m("c_y"), "tl"),
  point([0, 0, PI / 4 + AX], "kx kz", m("c_z"), "tr"),
]
  .join("\n")
  .replace(/<i class="dot kx[^"]*"><\/i>/g, ""); // axis-name billboards carry no dot

// ---------------------------------------------------------------- legend
const rows = [
  {
    k: 0,
    head: "0 CNOT",
    body: `点${m("O = (0,0,0)")}：恒等${m("I")}。${m("A_1 = (\\pi/2,0,0)")}も同じ類`,
  },
  {
    k: 1,
    head: "1 CNOT",
    body: `点${m("B = (\\pi/4,0,0)")}：CNOT。この1点だけ`,
  },
  {
    k: 2,
    head: "2 CNOT",
    body: `底面${m("c_z = 0")}（上の点を除く）。${m("\\sqrt{\\mathrm{CNOT}} = (\\pi/8,0,0)")}、${m("A_2 = (\\pi/4,\\pi/4,0)")}：iSWAP`,
  },
  {
    k: 3,
    head: "3 CNOT",
    body: `${m("c_z > 0")}の内部と側面。${m("A_3 = (\\pi/4,\\pi/4,\\pi/4)")}：SWAP`,
  },
];

const legend = `<div class="leg"><p class="hint">クリックで対応領域だけ表示</p><label class="row all" for="h-all">すべて表示</label>${rows
  .map(
    (r) =>
      `<label class="row" for="h${r.k}"><span class="sw s${r.k}"></span><b>${r.head}</b><span class="tx">${r.body}</span></label>`,
  )
  .join("")}</div>`;

// ---------------------------------------------------------------- views & css
const VIEWS = {
  obl: [-24, -32],
  top: [-90, 0],
  front: [-4, -6],
};
const rot = ([ax, ay]) => `rotateX(${ax}deg) rotateY(${ay}deg)`;
const inv = ([ax, ay]) => `rotateY(${-ay}deg) rotateX(${-ax}deg)`;

const ARIA =
  "Weyl chamber の立体図。c_x を右、c_y を奥、c_z を上にとった座標に四面体 O A1 A2 A3 を描いている。" +
  "手前の辺 O A1 上に √CNOT (π/8,0,0) と B = CNOT (π/4,0,0) があり、A2 = iSWAP (π/4,π/4,0) は B の真奥の底面上、" +
  "A3 = SWAP (π/4,π/4,π/4) は A2 の真上にある。底面 c_z = 0 は 2 CNOT、それより上は 3 CNOT の領域。";

const baseCss = `
:root{--fg:#1f2328;--mu:#6e7781;--bg:#ffffff;--hl:#eef2f6;--c0:#2f9e44;--c1:#d6336c;--c2:#1c7ed6;--c3:#e8590c}
[data-theme="dark"]{--fg:#e6edf3;--mu:#8b949e;--bg:#0d1117;--hl:#1f2630;--c0:#69db7c;--c1:#f783ac;--c2:#74c0fc;--c3:#ffa94d}
*{box-sizing:border-box}
.wc{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;padding:6px}
.sr{position:absolute;opacity:0;pointer-events:none}
.wrap{display:flex;align-items:center;gap:6px}
.scene{position:relative;flex:0 0 430px;height:330px;perspective:1400px;overflow:hidden}
.zoom{position:absolute;left:52%;top:54%;transform-style:preserve-3d}
.obj{transform-style:preserve-3d;transform:${rot(VIEWS.obl)}}
.obj i,.pt{position:absolute;left:0;top:0;display:block;transform-origin:0 0}
.pt,.bb,.z{transform-style:preserve-3d}
.bb{transform:${inv(VIEWS.obl)}}
.f{opacity:.22;transition:opacity .3s}
.f.k2{background:var(--c2)}
.f.k3{background:var(--c3);opacity:.07}
.e{background:var(--fg);opacity:.7}
.ax{background:repeating-linear-gradient(90deg,var(--mu) 0 5px,transparent 5px 9px)}
.gd{background:repeating-linear-gradient(90deg,var(--mu) 0 3px,transparent 3px 6px);opacity:.8}
.dot{position:absolute;width:10px;height:10px;border-radius:50%;transform:translate(-50%,-50%) translateZ(2px);transition:opacity .3s}
.dot.k0{background:var(--c0)}.dot.k1{background:var(--c1)}.dot.k2{background:var(--c2)}.dot.k3{background:var(--c3)}
.dot.ho{background:var(--bg);border:2px solid var(--c0)}
.lb{position:absolute;white-space:nowrap;font-size:13px;transition:opacity .3s}
.lb.r{transform:translate(9px,-50%) translateZ(24px)}
.lb.l{transform:translate(calc(-100% - 9px),-50%) translateZ(24px)}
.lb.t{transform:translate(-50%,calc(-100% - 7px)) translateZ(24px)}
.lb.b{transform:translate(-50%,7px) translateZ(24px)}
.lb.tr{transform:translate(7px,calc(-100% - 3px)) translateZ(24px)}
.lb.bl{transform:translate(calc(-100% + 4px),6px) translateZ(24px)}
.lb.tl{transform:translate(calc(-100% - 6px),calc(-100% - 14px)) translateZ(24px)}
.lb.kx{background:var(--bg);padding:0 3px;border-radius:4px}
.lb small{font-size:11.5px;color:var(--mu)}
math{font-size:15px}
.lb small math{font-size:13px}
.leg{flex:1 1 auto;display:flex;flex-direction:column;gap:3px;font-size:12.5px}
.leg math{font-size:13px}
.row{display:grid;grid-template-columns:14px auto;column-gap:6px;padding:4px 6px;border-radius:6px}
.row b{font-weight:600}
.row .tx{grid-column:2;color:var(--fg)}
.sw{width:12px;height:12px;border-radius:3px;align-self:center}
.s0{background:var(--c0)}.s1{background:var(--c1)}.s2{background:var(--c2)}.s3{background:var(--c3)}
.hint{margin:0 0 2px;color:var(--mu);font-size:11.5px}
@media (max-width:640px){
  .wrap{flex-direction:column;align-items:stretch;gap:2px}
  .scene{flex:0 0 auto;width:100%;height:240px}
  .zoom{left:46%;transform:scale(${MOBILE_ZOOM})}
  .z{transform:scale(${f(1 / MOBILE_ZOOM)})}
  .leg{font-size:11.5px;gap:1px}
  .leg math{font-size:12px}
  .row{padding:2px 6px}
}`;

const highlightCss = `
label.row{cursor:pointer}
label.row.all{display:block;color:var(--mu);padding:2px 6px}
${["all", 0, 1, 2, 3].map((k) => `#h${k === "all" ? "-all" : k}:checked~.wrap label[for="h${k === "all" ? "-all" : k}"]`).join(",")}{background:var(--hl);outline:1px solid var(--mu)}
${["all", 0, 1, 2, 3].map((k) => `#h${k === "all" ? "-all" : k}:focus-visible~.wrap label[for="h${k === "all" ? "-all" : k}"]`).join(",")}{outline:2px solid var(--c2)}
${[0, 1, 2, 3]
  .map(
    (k) =>
      `#h${k}:checked~.wrap .scene :is(.dot,.lb,.f):not(.k${k},.kx){opacity:.12}`,
  )
  .join("\n")}
${[0, 1, 2].map((k) => `#h${k}:checked~.wrap .scene .f.k3`).join(",")}{opacity:.03}
#h2:checked~.wrap .f.k2{opacity:.45}
#h3:checked~.wrap .f.k3{opacity:.28}`;

const radios = (name, ids, checked) =>
  ids.map((id) => `<input class="sr" type="radio" name="${name}" id="${id}"${id === checked ? " checked" : ""}>`).join("");

const scene = `<div class="scene" role="img" aria-label="${ARIA}"><div class="zoom"><div class="obj">\n${sceneBody}\n</div></div></div>`;

const viewCss = `
.bar{display:flex;gap:4px;flex-wrap:wrap;font-size:12.5px;margin:0 0 2px}
.bar label{cursor:pointer;padding:2px 10px;border:1px solid var(--mu);border-radius:999px;color:var(--mu)}
${Object.keys(VIEWS)
  .map((v) => `#v-${v}:checked~.wrap label[for="v-${v}"]`)
  .join(",")}{background:var(--hl);color:var(--fg);border-color:var(--fg)}
${Object.keys(VIEWS)
  .map((v) => `#v-${v}:focus-visible~.wrap label[for="v-${v}"]`)
  .join(",")}{outline:2px solid var(--c2)}
.obj,.bb{transition:transform .9s ease-in-out}
${Object.entries(VIEWS)
  .map(([v, r]) => `#v-${v}:checked~.wrap .obj{transform:${rot(r)}}\n#v-${v}:checked~.wrap .bb{transform:${inv(r)}}`)
  .join("\n")}
#v-top:checked~.wrap .lb.kz,#v-front:checked~.wrap .lb.ky{opacity:0}
.col{display:flex;flex-direction:column;flex:0 0 430px}
.col .scene{flex:none;width:430px}
@media (max-width:640px){.col{flex:0 0 auto}.col .scene{width:100%}}
@media (prefers-reduced-motion:reduce){.obj,.bb{transition:none}}`;

const hRadios = radios("h", ["h-all", "h0", "h1", "h2", "h3"], "h-all");
const vRadios = radios("v", ["v-obl", "v-top", "v-front"], "v-obl");
const viewCol = `<div class="col"><div class="bar"><label for="v-obl">斜めから</label><label for="v-top">真上から（${m("c_z")}軸方向）</label><label for="v-front">正面から（${m("c_y")}軸方向）</label></div>${scene}</div>`;

// With both control sets the phone layout must still fit in 500px.
const compactCss = `
@media (max-width:640px){
  .scene{height:225px}
  .hint{margin:0}
  .row{padding:1px 6px}
  label.row.all{padding:1px 6px}
}`;

const html = `${vRadios}${hRadios}<div class="wrap">${viewCol}${legend}</div>`;
const css = baseCss + viewCss + highlightCss + compactCss;
const out = `<div class="wc">${html}</div>\n<style>${css.trim()}\n</style>`;
const file = join(OUT_DIR, "weyl-chamber.embed.html");
writeFileSync(file, out);
console.log(`${file}: ${Buffer.byteLength(out.trim())} bytes`);
