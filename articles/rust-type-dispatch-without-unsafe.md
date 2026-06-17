---
title: "補助トレイトで型ごとのカーネルにディスパッチする（TypeIdとunsafeを消す）"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [rust]
published: false
register: almost
---

## はじめに

[前作](https://zenn.dev/ultimatile/articles/rust-inherent-impl-conflict-workarounds)では、実数と複素数で実装が分かれる差分を補助トレイト`Scalar`に押し込み、`Tensor`側の`impl`を1本にしました。型ごとの違いは`Scalar`の実装に閉じ込められ、`Tensor`は`T: Scalar`だけを見ればよくなります。本記事は同じ発想を「ディスパッチ」に広げます。型ごとに別々のカーネル（`f64`用と複素数用で別のエントリポイントを持つ外部ライブラリ呼び出しのようなもの）を、ジェネリックな`fn op<T: Scalar>`から呼び分けるとき、つい`TypeId`で型を確かめて`unsafe`でポインタを読み替える実装に手が伸びます。しかしこの`unsafe`は不要で、前作と同じく「型ごとの差分を`Scalar`のメソッドに閉じ込める」だけで消せます。

## 問題: ジェネリックな`T`を型ごとのカーネルへ渡す

型ごとに別実装を持つ低レベルカーネルを考えます。線形代数ライブラリは`f64`と複素数で別々のエントリポイントを公開していることがあります。

```rust
use num_complex::Complex;

struct Gemm<'a, T> {
    a: &'a [T],
    n: usize,
}

fn gemm_f64(g: Gemm<'_, f64>) { /* f64 専用カーネル */ }
fn gemm_c64(g: Gemm<'_, Complex<f64>>) { /* 複素数専用カーネル */ }
```

これをジェネリックな入口から呼びたいとします。

```rust
fn gemm<T: Scalar>(g: Gemm<'_, T>) {
    // T は generic。gemm_f64 は Gemm<f64> を要求する。どう繋ぐ?
}
```

`T`が何かは実行時に`TypeId`で確かめられます。`f64`だと分かれば、`Gemm<T>`を`Gemm<f64>`として読み替えてカーネルに渡せます。

```rust
use std::any::TypeId;

fn gemm<T: Scalar + 'static>(g: Gemm<'_, T>) {
    if TypeId::of::<T>() == TypeId::of::<f64>() {
        gemm_f64(reinterpret::<T, f64>(g));
    } else if TypeId::of::<T>() == TypeId::of::<Complex<f64>>() {
        gemm_c64(reinterpret::<T, Complex<f64>>(g));
    }
}

// Gemm<T> を Gemm<U> として読み替える（T と U が同じ型のときだけ正しい）
fn reinterpret<T, U>(g: Gemm<'_, T>) -> Gemm<'_, U> {
    Gemm {
        a: unsafe { std::slice::from_raw_parts(g.a.as_ptr() as *const U, g.a.len()) },
        n: g.n,
    }
}
```

`reinterpret`が`unsafe`なのは、`Gemm<T>`のスライスを別の型`Gemm<U>`のスライスとしてポインタごと読み替えているからです。`TypeId`で`T == f64`を確かめた上での読み替えなので実際には正しいのですが、その正しさはコンパイラには見えず、`from_raw_parts`の前提（要素数とアラインメントの一致）は人間が保証するしかありません。

## この`unsafe`はFFI由来ではない

ここで`unsafe`が出るのは、FFIでも特殊なレイアウト操作でもありません。`gemm_f64`も`gemm_c64`も普通のRustの函数です。`unsafe`は単に「ジェネリックな`T`を具体型に橋渡しする」ためだけに使われています。

橋渡しが要るのは、型ごとのロジックを`gemm_f64`や`gemm_c64`という独立した函数に置き、`TypeId`で選んでいるからです。`T`はジェネリックなまま入口に入り、型が確定した函数に渡すところでキャストが必要になります。

ここで前作の`Scalar::abs_sq`を思い出します。型ごとの差分（実数は`self * self`、複素数は`norm_sqr()`）は、`Scalar`のメソッドの実装に閉じ込められていました。`impl Scalar for f64`の中では`Self`が`f64`に確定しているので、`self * self`がそのまま書けます。カーネルの呼び分けも、これと同じ場所に置けば同じ理屈でキャストが消えます。

## 解決: 振り分けを`Scalar`のメソッドにする

`Scalar`にカーネル呼び出しのメソッドを足します。

```rust
use num_complex::Complex;
use num_traits::Float;

trait Scalar: Copy {
    type Real: Float;
    fn abs_sq(self) -> Self::Real;

    // 追加: 型ごとのカーネルへの振り分け
    fn gemm(g: Gemm<'_, Self>);
}

impl Scalar for f64 {
    type Real = f64;
    fn abs_sq(self) -> Self::Real {
        self * self
    }
    fn gemm(g: Gemm<'_, f64>) {
        gemm_f64(g) // Self = f64 なのでキャスト不要
    }
}

impl Scalar for Complex<f64> {
    type Real = f64;
    fn abs_sq(self) -> Self::Real {
        self.norm_sqr()
    }
    fn gemm(g: Gemm<'_, Complex<f64>>) {
        gemm_c64(g)
    }
}
```

入口はメソッドを呼ぶだけです。

```rust
fn gemm<T: Scalar>(g: Gemm<'_, T>) {
    T::gemm(g)
}
```

`impl Scalar for f64`の中では`Self = f64`がコンパイル時に確定しています。`fn gemm(g: Gemm<'_, f64>)`は最初から`Gemm<f64>`を受け取るので、`gemm_f64`にそのまま渡せます。`TypeId`の分岐も、ポインタの読み替えも要りません。`unsafe`は消えます。

入口の`gemm`も`T: Scalar`だけを見て`T::gemm`を呼びます。どの型が来るかの振り分けは、`TypeId`の実行時比較ではなくコンパイラが型ごとに解決するので、`'static`境界も要らなくなります。

## op が増えたら: enum 1つにまとめる

カーネルが`gemm`だけなら上の形で十分ですが、`svd`、`qr`と増えると、`Scalar`にメソッドがopの数だけ生え、各`impl`にも同じ数だけ実装が並びます。これは前作のニュータイプ回避策で見た「メソッドを追加するたびに型の数だけ`impl`を書く」のと同じ構図です。

opを1つの enum にまとめると、`Scalar`側のメソッドを1本に保てます。

```rust
enum Op<'a, T> {
    Gemm(Gemm<'a, T>),
    Svd(Svd<'a, T>),
    // ...
}

trait Scalar: Copy {
    type Real: Float;
    fn abs_sq(self) -> Self::Real;
    fn dispatch(op: Op<'_, Self>); // op が増えても1本
}

impl Scalar for f64 {
    // type Real, abs_sq は省略
    fn dispatch(op: Op<'_, f64>) {
        match op {
            Op::Gemm(g) => gemm_f64(g),
            Op::Svd(s) => svd_f64(s),
        }
    }
}

fn gemm<T: Scalar>(g: Gemm<'_, T>) {
    T::dispatch(Op::Gemm(g))
}
```

opを足すときは、`Op`に variant を1つと、各`impl`の`match`に腕を1本ずつ足します。`Scalar`のトレイト面（メソッドの数）は1本のまま保てます。

## まとめ

型ごとに別実装を持つカーネルをジェネリックな入口から呼ぶとき、`TypeId`と`unsafe`でキャストするのは、型ごとのロジックを独立した函数に置いて実行時に選んでいるからです。前作と同じく、その差分を`Scalar`のメソッドに移すと、`impl`の中で`Self`が具体型に確定し、キャストが要らなくなります。型による振り分けはコンパイラに任せ、`unsafe`は本当に必要な場所（本物のFFIなど）だけに残せます。
