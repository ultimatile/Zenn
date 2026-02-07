---
title: "Rustのcoherenceルールと回避パターン"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [rust]
published: false
---

## はじめに

Rustでジェネリクスを使ったライブラリを書いていると、「同じ型に対して複数の`impl`が衝突する」というコンパイルエラーに遭遇することがあります。これはRustのcoherence（一貫性）ルールによるもので、型安全性を保証するための重要な制約です。

この記事では、実際に私が遭遇した問題を例に、coherenceルールの仕組みと、それを回避するための設計パターンを解説します。

## 実際に遭遇した問題

### 背景

テンソル計算ライブラリを開発中、`Tensor<T>`に対して実数型（`f32`, `f64`）と複素数型の両方をサポートする必要がありました。

Rustの標準ライブラリには複素数型がないため、[`num_complex`](https://crates.io/crates/num-complex)クレートの`Complex<T>`を使います。このクレートは演算子や数学関数が実装済みで、独自型を定義するメリットがありません。

### 問題: implの衝突

実数と複素数でノルム計算の実装が異なるため、別々の`impl`を書こうとしました:

```rust
use num_complex::Complex;
use num_traits::Float;

struct Tensor<T> {
    data: Vec<T>,
}

impl<T: Float> Tensor<T> {
    fn norm(&self) -> T { /* 実数用 */ }
}

impl<T: Float> Tensor<Complex<T>> {
    fn norm(&self) -> T { /* 複素数用 */ }
}
```

これはコンパイルエラー（E0592）になります。

```
error[E0592]: duplicate definitions with name `norm`
 --> src/main.rs:9:5
  |
9 |     fn norm(&self) -> T {
  |     ^^^^^^^^^^^^^^^^^^^ duplicate definitions for `norm`
...
15|     fn norm(&self) -> T {
  |     ------------------- other definition for `norm`
  |
  = note: upstream crates may add a new impl of trait `num_traits::Float`
          for type `num_complex::Complex<_>` in future versions
```

なぜでしょうか？

## coherenceルールとは

Rustのcoherenceルールは「ある型に対するtraitの実装は、プログラム全体で一意でなければならない」という規則です。

上記の例では、将来的に`Complex<T>`が`Float`を実装する可能性を排除できないため、コンパイラは2つの`impl`が重複する可能性があると判断します。実際には`num_complex::Complex`は`Float`を実装していませんが、コンパイラは保守的に判断します。

## 回避パターン

coherenceルールを回避するための主要なパターンを紹介します。

### 1. Newtype パターン

外部型をラップした新しい型を定義する方法です。

```rust
struct Real<T>(T);
struct Cplx<T>(Complex<T>);

impl<T: Float> Real<T> {
    fn norm(&self) -> T { /* ... */ }
}

impl<T: Float> Cplx<T> {
    fn norm(&self) -> T { /* ... */ }
}
```

なぜ回避できるか:
- `Real<T>`と`Cplx<T>`は完全に別の型として定義されている
- コンパイラにとって両者のimplは独立しており、重複の可能性がない
- 元の問題では`Tensor<T>`と`Tensor<Complex<T>>`が「将来`Complex<U>: Float`になったら重複する」という懸念があったが、Newtypeでは型自体が異なるためこの問題は発生しない

メリット:
- シンプルで理解しやすい
- 型レベルで実数/複素数を区別できる

デメリット:
- APIの利用者が常にラッパー型を意識する必要がある
- `.0`でのアクセスや`From`/`Into`の実装が必要

### 2. Extension trait パターン

外部型に対して新しいtraitを定義し、そのtraitを実装する方法です。

```rust
trait TensorExt<T> {
    fn norm(&self) -> T;
}

impl<T: Float> TensorExt<T> for Tensor<T> {
    fn norm(&self) -> T { /* ... */ }
}

impl<T: Float> TensorExt<T> for Tensor<Complex<T>> {
    fn norm(&self) -> T { /* ... */ }
}
```

なぜ回避できるか:
- `TensorExt<T>`が型パラメータを持つことがポイント
- `Tensor<f64>`には`TensorExt<f64>`、`Tensor<Complex<f64>>`にも`TensorExt<f64>`が実装される
- 仮に将来`Complex<U>: Float`が追加されても:
  - 1つ目のimplは`TensorExt<Complex<U>> for Tensor<Complex<U>>`を提供
  - 2つ目のimplは`TensorExt<U> for Tensor<Complex<U>>`を提供
  - これらは**異なるtrait**（`TensorExt<Complex<U>>`と`TensorExt<U>`）なので衝突しない

注意: 型パラメータなしの`trait TensorExt { fn norm(&self) -> T; }`で定義すると、元の問題と同様にcoherenceエラー（E0119）になる。

メリット:
- 既存の型をそのまま使える
- 標準ライブラリでも使われるパターン（`Iterator`の拡張など）

デメリット:
- 利用側で`use`が必要
- traitが公開APIの一部になる

### 3. Sealed trait パターン

自クレート内でのみ実装可能なtraitを定義し、許可する型を明示的に列挙する方法です。

```rust
mod sealed {
    pub trait Sealed {}
    impl Sealed for f32 {}
    impl Sealed for f64 {}
    impl Sealed for num_complex::Complex<f32> {}
    impl Sealed for num_complex::Complex<f64> {}
}

pub trait Scalar: sealed::Sealed + Clone + Copy {
    type Real;
    fn abs(self) -> Self::Real;
    fn conj(self) -> Self;
}

impl Scalar for f32 {
    type Real = f32;
    fn abs(self) -> f32 { self.abs() }
    fn conj(self) -> f32 { self }
}

impl Scalar for Complex<f32> {
    type Real = f32;
    fn abs(self) -> f32 { self.norm() }
    fn conj(self) -> Complex<f32> { self.conj() }
}
// f64, Complex<f64>も同様に実装
```

なぜ回避できるか:
- ジェネリックな`impl<T: Float>`ではなく、具体的な型（`f32`, `f64`, `Complex<f32>`, `Complex<f64>`）に対して個別にimplを書く
- 各implは完全に独立した型に対するものなので、重複の可能性がない
- 「将来`Complex<U>: Float`が追加されたら...」という問題は、そもそも`Float`境界を使わないため発生しない
- Sealedモジュールにより、外部クレートが新しい型に`Scalar`を実装することも防げる

メリット:
- `impl`が1本に集約され、coherence問題を根本回避
- 外部クレートからの実装を防げる（API安定性）
- 型ごとの振る舞いを明示的に定義できる

デメリット:
- サポートする型を追加するたびに実装が必要
- ジェネリックな拡張性は制限される

## パターンの組み合わせ

3つのパターンは直交しておらず、組み合わせて使うことができます。

| Newtype | Extension | Sealed | 実用性 | 用途 |
|:-------:|:---------:|:------:|:------:|------|
| - | - | - | - | 問題未解決 |
| ✓ | - | - | ◎ | 型をラップして区別 |
| - | ✓ | - | ◎ | traitで機能追加 |
| - | - | ✓ | ◎ | 許可型を固定 |
| - | ✓ | ✓ | ◎ | **trait公開 + 外部実装禁止** |
| ✓ | - | ✓ | △ | ラッパー型をSealed（通常は過剰） |
| ✓ | ✓ | - | ○ | ラッパー型にExtension trait |
| ✓ | ✓ | ✓ | × | 全部盛り（過剰） |

### Extension + Sealed（実用的な組み合わせ）

Extension traitをSealedにすることで、「traitとして公開するが外部実装は禁止」という設計が可能です。

```rust
mod sealed {
    pub trait Sealed {}
    impl Sealed for f32 {}
    impl Sealed for Complex<f32> {}
}

// 公開traitだが、外部クレートは実装できない
pub trait ScalarExt: sealed::Sealed {
    type Real;
    fn abs(self) -> Self::Real;
}

impl ScalarExt for f32 { /* ... */ }
impl ScalarExt for Complex<f32> { /* ... */ }
```

なぜ回避できるか:
- coherence回避の仕組みはSealed traitパターンと同じ。具体型に個別implしているため重複の可能性がない
- 「Extension」部分はcoherence回避には寄与せず、「traitとして公開APIにする」という設計上の役割
- `: sealed::Sealed`により外部クレートからの実装を防ぎつつ、trait自体は公開できる

標準ライブラリの`std::str::pattern::Pattern` traitがこのパターンを採用しています。`str::contains()`などに渡せる型を制限しつつ、traitとしてのAPIは公開しています。

### Newtype + Extension（特定のユースケース向け）

ラッパー型を作りつつ、Extension traitで共通インターフェースを提供するパターンです。

```rust
struct Real<T>(T);
struct Cplx<T>(Complex<T>);

trait NormExt {
    type Output;
    fn norm(&self) -> Self::Output;
}

impl<T: Float> NormExt for Real<T> { /* ... */ }
impl<T: Float> NormExt for Cplx<T> { /* ... */ }
```

なぜ回避できるか:
- coherence回避の仕組みはNewtypeパターンと同じ。`Real<T>`と`Cplx<T>`が完全に別の型なので重複の可能性がない
- 「Extension」部分はcoherence回避には寄与せず、共通インターフェースを提供する設計上の役割
- `NormExt`は型パラメータなしだが、impl対象が異なる型なので問題ない

型レベルで実数/複素数を区別しつつ、共通のtraitで操作したい場合に有用です。

## どのパターンを選ぶべきか

単独パターンの判断基準:

| 観点 | Newtype | Extension | Sealed |
|------|---------|-----------|--------|
| API の自然さ | △ ラッパー必要 | △ use必要 | ◎ 透過的 |
| 型の拡張性 | ◎ 自由 | ◎ 自由 | △ 明示的追加 |
| 外部実装の防止 | × | × | ◎ |
| 実装の手間 | ○ | ○ | △ 型ごとに実装 |

選択の指針:
- **Newtype**: 型レベルで区別したい場合、または一時的な回避策として
- **Extension**: 既存の型に機能を追加したい場合、利用者が`use`を許容できる場合
- **Sealed**: サポートする型が限定的で、APIの安定性を重視する場合
- **Extension + Sealed**: traitとして公開したいが、実装は自クレートに限定したい場合

## 私のケースでの選択: Sealed trait

テンソルネットワークライブラリでは、以下の理由からSealed traitパターンを採用しました。

1. **サポート型が限定的**: `f32`, `f64`, `Complex<f32>`, `Complex<f64>`の4種類のみ
2. **APIの自然さ**: 利用者が`use`やラッパー型を意識せずに使える
3. **将来の拡張**: `f16`/`bf16`追加時も同じパターンで対応可能
4. **外部実装の防止**: ライブラリの内部不変条件を保護できる

```rust
// 利用側のコード
let tensor: Tensor<f64> = Tensor::new(data);
let n = tensor.norm();  // 自然に呼び出せる

let complex_tensor: Tensor<Complex<f64>> = Tensor::new(complex_data);
let cn = complex_tensor.norm();  // 同じAPI
```

## 補足: specialization

Rust nightlyには`specialization`という機能があり、より具体的な型に対して特殊化した実装を提供できます。

```rust
#![feature(specialization)]

trait Norm {
    fn norm(&self) -> f64;
}

impl<T> Norm for Tensor<T> {
    default fn norm(&self) -> f64 { /* デフォルト実装 */ }
}

impl<T: Float> Norm for Tensor<T> {
    fn norm(&self) -> f64 { /* 実数用の特殊化 */ }
}
```

これにより、coherence問題を直接解決できる可能性がありますが、2025年現在もunstableであり、安定化の見通しは立っていません。プロダクションコードでは上記の3パターンのいずれかを使うことをお勧めします。

## まとめ

- Rustのcoherenceルールは型安全性のための重要な制約
- 回避パターンとしてNewtype、Extension trait、Sealed traitがある
- サポートする型が限定的でAPIの自然さを重視するならSealed traitが有効
- specializationは将来的な解決策だが、現時点ではnightly限定

## 参考

- [The Rust Reference - Coherence](https://doc.rust-lang.org/reference/items/implementations.html#trait-implementation-coherence)
- [Rust API Guidelines - Sealed traits](https://rust-lang.github.io/api-guidelines/future-proofing.html#sealed-traits-protect-against-downstream-implementations-c-sealed)
- [RFC 1210 - Specialization](https://rust-lang.github.io/rfcs/1210-impl-specialization.html)
