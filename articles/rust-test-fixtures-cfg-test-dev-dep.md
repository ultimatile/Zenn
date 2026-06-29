---
title: "dev-dependency cycle と cfg(test) で自クレートの unit test が壊れる"
emoji: "🦀"
type: "tech"
topics: ["rust", "cargo"]
published: false
register: almost
---

:::message
これは記事化前の **HANDOFF（作業メモ）** です。文体・句読点・タイトルは暫定で、記事化の開始時に確定ゲート（CLAUDE.md）で決め直します。最小再現は `cargo` 実機で確認済みです。
:::

## TL;DR

- あるクレートのテスト用 fixture を別クレートに切り出し、元クレートがそれを dev-dependency にすると、元クレート自身の `#[cfg(test)]` unit test がコンパイルできなくなる
- 原因は `cargo test` が元クレートを「`--cfg test` 版」と「非 test 版」の2インスタンスでビルドし、両者の型が別物になること
- `cargo build` も統合テスト（`tests/*.rs`）も通るので「動く」と誤認しやすい
- 対処は別クレートにせず、fixture を元クレート内に `#[cfg(any(test, feature = "..."))] pub mod` で置くこと

## 何が起きたか

ジェネリックな fixture builder（例えばあるトレイト境界 `S: Sector` を持つ `make<S>() -> Thing<S>`）を、複数クレートのテストで共有したくなり別クレート `fixtures` に切り出しました。`fixtures` は型定義のある元クレート `foo` に依存し、`foo` 側は `fixtures` を dev-dependency に追加します（dev-dependency の循環）。`fixtures` 単体のビルドも、`foo` の統合テストも通りました。ところが `foo` 自身の unit test だけが `error[E0277]: the trait bound \`U1: foo::Sector\` is not satisfied` で落ちました。

## 最小再現

2クレートの workspace で再現します。

```
repro/
  Cargo.toml          # [workspace] members = ["foo", "fixtures"], resolver = "2"
  foo/Cargo.toml      # [dev-dependencies] fixtures = { path = "../fixtures" }
  foo/src/lib.rs
  fixtures/Cargo.toml # [dependencies] foo = { path = "../foo" }
  fixtures/src/lib.rs
```

```rust:foo/src/lib.rs
pub trait Sector {}
pub struct U1;
impl Sector for U1 {}

pub struct Thing<S: Sector>(pub core::marker::PhantomData<S>);
pub fn consume<S: Sector>(_t: Thing<S>) {}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn round_trip() {
        let t = fixtures::make::<U1>(); // fixtures 経由で foo の型を作り
        consume(t);                     // foo 自身の関数へ戻す
    }
}
```

```rust:fixtures/src/lib.rs
use foo::{Sector, Thing};

pub fn make<S: Sector>() -> Thing<S> {
    Thing(core::marker::PhantomData)
}
```

```console
$ cargo build -p foo          # 通る
    Finished `dev` profile ...

$ cargo test -p foo           # 自クレートの unit test が落ちる
error[E0277]: the trait bound `U1: foo::Sector` is not satisfied
 --> foo/src/lib.rs:14:34
note: there are multiple different versions of crate `foo` in the dependency graph
```

`note: there are multiple different versions of crate \`foo\`` が核心です。`fixtures::make::<U1>()` が返す `Thing<U1>` の `U1`/`Sector` と、unit test 側の `consume` が要求する `U1`/`Sector` が、別インスタンスの `foo` 由来で食い違います。

## 何が問題か

`cargo test -p foo` は `foo` を2回ビルドします。unit test バイナリは `foo` を `--cfg test` でコンパイルした「テスト版」です。一方 dev-dependency の `fixtures` がリンクするのは `--cfg test` の付かない「非 test 版」の `foo` です。この2つは Rust にとって別クレートで、同名の型・トレイトも別物として扱われます。unit test（テスト版 `foo` の中身）が `fixtures`（非 test 版 `foo` にリンク）の戻り値を受け取ると、型 identity が一致せず境界を満たせません。

厄介なのは検知のすり抜けです。`fixtures` 単体ビルドと `foo` の統合テスト（`tests/*.rs` は `foo` を1インスタンスでリンクする別クレート）は問題なく通るため、「ビルドできる＝OK」の浅い確認では壊れていることに気づけません。壊れるのは「元クレート自身の unit test が、自分の型を切り出し先クレート経由で受け取る」経路に限られます。

ジェネリック特有でもありません。具体型でも、テスト版 `foo` の函数に非 test 版 `foo` の値を渡せば mismatch になります。ジェネリックだと「trait bound not satisfied」、具体型だと「mismatched types / multiple different versions of crate」として現れる差だけです。

## 現状の対処法

fixture を別クレートにせず、元クレート内に feature gate で置きます。

```rust:foo/src/lib.rs
#[cfg(any(test, feature = "test-fixtures"))]
pub mod test_fixtures; // pub fn make<S: Sector>() -> Thing<S> { ... }
```

```toml:foo/Cargo.toml
[features]
test-fixtures = []

[dev-dependencies]
# foo 自身の統合テスト（別クレート）から arnet 風に foo::test_fixtures を使うため、
# feature を有効にした自己 dev-dependency を足す
foo = { path = ".", features = ["test-fixtures"] }
```

- `foo` 自身の unit test は `cfg(test)` で同一インスタンスの `crate::test_fixtures` を見るので壊れない
- 他クレートは dev-dependency で `foo = { ..., features = ["test-fixtures"] }` を有効化し `foo::test_fixtures` を使う
- `resolver = "2"` なら dev-dependency 由来の feature は通常ビルド・公開ビルドに漏れず、fixture コードは出荷物に入らない

## 失敗モード（lean）

- 別クレート fixture × 元クレートの `#[cfg(test)]` unit test が、切り出し先経由で自分の型を受け取る → `E0277` /「multiple different versions of crate」
- `cargo build` と統合テストは通るので「動く」と誤認する（壊れるのは unit test 経路だけ）
- ジェネリック非依存。具体型は「mismatched types」、ジェネリックは「trait bound not satisfied」で出るだけ
- 「dev-dependency の循環はビルドが通るか」だけの確認では検知できない（循環自体はビルド可能）

## 記事化 TODO / 未確認

- 文体・句読点の確定（CLAUDE.md の確定ゲート）。タイトルも仮
- `programs/rust-test-fixtures-cfg-test-dev-dep/` に最小再現を置く（検証済みコードあり）
- どこまで「2回ビルドされる」挙動を Cargo 公式ドキュメントで裏取りできるか確認（本文は実機の `note` 出力ベース）
- 代替案の比較に触れるか（unit test を統合テストへ移す案は内部 `pub(crate)` 依存があると不可、等）
