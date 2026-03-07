---
title: "Rustのinherent impl衝突（E0592）の原因と回避法"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [rust]
published: false
---

## はじめに

Rustでジェネリクスを使ったライブラリを書いていると、「同じ型に対して複数の`impl`が衝突する」というコンパイルエラー（E0592）に遭遇することがあります。
これはinherent impl（型に直接定義するメソッド）の重複チェックによるものです。

## 実際に遭遇した問題

### 背景

テンソル計算ライブラリを開発中、多次元配列を表現する`Tensor<T>`に対して浮動小数点数型（`f32`、`f64`）とそれらの複素数型の両方をサポートしようとしました。
Rustの標準ライブラリには複素数型がないため、[`num_complex`](https://crates.io/crates/num-complex)クレートの`Complex<T>`を使います。
このクレートは加算などの算術演算子や数学関数が実装済みです。

### 問題: implの衝突

実数と複素数でノルム計算の実装が異なるため、別々の`impl`を書こうとしました:

```rust
use num_complex::Complex;
use num_traits::Float;

struct Tensor<T> {
    data: Vec<T>,
}

impl<T: Float> Tensor<T> {
    fn norm(&self) -> T {
        self.data
            .iter()
            .copied()
            .map(|x| x * x)
            .fold(T::zero(), |acc, x| acc + x)
            .sqrt()
    }
}

impl<T: Float> Tensor<Complex<T>> {
    fn norm(&self) -> T {
        self.data
            .iter()
            .copied()
            .map(|z| z.norm_sqr())
            .fold(T::zero(), |acc, x| acc + x)
            .sqrt()
    }
}
```

これは以下のようなコンパイルエラー（E0592）になります。

```shell-session
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

## なぜ衝突するのか

2つのinherent impl のヘッダが重なりうる場合、コンパイラはE0592を出します。
上記の例では、将来的に`Complex<T>`が`Float`を実装する可能性を排除できないため、`Tensor<T>`（`T = Complex<U>`のとき）と`Tensor<Complex<T>>`が同じ型を指しうるとコンパイラは判断します。
実際には`num_complex::Complex`は`Float`を実装していませんし、`Float`は全順序（`Ord`）を要求するため複素数への実装は不自然ですが、コンパイラは保守的に判断します。

:::details 補足: コヒーレンスルールとの関係
E0592はinherent implの重複チェックであり、Rust Referenceで定義される[コヒーレンスルール](https://doc.rust-lang.org/reference/items/implementations.html#trait-implementation-coherence)（trait implに対する孤児ルール＋重複チェック）とは厳密には別のルールです。
ただし「upstream crateが将来trait implを追加する可能性」を考慮する推論ロジックは両者で共通しています。
trait implの衝突（E0119）については[パターン3の注意点](#3-extension-trait（設計に注意）)で触れます。
:::

## 回避パターン

impl衝突を回避するための方法はいくつかあります。

### 1. 補助トレイトによる impl の1本化

実数/複素数の差分を補助トレイト（`Scalar`）に押し込み、`Tensor` 側の `impl` を1本にする方法です。

```rust
use num_complex::Complex;
use num_traits::Float;

trait Scalar: Copy {
    type Real: Float;

    fn abs_sq(self) -> Self::Real;
}

impl Scalar for f64 {
    type Real = f64;
    fn abs_sq(self) -> Self::Real {
        self * self
    }
}

impl Scalar for Complex<f64> {
    type Real = f64;
    fn abs_sq(self) -> Self::Real {
        self.norm_sqr()
    }
}

struct Tensor<T> {
    data: Vec<T>,
}

impl<T: Scalar> Tensor<T> {
    fn norm(&self) -> T::Real {
        self.data
            .iter()
            .copied()
            .map(|x| x.abs_sq())
            .fold(T::Real::zero(), |acc, x| acc + x)
            .sqrt()
    }
}
```

`Tensor` 側の `impl` が1本なので、衝突しません。

### 2. Newtype で型を分離する

外部型をラップした新しい型を定義し、`Self` 型を明示的に分けることで衝突を回避する方法です。

```rust
use num_complex::Complex;
use num_traits::Float;

struct Real<T>(T);
struct Cplx<T>(Complex<T>);

struct Tensor<T> {
    data: Vec<T>,
}

impl<T: Float> Tensor<Real<T>> {
    fn norm(&self) -> T {
        self.data
            .iter()
            .map(|x| x.0 * x.0)
            .fold(T::zero(), |acc, x| acc + x)
            .sqrt()
    }
}

impl<T: Float> Tensor<Cplx<T>> {
    fn norm(&self) -> T {
        self.data
            .iter()
            .map(|z| z.0.norm_sqr())
            .fold(T::zero(), |acc, x| acc + x)
            .sqrt()
    }
}
```

メリット:

- 衝突条件が明確

デメリット:

- API利用者がラッパー型を意識する必要がある

### 3. Extension trait（設計に注意）

Extension trait も有効ですが、**定義の仕方** が重要です。

```rust
use num_complex::Complex;
use num_traits::Float;

struct Tensor<T> {
    data: Vec<T>,
}

trait TensorExt<R> {
    fn norm(&self) -> R;
}

impl<T: Float> TensorExt<T> for Tensor<T> {
    fn norm(&self) -> T {
        self.data
            .iter()
            .copied()
            .map(|x| x * x)
            .fold(T::zero(), |acc, x| acc + x)
            .sqrt()
    }
}

impl<T: Float> TensorExt<T> for Tensor<Complex<T>> {
    fn norm(&self) -> T {
        self.data
            .iter()
            .copied()
            .map(|z| z.norm_sqr())
            .fold(T::zero(), |acc, x| acc + x)
            .sqrt()
    }
}
```

この形なら2つ目の型引数を含めて重複しないため成立します。

注意点:

- `trait TensorExt { fn norm(&self) -> ... }` のように型引数なしにすると、元の問題と同じ衝突を踏みやすい
- 利用側で `use` が必要になる

### 4. Sealed trait で外部実装を禁止する

Sealed trait はimpl衝突の回避そのものではなく、補助トレイト（パターン1）と組み合わせて外部クレートからの実装を禁止するための仕組みです。

#### モジュールを使う版

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
    fn abs(self) -> Self::Real;
}
```

`mod sealed` 内の `Sealed` トレイトは外部から実装できないため、`Scalar` の実装を自クレート内に限定できます。

#### モジュールなし版（Rust 1.74 以降）

```rust
trait Sealed {}
impl Sealed for f32 {}
impl Sealed for f64 {}
impl Sealed for num_complex::Complex<f32> {}
impl Sealed for num_complex::Complex<f64> {}

#[allow(private_bounds)]
pub trait Scalar: Sealed {
    type Real;
    fn abs(self) -> Self::Real;
}
```

この形でも「下流クレートが `Scalar` を実装できない」という意味では sealed として機能します。

ただし公開 trait で private supertrait を使うため、`private_bounds` 警告が出ます。
そのため `#[allow(private_bounds)]` で警告を抑制する必要があります。
`mod sealed { pub trait Sealed {} ... }` パターンは、この警告を避けつつ意図を明示しやすいのが利点です。

## どれを選ぶべきか

| 観点 | 1. 補助トレイト1本化 | 2. Newtype | 3. Extension trait | 4. Sealed |
|------|---------------------|-----------|-------------------|-----------|
| impl衝突回避 | ◎ | ◎ | ◎ | ×（単体では不可） |
| APIの自然さ | ◎ | △ | △ | - |
| 外部実装の制御 | △ | △ | △ | ◎ |
| 実装コスト | ○ | ○ | ○ | ○ |

実務上は次の順が扱いやすいです。

1. まず `impl` を非重複化する（1本化/型分離/拡張trait）
2. 公開ライブラリなら `Sealed` を検討する

## 私のケースでの結論

テンソルライブラリでは以下を採用しました。

- `Tensor` 側は `impl<T: Scalar>` の1本化
- 実数/複素数の差分は `Scalar` 実装へ移譲
- 公開API安定化のため `Scalar` は `Sealed` で閉じる

これで、impl衝突の回避とAPI管理を役割分離できます。

## まとめ

- `impl` 衝突の直接原因は、重なりうる `impl` ヘッダ
- 回避の本体は `impl` を非重複にすること
- `Sealed` はimpl衝突の回避ではなく、外部実装禁止と将来互換のための仕組み
- `Newtype` と `Extension trait` は、設計条件を満たせば有効な回避策

## 参考

- [The Rust Reference - Coherence](https://doc.rust-lang.org/reference/items/implementations.html#trait-implementation-coherence)
- [Rust API Guidelines - Sealed traits](https://rust-lang.github.io/api-guidelines/future-proofing.html#sealed-traits-protect-against-downstream-implementations-c-sealed)
- [RFC 1210 - Specialization](https://rust-lang.github.io/rfcs/1210-impl-specialization.html)
- [Rust Forum - Why does Sealed trait require a module? (#2)](https://users.rust-lang.org/t/why-does-sealed-trait-require-a-module/134702/2)
