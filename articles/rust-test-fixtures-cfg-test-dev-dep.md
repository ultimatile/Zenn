---
title: "dev-dependency cycleとcfg(test)で自クレートのunit testが壊れる"
emoji: "🦀"
type: "tech"
topics: ["rust", "cargo"]
published: false
register: almost
---

## TL;DR

- 別クレートに切り出したfixtureを元クレートがdev-dependencyにすると、元クレート自身の`#[cfg(test)]` unit testがコンパイルできなくなる。
- 原因は`cargo test`が元クレートを「`cfg(test)`あり版」と「なし版」の2インスタンスでビルドし、両者の同名の型が別物になること。
- `cargo build`も統合テスト（`tests/*.rs`）も通るので「動く」と誤認しやすい。壊れるのは元クレート自身のunit test経路だけ。
- 対処は別クレートにせず、fixtureを元クレート内に`#[cfg(any(test, feature = "..."))] pub mod`で置くこと。

## はじめに

あるクレートのテスト用ヘルパー（fixture）を複数のクレートで使い回したくなることがあります。素直な発想はfixtureを独立したクレートに切り出して共有することですが、元クレートの型に依存するfixtureでこれをやると、元クレート自身の`#[cfg(test)]` unit testだけがコンパイルできなくなります。`cargo build`も統合テストも通るのにunit testだけが落ちるので、原因にたどり着きにくい罠です。

具体的には、あるトレイト境界（例えば`S: Sector`）を持つジェネリックなfixture builder `make<S>() -> Thing<S>`を別クレート`fixtures`に切り出し、型定義のある元クレート`foo`がそれをdev-dependencyに追加した状況です。`fixtures`単体のビルドも`foo`の統合テストも通りましたが、`foo`自身のunit testだけが``error[E0277]: the trait bound `U1: foo::Sector` is not satisfied``で落ちました。dev-dependencyが循環している（`fixtures`は`foo`に依存し、`foo`は`fixtures`をdev-dependencyにする）ことがヒントですが、循環自体はビルド可能なので、それだけでは原因が見えません。

## 最小再現

2クレートのworkspaceで再現します。

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
        let t = fixtures::make::<U1>(); // fixtures経由でfooの型を作り
        consume(t);                     // foo自身の関数へ戻す
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
$ cargo build -p foo             # 通る
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.41s

$ cargo test -p foo --test it    # 統合テストも通る
     Running tests/it.rs
test from_integration ... ok

$ cargo test -p foo              # 自クレートの unit test が落ちる
error[E0277]: the trait bound `U1: foo::Sector` is not satisfied
  --> foo/src/lib.rs:14:34
   |
14 |         let t = fixtures::make::<U1>();
   |                                  ^^ unsatisfied trait bound
   |
note: there are multiple different versions of crate `foo` in the dependency graph
```

`` note: there are multiple different versions of crate `foo` ``が核心です。`fixtures::make::<U1>()`が返す`Thing<U1>`の`U1`/`Sector`と、unit test側の`consume`が要求する`U1`/`Sector`が、別インスタンスの`foo`に由来して食い違います。この最小再現一式は[`programs/rust-test-fixtures-cfg-test-dev-dep/`](https://github.com/ultimatile/Zenn/tree/main/programs/rust-test-fixtures-cfg-test-dev-dep)に置いています。

## なぜ壊れるのか

`cargo test -p foo`は`foo`を2回ビルドします。これはCargoの仕様で、[`cargo test`のドキュメント](https://doc.rust-lang.org/cargo/commands/cargo-test.html)には`--tests`について"the lib target may be built twice (once as a unittest, and once as a dependency for binaries, integration tests, etc.)"とあります。unit testバイナリは`foo`を`cfg(test)`付きでコンパイルした「テスト版」で、dev-dependencyの`fixtures`がリンクするのは`cfg(test)`の付かない「非test版」の`foo`です。

この2つはRustから見ると別クレートで、同名の型・トレイトも別物として扱われます。`fixtures::make::<U1>()`が返す`Thing<U1>`は非test版`foo`の`U1`/`Sector`で作られ、それを受け取るunit test側の`consume`はテスト版`foo`の`U1`/`Sector`を要求します。両者の型の同一性が一致しないため`U1: Sector`の境界を満たせず、`E0277`になります。エラーの`` note: there are multiple different versions of crate `foo` ``が、この食い違いを名指ししています。

厄介なのは検知のすり抜けです。`fixtures`単体のビルドと`foo`の統合テスト（`tests/*.rs`は`foo`を1インスタンスだけリンクする別クレートなのでmismatchが起きない）は通ってしまうため、「ビルドできる＝OK」の浅い確認では壊れていることに気づけません。壊れるのは「元クレート自身のunit testが、自分の型を切り出し先クレート経由で受け取る」経路に限られます。「dev-dependencyの循環はビルドが通るか」だけを確かめても、循環自体はビルド可能なので検知できません。

ジェネリック特有の問題でもありません。具体型でも、テスト版`foo`の函数に非test版`foo`の値を渡せばmismatchになります。違いは現れ方だけで、ジェネリックなら`trait bound not satisfied`、具体型なら`mismatched types`として出ます。

## 対処法

fixtureを別クレートに切り出さず、元クレート内にfeature gateで置きます。

```rust:foo/src/lib.rs
#[cfg(any(test, feature = "test-fixtures"))]
pub mod test_fixtures; // pub fn make<S: Sector>() -> Thing<S> { ... }
```

```toml:foo/Cargo.toml
[features]
test-fixtures = []

[dev-dependencies]
# 自身の統合テスト（別クレート）からfoo::test_fixturesを使うため、
# featureを有効にした自己dev-dependencyを足す
foo = { path = ".", features = ["test-fixtures"] }
```

- `foo`自身のunit testは`cfg(test)`で同一インスタンスの`crate::test_fixtures`を見るので壊れない。
- 他クレートはdev-dependencyで`foo = { ..., features = ["test-fixtures"] }`を有効化し、`foo::test_fixtures`を使う。
- `resolver = "2"`ならdev-dependency由来のfeatureは通常ビルド・公開ビルドに漏れず、fixtureコードは出荷物に入らない。

## まとめ

別クレートに切り出したfixtureを元クレートがdev-dependencyにすると、`cargo test`が元クレートをテスト版と非test版の2インスタンスでビルドし、両者の同名の型が食い違うため、元クレート自身のunit testだけがコンパイルできなくなります。`cargo build`も統合テストも通るぶん気づきにくい罠です。fixtureは別クレートにせず、元クレート内に`#[cfg(any(test, feature = "..."))] pub mod`で置き、他クレートからはfeature付きdev-dependencyで使うのが安全です。

## 参考

- [cargo test — The Cargo Book](https://doc.rust-lang.org/cargo/commands/cargo-test.html) — `--tests`の項に"the lib target may be built twice"の記述
- [Dev-dependencies — Rust By Example](https://doc.rust-lang.org/rust-by-example/testing/dev_dependencies.html) — dev-dependencyの基本
- [Feature resolver version 2 — The Cargo Book](https://doc.rust-lang.org/cargo/reference/resolver.html#feature-resolver-version-2) — `resolver = "2"`でdev-dependency由来のfeatureが通常ビルドに漏れない
