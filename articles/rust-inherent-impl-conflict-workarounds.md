---
title: "Rustのinherent impl衝突（E0592）の原因と回避法"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [rust]
published: true
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

実数と複素数でノルム計算の実装が異なるため、別々の`impl`を書こうとしました。
実数のノルムは$\sqrt{\sum_i x_i^2}$、複素数のノルムは$\sqrt{\sum_i |z_i|^2}$で、`Complex::norm_sqr()`は絶対値の二乗$|z|^2 = \left(\mathrm{Re}\,z\right)^2 + \left(\mathrm{Im}\,z\right)^2$を直接計算します:

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

2つのinherent implの対象型が重なりうる場合、コンパイラはE0592を出します。
上記の例では、将来的に`Complex<T>`が`Float`を実装する可能性を排除できないため、`Tensor<T>`（`T = Complex<U>`のとき）と`Tensor<Complex<T>>`が同じ型を指しうるとコンパイラは判断します。
実際には`num_complex::Complex`は`Float`を実装していませんし、`Float`は`PartialOrd`を要求するため順序を持たない複素数への実装は不自然ですが、コンパイラは保守的に判断します。

:::details 補足: コヒーレンスルールとの関係
E0592はinherent implの重複チェックであり、Rust Referenceで定義される[コヒーレンスルール](https://doc.rust-lang.org/reference/items/implementations.html#trait-implementation-coherence)（trait implに対する孤児ルール＋重複チェック）とは厳密には別のルールです。
ただし「上流クレートが将来trait implを追加する可能性」を考慮する推論ロジックは両者で共通しています。
trait implの衝突（E0119）については[拡張トレイトの注意点](#拡張トレイト)で触れます。
:::

## 回避パターン

### ニュータイプパターンで型を分離する

E0592の回避策としてよく紹介されるのが、外部型をラップした新しい型を定義し、対象型を明示的に分ける方法です。

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
        // ...
    }
}

impl<T: Float> Tensor<Cplx<T>> {
    fn norm(&self) -> T {
        // ...
    }
}
```

`Tensor<Real<T>>`と`Tensor<Cplx<T>>`は完全に別の型なので衝突しません。
ただし、メソッドを追加するたびに各ニュータイプ用のimplに同じシグネチャを書く必要があります。型の追加よりもメソッドの追加が多いケースでは、ボイラープレートが急速に増えます。

### 補助トレイトによるimplの1本化

実数/複素数の差分を補助トレイト（`Scalar`）に押し込み、`Tensor`側の`impl`を1本にする方法です。

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

`Tensor`側の`impl`が1本なので衝突しません。メソッドを追加しても`Tensor`側は1箇所で済み、型ごとの差分は`Scalar`の実装に閉じ込められます。
型の追加よりもメソッドの追加が圧倒的に多いケースでは、ニュータイプよりもこちらの方がスケールします。私のテンソルライブラリではこの方法を採用しました。

### 拡張トレイト

拡張トレイトは本来、既存の型に新しいメソッドを追加するためのパターンですが、E0592の回避にも使えなくはありません。ただし、定義の仕方には注意が必要です。

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
        // ...
    }
}

impl<T: Float> TensorExt<T> for Tensor<Complex<T>> {
    fn norm(&self) -> T {
        // ...
    }
}
```

この形なら2つ目の型引数を含めて重複しないため成立します。

注意点:

- トレイトに型引数がないと（`trait TensorExt { fn norm(&self) -> ... }`）、`TensorExt for Tensor<T>`と`TensorExt for Tensor<Complex<T>>`が同一トレイトの重複実装となり、[コヒーレンスルール](https://doc.rust-lang.org/reference/items/implementations.html#trait-implementation-coherence)に抵触する（E0119）。型引数`R`を持たせることで`TensorExt<T>`と`TensorExt<Complex<T>>`が別のトレイトとして扱われ、衝突を回避できる
- ニュータイプと同様、メソッド追加のたびに型の数だけimplを書く必要がある
- 利用側で毎回`use`が必要になる
