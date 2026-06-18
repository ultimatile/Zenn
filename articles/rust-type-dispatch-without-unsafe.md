---
title: "その`unsafe`は本当に必要か（エージェントが`Scalar`トレイトを使い損ねた話）"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [rust]
published: false
register: almost
---

## はじめに

[前作](https://zenn.dev/ultimatile/articles/rust-inherent-impl-conflict-workarounds)では、実数と複素数で実装が分かれる差分を補助トレイト`Scalar`に押し込み、`Tensor`側の`impl`を1本にしました。型ごとの違いは`Scalar`の実装に閉じ込められます。

ならば、型ごとに別のエントリポイントを持つカーネル（`f64`用と複素数用で函数が分かれている線形代数ライブラリなど）をジェネリックな入口から呼び分けるときも、答えは明らかです。`Scalar`にメソッドを1つ足し、各`impl`で対応するカーネルを呼べばよい。人間がこれを書くなら、まず迷いません。

ところが、この記事の元になったあるリファクタ（コード生成エージェントによるもの）は、そうしませんでした。`TypeId`で実行時に型を確かめ、`unsafe`でポインタを読み替えてconcreteなカーネルに渡す、というコードを書きました。`Scalar`というトレイトがすぐ隣にあるのにです。

なので本記事の問いは「どう直すか」ではありません。それは明らかです。問いは2つです。なぜ`Scalar`があるのに`unsafe`に走ったのか、そしてレビューで何を見れば気づけるのか。テイクホームは1行です。その`unsafe`、本当に必要ですか。

## 何が書かれていたか

型パラメータ付きの記述子`GemmDescriptor<T>`を、`ComputeBackend::gemm<T: Scalar>`のような抽象境界まで持ち上げます。カーネルは型ごとに分かれているので、内部で`T`をconcreteな型に戻してから呼びます。書かれていたのはこういう形です。

```rust
fn gemm<T: Scalar + 'static>(&self, desc: GemmDescriptor<'_, T>) -> Result<(), Error> {
    if TypeId::of::<T>() == TypeId::of::<f64>() {
        // Safety: T is f64, verified by TypeId.
        let desc = unsafe { reinterpret_desc::<T, f64>(desc) };
        gemm_f64(desc)
    } else if TypeId::of::<T>() == TypeId::of::<Complex<f64>>() {
        let desc = unsafe { reinterpret_desc::<T, Complex<f64>>(desc) };
        gemm_c64(desc)
    } else {
        Err(Error::NotSupported)
    }
}
```

`reinterpret_desc`は、`GemmDescriptor<T>`のスライスを`GemmDescriptor<f64>`としてポインタごと読み替える`unsafe`函数です。`TypeId`で`T == f64`を確かめた上での読み替えなので、soundnessとしては正しい。コメントにもそう書いてあります。

## その`unsafe`はFFI由来ではない

`gemm`という名前や「記述子」という語からは、BLASやFFIの境界のように見えます。しかし、少なくともこの文脈の`gemm_f64`や`gemm_c64`は、[`faer`](https://crates.io/crates/faer)（pure Rustの線形代数ライブラリ）のsafeなAPIを呼ぶ普通の函数でした。FFIも、特殊なレイアウト操作もありません。

つまりこの`unsafe`は「FFIだから必要」だったのではありません。`unsafe`は単に、ジェネリックな`T`をconcreteな型に橋渡しするためだけに使われていました。

## 変換問題ではなく、配置問題

この状況を「`Descriptor<T>`を`Descriptor<f64>`に変換する問題」と捉えると、`TypeId`で型を確かめて`from_raw_parts`や`ptr::read`で読み替える実装に、自然に流れます。soundnessのコメントも書けて、コンパイラも通ります。局所的には「解けた」ように見えます。

しかし、同じ状況は「型ごとの振る舞いをどこに置くか」という配置問題でもあります。そして`Scalar`のような補助トレイトがすでにあるなら、置き場所は最初から用意されています。`impl Scalar for f64`の中に入れば`Self = f64`は型システムが知っています。人間が`TypeId`比較の正しさをコメントで保証する必要はありません。

やることは、振り分けを`Scalar`のメソッドに移すだけです。

```rust
trait Scalar: Copy {
    type Real: Float;
    fn abs_sq(self) -> Self::Real;
    fn gemm(desc: GemmDescriptor<'_, Self>) -> Result<(), Error>; // 追加
}

impl Scalar for f64 {
    // type Real, abs_sq は省略
    fn gemm(desc: GemmDescriptor<'_, f64>) -> Result<(), Error> {
        gemm_f64(desc) // Self = f64 なので読み替え不要
    }
}
```

入口は`T::gemm(desc)`を呼ぶだけになり、`TypeId`も`unsafe`も`'static`境界も消えます。前作で`abs_sq`の差分を`Scalar`に閉じ込めたのと、まったく同じ手です。だからこそ、人間がレビューすれば「なぜ最初からこう書かない」と一瞬で思うわけです。

## なぜエージェントは局所的に`unsafe`を選ぶのか

人間がRustを書くとき、`unsafe`はたいてい最後の脱出口です。safe Rustで型と所有権に押し込めるところまで押し込み、どうしてもFFI・raw pointer・レイアウト・aliasingの境界に当たったときだけ、狭い範囲に`unsafe`を閉じ込めます。だから「`Scalar`があるのに`unsafe`」は、人間にはまず起きません。

コード生成エージェントの事情は少し違うと考えると、説明がつきます。`unsafe`を含む低レベルRustを大量に学習しているとすれば、`TypeId`・descriptor・kernel・backend・GEMM・complexといった語彙が並んだとき、実際にはsafeなAPIへのルーティング問題でも、低レベル境界のように見えてしまうことがあります。さらに、`unsafe`を使うとコンパイルエラーが消えます。エラーが消えるのは強い「解けた」信号で、その局所的な達成感が、一歩手前の「そもそも読み替えが要るのか」という問いを飛ばさせます。

言い換えると、これは知識の問題というより、問題の枠の取り方の問題です。「変換問題」と枠を取った時点で、`unsafe`は妥当な道具に見えます。「配置問題」と枠を取り直せれば、`unsafe`は出番がありません。

## レビューで見る匂い

なので、この種の`unsafe`に対するフィードバックは「`unsafe`を避けよう」では弱いです。もっと具体的な合図にした方がよい。

```rust
TypeId::of::<T>() == TypeId::of::<f64>()
unsafe { reinterpret_desc::<T, f64>(desc) }
```

この2つが並んでいたら、`unsafe`の中身がsoundかを確かめる前に、まず設計を疑います。`Descriptor<T>`を`Descriptor<f64>`へ戻すために`TypeId`とraw pointer castを使っているなら、多くの場合やるべきことは、記述子を読み替えることではなく、`T`の実装側へ処理を持っていくことです。

`unsafe`ブロックの中身を正当化するより、`unsafe`ブロックが要る問題設定そのものを消せるなら、その方がよい。レビューや設計の場で、まず一度こう聞くだけで足ります。その`unsafe`、本当に必要ですか。
