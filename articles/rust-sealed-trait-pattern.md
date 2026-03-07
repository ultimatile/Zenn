---
title: "Rustの外部実装を禁止するsealedトレイトパターン"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [rust]
published: true
---

## はじめに

Rustで公開ライブラリを書く際、定義したトレイトを外部クレートが自由に実装できてしまうと、将来の変更が難しくなります。
sealedトレイトパターンは、トレイトの実装を自クレート内に限定するための手法です。

## 問題: 外部クレートによるトレイト実装

以下のように公開トレイトを定義すると、外部クレートが自由に実装を追加できます。

```rust
pub trait Scalar {
    type Real;
    fn abs_sq(self) -> Self::Real;
}
```

ライブラリ側が想定しない型に`Scalar`が実装されると、将来メソッドを追加した際に下流クレートが壊れる可能性があります。

## sealedトレイトパターン

```rust
mod sealed {
    pub trait Sealed {}
    impl Sealed for f32 {}
    impl Sealed for f64 {}
    impl Sealed for num_complex::Complex<f32> {}
    impl Sealed for num_complex::Complex<f64> {}
}

pub trait Scalar: sealed::Sealed {
    type Real;
    fn abs_sq(self) -> Self::Real;
}
```

`mod sealed`内の`Sealed`トレイトは外部から実装できないため、`Scalar`の実装を自クレート内に限定できます。

### モジュールを使わない書き方（Rust 1.74 以降）

Rust 1.74以降では、モジュールを使わずにsealedトレイトを定義することもできます。

```rust
trait Sealed {}
impl Sealed for f32 {}
impl Sealed for f64 {}
impl Sealed for num_complex::Complex<f32> {}
impl Sealed for num_complex::Complex<f64> {}

#[allow(private_bounds)]
pub trait Scalar: Sealed {
    type Real;
    fn abs_sq(self) -> Self::Real;
}
```

この形でも「下流クレートが`Scalar`を実装できない」という意味ではsealedとして機能します。

ただし、パブリックトレイトでプライベートスーパートレイトを使うため、`private_bounds`警告が出ます。
そのため、`#[allow(private_bounds)]`で警告を抑制する必要があります。

## 参考

- [Rust API Guidelines - Sealed traits](https://rust-lang.github.io/api-guidelines/future-proofing.html#sealed-traits-protect-against-downstream-implementations-c-sealed)
- [Rust Forum - Why does Sealed trait require a module? (#2)](https://users.rust-lang.org/t/why-does-sealed-trait-require-a-module/134702/2)
