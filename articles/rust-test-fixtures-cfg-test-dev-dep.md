---
title: "Rustでテストフィクスチャーを別クレートに切り出したら自クレートの単体テストが壊れた"
emoji: "🦀"
type: "tech"
topics: ["rust", "cargo"]
published: true
register: almost
---


:::message

## TL;DR

- 別クレートに切り出したフィクスチャーを元クレートがdev-dependencyにすると、元クレート自身の`#[cfg(test)]`を用いた単体テストがコンパイルできなくなる。
- 原因は`cargo test`が元クレートを「`cfg(test)`あり版」と「なし版」の2インスタンスでビルドし、両者の同名の型が別物になること。
- `cargo build`も統合テスト（`tests/*.rs`）も通るので「動く」と誤認しやすい。壊れるのは元クレート自身のin-lib単体テスト経路だけ（統合テストなら元クレートを1インスタンスしかリンクせず無事）。
- **要点: 元クレートの型を組み立てて元クレート自身のin-lib単体テストで使うフィクスチャーは、外部クレートに切り出せない。** 切り出すと`foo ⇄ fixtures`のdev-dependency循環が必要になり、この循環ゆえに単体テストビルドは別インスタンスの型をリンクするため。対処は元クレート内に`#[cfg(any(test, feature = "..."))] pub mod`で置くこと。元クレートに依存しない（循環にならない）フィクスチャー、たとえば統合テスト専用や下位クレートのシナリオ用のものは切り出せる。

:::

## はじめに

あるクレートのテスト用ヘルパー（フィクスチャー）を複数のクレートで使い回したくなることがあります。つい独立したクレートに切り出して共有したくなりますが、元クレートの型に依存するフィクスチャーでこれをやると、元クレート自身の`#[cfg(test)]`単体テストだけがコンパイルできなくなります。`cargo build`も統合テストも通るのに単体テストだけが落ちるので、原因がわかりづらいです。

具体的には、`foo`の型`Thing`を組み立てるフィクスチャー`make() -> Thing`を別クレート`fixtures`に切り出し、型定義のある元クレート`foo`がそれをdev-dependencyに追加した状況です。`fixtures`単体のビルドも`foo`の統合テストも通りましたが、`foo`自身の単体テストだけが`error[E0308]: mismatched types`（`` expected `Thing`, found `foo::Thing` ``）で落ちました。dev-dependencyが循環している（`fixtures`は`foo`に依存し、`foo`は`fixtures`をdev-dependencyにする）ことがヒントですが、循環自体はビルド可能なので、それだけでは原因が見えません。

## 最小再現

### 構成

2クレートのworkspaceで再現します。

```
repro/
├── Cargo.toml
├── foo/
│   ├── Cargo.toml
│   └── src/
│       └── lib.rs
└── fixtures/
    ├── Cargo.toml
    └── src/
        └── lib.rs
```

```toml:Cargo.toml
[workspace]
members = ["foo", "fixtures"]
resolver = "2"
```

```toml:foo/Cargo.toml
[package]
name = "foo"
version = "0.1.0"
edition = "2021"

[dev-dependencies]
fixtures = { path = "../fixtures" }
```

```toml:fixtures/Cargo.toml
[package]
name = "fixtures"
version = "0.1.0"
edition = "2021"

[dependencies]
foo = { path = "../foo" }
```

```rust:foo/src/lib.rs
pub struct Thing(pub i32);

pub fn consume(_t: Thing) {}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn round_trip() {
        let t = fixtures::make(); // fixtures経由でfooの型を作り
        consume(t);               // foo自身の関数へ戻す
    }
}
```

```rust:fixtures/src/lib.rs
use foo::Thing;

pub fn make() -> Thing {
    Thing(0)
}
```

### 実行結果

```console:terminal
$ cargo build -p foo             # 通る
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.41s

$ cargo test -p foo --test it    # 統合テストも通る
     Running tests/it.rs
test from_integration ... ok

$ cargo test -p foo              # 自クレートの 単体テスト が落ちる
error[E0308]: mismatched types
  --> foo/src/lib.rs:11:17
   |
11 |         consume(t);               // foo自身の関数へ戻す
   |         ------- ^ expected `Thing`, found `foo::Thing`
   |         |
   |         arguments to this function are incorrect
   |
note: there are multiple different versions of crate `foo` in the dependency graph
  --> foo/src/lib.rs:1:1
   |
 1 | pub struct Thing(pub i32);
   | ^^^^^^^^^^^^^^^^ this is the expected type
   |
  ::: foo/src/lib.rs:1:1
   |
 1 | pub struct Thing(pub i32);
   | ---------------- this is the found type
```

`` note: there are multiple different versions of crate `foo` ``が核心です。`fixtures::make()`の返す`Thing`と、単体テスト側の`consume`が要求する`Thing`は、別インスタンスの`foo`に由来して食い違います。`` expected `Thing` ``と `` found `foo::Thing` `` が同じ`struct Thing`の定義行（`foo/src/lib.rs:1`）を二重に指しているのが、この「同名だが別物」の状況を端的に表しています。

## なぜ壊れるのか

まず登場人物と依存の向きを整理します。フィクスチャーを別クレート`fixtures`に切り出すと、`fixtures`は`foo`の型を組み立てるので`foo`に依存します。そのうえでその`fixtures`を`foo`自身のテストでも使いたいので、`foo`は`fixtures`をdev-dependencyに持ちます。fixtureをクレートとして共有し、かつ元クレートのテストでも使うという構造上、この`foo ⇄ fixtures`の循環は避けられません。Cargoは通常の（非dev）dependencyの循環は`error: cyclic package dependency`で拒否しますが、dev-dependencyを経由する循環は許容します。`foo`が`fixtures`をdev-dependencyにする構成はCargoとして正当で、ビルドも通ります。問題の所在は循環の有無ではなく、この構成のもとで`cargo test`が`foo`を2インスタンスにビルドし、同名の型が食い違うことにあります。

```html-embed
<svg class="wide" viewBox="0 0 680 255" role="img" aria-label="fixturesはfooに依存し、fooはfixturesをdev-dependencyに持つので循環する。barはfixturesをdev-dependencyに持つだけで循環しない">
  <defs>
    <marker id="h1w" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto"><path class="head" d="M0 0L10 5L0 10z"/></marker>
    <marker id="h1wc" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="13" markerHeight="13" orient="auto"><path class="head cyc" d="M0 0L10 5L0 10z"/></marker>
  </defs>
  <rect class="box" x="20" y="20" width="180" height="110" rx="8"/>
  <text class="t" x="110" y="68">crate foo</text>
  <text class="s" x="110" y="94"><tspan class="ja">型 </tspan>Thing / consume</text>
  <rect class="box" x="460" y="20" width="200" height="110" rx="8"/>
  <text class="t" x="560" y="68">crate fixtures</text>
  <text class="s" x="560" y="94">make() -&gt; foo::Thing</text>
  <rect class="box" x="460" y="185" width="200" height="60" rx="8"/>
  <text class="t" x="560" y="210">crate bar など</text>
  <text class="s ja" x="560" y="232">他の利用者</text>

  <line class="dep" x1="460" y1="52" x2="200" y2="52" marker-end="url(#h1w)"/>
  <text class="l" x="330" y="40">dependency（fooの型に依存）</text>
  <line class="dev cyc" x1="200" y1="98" x2="460" y2="98" marker-end="url(#h1wc)"/>
  <text class="l cyc" x="330" y="120">dev-dependency（この向きで循環になる）</text>
  <line class="dev" x1="560" y1="185" x2="560" y2="130" marker-end="url(#h1w)"/>
  <text class="l end" x="550" y="162">dev-dependency</text>
</svg>

<svg class="narrow" viewBox="0 0 340 404" role="img" aria-label="fixturesはfooに依存し、fooはfixturesをdev-dependencyに持つので循環する。barはfixturesをdev-dependencyに持つだけで循環しない">
  <defs>
    <marker id="h1n" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto"><path class="head" d="M0 0L10 5L0 10z"/></marker>
    <marker id="h1nc" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="13" markerHeight="13" orient="auto"><path class="head cyc" d="M0 0L10 5L0 10z"/></marker>
  </defs>
  <rect class="box" x="40" y="10" width="260" height="64" rx="8"/>
  <text class="t" x="170" y="37">crate foo</text>
  <text class="s" x="170" y="59"><tspan class="ja">型 </tspan>Thing / consume</text>
  <rect class="box" x="40" y="200" width="260" height="64" rx="8"/>
  <text class="t" x="170" y="227">crate fixtures</text>
  <text class="s" x="170" y="249">make() -&gt; foo::Thing</text>
  <rect class="box" x="40" y="330" width="260" height="64" rx="8"/>
  <text class="t" x="170" y="357">crate bar など</text>
  <text class="s ja" x="170" y="379">他の利用者</text>

  <line class="dep" x1="100" y1="200" x2="100" y2="74" marker-end="url(#h1n)"/>
  <text class="l halo" x="100" y="132">dependency</text>
  <text class="l halo" x="100" y="150">（fooの型に依存）</text>
  <line class="dev cyc" x1="240" y1="74" x2="240" y2="200" marker-end="url(#h1nc)"/>
  <text class="l cyc halo" x="240" y="123">dev-dependency</text>
  <text class="l cyc halo" x="240" y="141">（この向きで</text>
  <text class="l cyc halo" x="240" y="159">循環になる）</text>
  <line class="dev" x1="170" y1="330" x2="170" y2="264" marker-end="url(#h1n)"/>
  <text class="l halo" x="170" y="301">dev-dependency</text>
</svg>

<style>
  :root {
    --page: #fff;
    --text: #263548;
    --box: #f3f6fa;
    --line: #5b6b7f;
    --cycle: #c62828;
  }
  :root[data-theme="dark"] {
    --page: #151b24;
    --text: #e4ebf4;
    --box: #202b39;
    --line: #9aabbf;
    --cycle: #ff8a80;
  }
  body {
    margin: 0;
    background: var(--page);
    color: var(--text);
  }
  svg {
    display: block;
    width: 100%;
    height: auto;
    font-family: system-ui, sans-serif;
  }
  .narrow { display: none; max-width: 340px; margin: 0 auto; }
  @media (max-width: 640px) {
    .wide { display: none; }
    .narrow { display: block; }
  }
  .box { fill: var(--box); stroke: var(--line); stroke-width: 1.2; }
  text { fill: var(--text); text-anchor: middle; }
  .t { font-size: 15px; font-weight: 700; }
  .s { font-size: 12.5px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  .ja { font-family: system-ui, sans-serif; }
  .l { font-size: 12.5px; }
  .end { text-anchor: end; }
  .halo { paint-order: stroke; stroke: var(--page); stroke-width: 6px; stroke-linejoin: round; }
  line { stroke: var(--line); stroke-width: 1.6; }
  .dev { stroke-dasharray: 6 4; }
  .head { fill: var(--line); }
  line.cyc { stroke: var(--cycle); stroke-width: 2.4; }
  .head.cyc, text.cyc { fill: var(--cycle); }
  text.cyc { font-weight: 700; }
</style>
```

`bar`のように「`foo`の外側の利用者」が`fixtures`を使う経路には循環がなく、問題は起きません。壊れるのは循環の当事者である`foo`自身のテストだけです。

`cargo test -p foo`は`foo`を2回ビルドします。これはCargoの仕様で、[`cargo test`のドキュメント](https://doc.rust-lang.org/cargo/commands/cargo-test.html)には`--tests`について

> the lib target may be built twice (once as a unittest, and once as a dependency for binaries, integration tests, etc.)

とあります。単体テストバイナリは`foo`を`cfg(test)`付きでコンパイルした「test版」で、dev-dependencyの`fixtures`がリンクするのは`cfg(test)`の付かない「非test版」の`foo`です。

この2つはRustから見ると別クレートで、同名の型も別物として扱われます。`fixtures::make()`が返す`Thing`は非test版`foo`の`Thing`で作られ、それを受け取る単体テスト側の`consume`はテスト版`foo`の`Thing`を要求します。両者の型が同一ではないため`E0308`（mismatched types）になります。エラーの`` note: there are multiple different versions of crate `foo` ``が、この食い違いを名指ししています。

厄介なのは検知のすり抜けです。`fixtures`単体のビルドと`foo`の統合テスト（`tests/*.rs`は`foo`を1インスタンスだけリンクする別クレートなのでミスマッチが起きない）は通ってしまうため、壊れていることに気づきにくいです。壊れるのは「元クレート自身の単体テストが、自分の型を切り出し先クレート経由で受け取る」経路に限られます。

なお、フィクスチャーがトレイト境界を持つ総称型（例えば`make<S: Trait>() -> Thing<S>`）でも同じことが起きます。この場合は非test版の型がtest版の境界を満たせず、エラーが`error[E0277]: trait bound not satisfied`になりますが、原因は同一で「同名でも別インスタンスの型」に由来します。

## 対処法

フィクスチャーは別クレートへ切り出さず、元クレート内にfeature gateで置きます。これで`fixtures`クレートがなくなり、`foo ⇄ fixtures`の循環も消えます。効いているのは循環の除去そのものというより、単体テストがフィクスチャーを同じ`foo`インスタンス内の`crate::test_fixtures`として見る点です。同じインスタンスなので、型が二重化しません。

```html-embed
<svg class="wide" viewBox="0 0 680 300" role="img" aria-label="crate fooの中で、単体テストがmod test_fixturesのmake()から同一インスタンスのThingを受け取り、consumeに渡す">
  <defs>
    <marker id="h2w" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto"><path class="head" d="M0 0L10 5L0 10z"/></marker>
  </defs>
  <rect class="crate" x="4" y="4" width="672" height="290" rx="10"/>
  <text class="ct" x="20" y="30">crate foo<tspan class="cn">（フィクスチャーを内蔵・型は1インスタンス）</tspan></text>
  <rect class="box" x="30" y="60" width="170" height="64" rx="8"/>
  <text class="t" x="115" y="87">単体テスト</text>
  <text class="s" x="115" y="109">#[cfg(test)]</text>
  <rect class="box" x="440" y="60" width="210" height="64" rx="8"/>
  <text class="t m" x="545" y="87">mod test_fixtures</text>
  <text class="s" x="545" y="109">#[cfg(any(test, feature))]</text>
  <rect class="box" x="240" y="200" width="200" height="64" rx="8"/>
  <text class="t" x="340" y="237">型 <tspan class="m">Thing / consume</tspan></text>

  <line x1="200" y1="92" x2="440" y2="92" marker-end="url(#h2w)"/>
  <text class="l m" x="320" y="82">crate::test_fixtures::make()</text>
  <text class="l" x="320" y="110">同一インスタンスの<tspan class="m">Thing</tspan></text>
  <path d="M115 124V232H240" marker-end="url(#h2w)"/>
  <text class="l start" x="125" y="182"><tspan class="m">consume(t)</tspan> に渡す</text>
  <path d="M545 124V232H440" marker-end="url(#h2w)"/>
</svg>

<svg class="narrow" viewBox="0 0 340 420" role="img" aria-label="crate fooの中で、単体テストがmod test_fixturesのmake()から同一インスタンスのThingを受け取り、consumeに渡す">
  <defs>
    <marker id="h2n" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto"><path class="head" d="M0 0L10 5L0 10z"/></marker>
  </defs>
  <rect class="crate" x="4" y="4" width="332" height="412" rx="10"/>
  <text class="ct" x="16" y="28">crate foo</text>
  <text class="cn" x="16" y="48">（フィクスチャーを内蔵・型は1インスタンス）</text>
  <rect class="box" x="20" y="66" width="230" height="60" rx="8"/>
  <text class="t" x="135" y="91">単体テスト</text>
  <text class="s" x="135" y="113">#[cfg(test)]</text>
  <rect class="box" x="20" y="226" width="230" height="60" rx="8"/>
  <text class="t m" x="135" y="251">mod test_fixtures</text>
  <text class="s" x="135" y="273">#[cfg(any(test, feature))]</text>
  <rect class="box" x="20" y="346" width="230" height="56" rx="8"/>
  <text class="t" x="135" y="379">型 <tspan class="m">Thing / consume</tspan></text>

  <line x1="135" y1="126" x2="135" y2="226" marker-end="url(#h2n)"/>
  <text class="l m halo" x="135" y="170">crate::test_fixtures::make()</text>
  <text class="l halo" x="135" y="188">同一インスタンスの<tspan class="m">Thing</tspan></text>
  <line x1="135" y1="286" x2="135" y2="346" marker-end="url(#h2n)"/>
  <path d="M250 96H295V374H250" marker-end="url(#h2n)"/>
  <text class="l m halo" x="295" y="230">consume(t)</text>
  <text class="l halo" x="295" y="248">に渡す</text>
</svg>

<style>
  :root {
    --page: #fff;
    --text: #263548;
    --crate: #f7f9fc;
    --box: #e8eef5;
    --line: #5b6b7f;
  }
  :root[data-theme="dark"] {
    --page: #151b24;
    --text: #e4ebf4;
    --crate: #1a222d;
    --box: #26334a;
    --line: #9aabbf;
  }
  body {
    margin: 0;
    background: var(--page);
    color: var(--text);
  }
  svg {
    display: block;
    width: 100%;
    height: auto;
    font-family: system-ui, sans-serif;
  }
  .narrow { display: none; max-width: 340px; margin: 0 auto; }
  @media (max-width: 640px) {
    .wide { display: none; }
    .narrow { display: block; }
  }
  .crate { fill: var(--crate); stroke: var(--line); stroke-width: 1.6; }
  .box { fill: var(--box); stroke: var(--line); stroke-width: 1.2; }
  text { fill: var(--text); text-anchor: middle; }
  .ct { font-size: 15px; font-weight: 700; text-anchor: start; }
  .cn { font-size: 12.5px; font-weight: 400; text-anchor: start; }
  .t { font-size: 15px; font-weight: 700; }
  .s { font-size: 12.5px; }
  .s, .m { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  .l { font-size: 12.5px; }
  .start { text-anchor: start; }
  .halo { paint-order: stroke; stroke: var(--crate); stroke-width: 6px; stroke-linejoin: round; }
  line, path { stroke: var(--line); stroke-width: 1.6; fill: none; }
  .head { fill: var(--line); stroke: none; }
</style>
```

```rust:foo/src/lib.rs
#[cfg(any(test, feature = "test-fixtures"))]
pub mod test_fixtures; // pub fn make() -> Thing { ... }
```

```toml:foo/Cargo.toml
[features]
test-fixtures = []

[dev-dependencies]
foo = { path = ".", features = ["test-fixtures"] }
```

- `cfg(test)`はそのクレート自身のテストビルドにしか付かず、クレート境界を越えない。だから`foo`自身の単体テストは`test`側から自動で入る。外から使わせるには`test-fixtures` featureを立てる。`any`はこの2経路を束ねている。
- その`test-fixtures`の立て方は2通り。他クレートはdev-dependencyで`foo = { ..., features = ["test-fixtures"] }`。`foo`自身の`tests/*.rs`（別クレート扱い）は自己dev-dependency（上記`[dev-dependencies]`）で有効化する。これで手元の`cargo test`がそのまま通る。
- `resolver = "2"`なら、dev-dependency経由で有効にしたfeatureは通常の`cargo build`に統合されず、feature gateしたフィクスチャーも通常ビルドのコンパイル対象にならない（`cargo test`や`--all-targets`など`tests`を含むビルドでは統合される）。ソースはデフォルトで配布パッケージに同梱され、`test-fixtures`を有効にした利用者から`foo::test_fixtures`が公開APIとして見える。

## まとめ

別クレートに切り出したフィクスチャーを元クレートがdev-dependencyにすると、`cargo test`が元クレートをtest版と非test版の2インスタンスでビルドし、両者の同名の型が食い違うため、元クレート自身の単体テストだけがコンパイルできなくなります。`cargo build`も統合テストも通るぶん気づきにくいです。壊れるのは元クレートの型に依存するフィクスチャーを自身の単体テストへ戻す経路に限られるので、そのフィクスチャーは別クレートにせず、元クレート内に`#[cfg(any(test, feature = "..."))] pub mod`で置き、他クレートからはfeature付きdev-dependencyで使うのが安全です。共有したいだけなら別クレート化は不要で、切り出しの候補になるのは元クレートに依存しないフィクスチャー（循環しないもの）に限られます。`foo`自身の統合テストは、`test-fixtures`付きの自己dev-dependencyを足せば素の`cargo test`で通ります。テスト専用featureなので、消費者が通常触ることはなく、有効化するのはテストを走らせる側だけです。

## 参考

- [cargo test — The Cargo Book](https://doc.rust-lang.org/cargo/commands/cargo-test.html) — `--tests`の項に"the lib target may be built twice"の記述
- [Dev-dependencies — Rust By Example](https://doc.rust-lang.org/rust-by-example/testing/dev_dependencies.html) — dev-dependencyの基本
- [Feature resolver version 2 — The Cargo Book](https://doc.rust-lang.org/cargo/reference/resolver.html#feature-resolver-version-2) — `resolver = "2"`でdev-dependency由来のfeatureが通常ビルドに漏れない
