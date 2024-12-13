---
title: "Typstで数式中の文字を斜めにしない方法"
emoji: "🔰"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["typst","math"]
published: true
published_at: 2024-12-12 00:00 
---

:::message
この記事は [Typst Advent Calendar 2024](https://qiita.com/advent-calendar/2024/typst) の12日目の記事です．昨日は[@Omochice](https://qiita.com/Omochice)さんの「[Typixを使って複数環境でTypstでスライドをコンパイルする](https://zenn.dev/omochice/articles/reproducible-compilation-of-typst-by-typix)」でした．明日は[@ozekik](https://qiita.com/ozekik)さんの「[Typstで論理式/証明図を書く](https://zenn.dev/ozekik/articles/0f5bbb6a77af20)」です．
:::

## はじめに

Typstでは`$`で囲むことで数式を入力することができますが，数式中の文字は$A$のように通常斜めの書体（斜体）になります． 一方で数式中でも$\mathrm{A}$のように本文中と同じまっすぐな書体（立体）で記述した方が良い場合があります． 具体的には自然対数の底$\mathrm{e}$や虚数単位$\mathrm{i}$などの[数学定数](https://ja.wikipedia.org/wiki/%E6%95%B0%E5%AD%A6%E5%AE%9A%E6%95%B0)や微積分に出てくる$\mathrm{d}x$などです． 他には函数などの数学的操作を表す場合なども立体で表記した方が良いです．正弦函数を表すために$sin$と表記してしまうと変数$s$，$i$，$n$の積として解釈されてしまうため，$\sin$と立体で表記することが望ましいです．

:::details いつ立体にするべき？
数学的操作を立体にすべきなのは分野に依らないと思いますが，その他の場合にいつ立体にするべきか？というのは分野や論文雑誌の規則などによって異なります． 例えば先ほど出てきた自然対数の底などの数学定数や$\mathrm{d}x$は物理分野では立体で表記することが一般的ですが，数学分野では斜体で表記することが一般的なようです． 論文投稿の際には出版社がスタイルガイドを提供していることが多いと思いますので，それに従うのが最優先です． 出版社以外にも分野を代表する組織が規則を定めていることがあります． 例えば物理分野では[IUPAP](https://ja.wikipedia.org/wiki/%E5%9B%BD%E9%9A%9B%E7%B4%94%E7%B2%8B%E3%83%BB%E5%BF%9C%E7%94%A8%E7%89%A9%E7%90%86%E5%AD%A6%E9%80%A3%E5%90%88)と呼ばれる組織が発行している通称[Red book](https://iupap.org/who-we-are/internal-organization/commissions/c2-commission-on-symbols-units-nomenclature-atomic-masses-and-fundamental-constants/#additional-information)と呼ばれる物理量などの表記に関する規格書があります^[正式なタイトルはSYMBOLS, UNITS, NOMENCLATURE AND FUNDAMENTAL CONSTANTS IN PHYSICSです．]．
:::

Typstの数式環境において文字を立体にするには以下の3つの方法があり，場合に応じて使い分ける必要があります．
1. 数学的操作を表す場合はテキスト演算子を使う
2. 2文字以上の文字列の場合は二重引用符`"`で囲む
3. 1文字の場合は`upright`命令を使う

以下では順に書き方と使い分けが必要な理由を説明していきます．
とりあえず使い方だけ知りたい方向けにまとめのフローチャートを本文を読んでいなくても分かるように書いたのでお急ぎの方は[まとめ](#まとめ)に飛んでください．

---

Typst 0.12.0で動作確認しています．

:::details 本文中に表示されている数式に関して
Zennでは数式のTypst記法は未対応のため本文中に表示されている数式は$\LaTeX$記法で書いています．そのためTypstの表示と差異がある場合があります． 実際のTypstの表示が必要な場合などはTypstのコードと実行結果を画像の形で挿入しています．
:::

## 数学的操作を表す場合はテキスト演算子を使う

Typstでは正弦函数などよく用いられる函数や記号については立体になる命令があらかじめ多く定義されており，それらは（定義済み）[text operator](https://typst.app/docs/reference/math/op)と呼ばれます．以下ではテキスト演算子と呼びます．
[定義済みテキスト演算子](https://typst.app/docs/reference/math/op/#predefined)は `arccos`,`arcsin`,`arctan`, `arg`, `cos`, `cosh`, `cot`, `coth`, `csc`, `csch`, `ctg`, `deg`, `det`, `dim`, `exp`, `gcd`, `hom`, `id`, `im`, `inf`, `ker`, `lg`, `lim`, `liminf`, `limsup`, `ln`, `log`, `max`, `min`, `mod`, `Pr`, `sec`, `sech`, `sin`, `sinc`, `sinh`, `sup`, `tan`, `tanh`, `tg`, `tr` です．
この他に厳密にはテキスト演算子ではありませんが^[後に続く変数との間に空きが入らないためテキスト演算子とは異なる処理がなされているようです．]`dif`と`Dif`という命令があります．この2つの命令はその名前からも予想されるように微分を表すための記号で，それぞれ$\mathrm{d}$，$\mathrm{D}$と表示されます． 定義済みテキスト演算子は数式中でそのまま呼び出せますので`$sin$`と書くと$\sin$と表示されます．逆に斜体にするには`$s i n$`と書く必要があり^[`italic(sin)`でも可です．]，素直に書いていれば立体になる仕様になっています．

上記の定義済みテキスト演算子以外にも自分でテキスト演算子を定義することができます．
例えば

```typst:数式環境外
#let span = math.op("span") 
```

と定義することで，`$span$`と書くと$\mathrm{span}$と表示するようにできます． あるいは1度だけ必要な場合などは数式内で直接`$op("span")$`と書いても良いです．この場合`math.`は省略できます．

:::details math.opのオプションに関する補足
[math.op](https://typst.app/docs/reference/math/op/)は真偽値を取る[`limits`](https://typst.app/docs/reference/math/op#parameters-limits)というオプションを持っています．これを用いて

```typst:数式環境外
#let colim = math.op("colim", limits: true) 
```

のように書くことができます．
`limits`は数式のみを独立した行で表示するディスプレイモードで上付き添字と下付き添字が表示される位置を指定するためのオプションです． `true`を指定すると上付き添字と下付き添字が演算子の上下に表示されます．
`$ colim^u_d $`と書くと
$$\operatornamewithlimits{colim}^u_d$$
のようになります．
`false`を指定すると上付き添字と下付き添字が以下のようにテキスト演算子の右に表示されます．
$$\mathrm{colim}^u_d$$
デフォルトは`false`です． `limits`の意味は添字を`lim`のように表示するのかどうかということだと思います．
:::

## 2文字以上の文字列の場合は二重引用符`"`で囲む

**2文字以上の**文字列を二重引用符`"`で囲むことで立体にすることができます．
`$D_"KL"$`と書くと$D_\mathrm{KL}$のように表示されます^[$D_\mathrm{KL}$は[Kullback-Leibler情報量](https://ja.wikipedia.org/wiki/%E3%82%AB%E3%83%AB%E3%83%90%E3%83%83%E3%82%AF%E3%83%BB%E3%83%A9%E3%82%A4%E3%83%96%E3%83%A9%E3%83%BC%E6%83%85%E5%A0%B1%E9%87%8F)です．]．

節の始めに強調したように1文字の場合は立体になりません．
試しに `$k_"B"$`と書いてみましょう^[$k_\mathrm{B}$は[Boltzmann定数](https://ja.wikipedia.org/wiki/%E3%83%9C%E3%83%AB%E3%83%84%E3%83%9E%E3%83%B3%E5%AE%9A%E6%95%B0)です．]．下付き添字`B`が立体になるように二重引用符で囲んで$k_\mathrm{B}$と表示されるように書いたつもりですが実際は$k_B$と表示されます．

なぜこのようになるのでしょうか？詳しい解説は見つけられていませんが，[Typstの公式ドキュメントのVariablesの項目](https://typst.app/docs/reference/math/#variables)には

> In math, single letters are always displayed as is.

と記載されています． 簡単に訳すと，数式環境では1文字は常にそのまま表示されるということを述べていると思います．
この説明だけでは今回の挙動の説明になっているとは思いませんが，とにかく1文字は特別扱いされていて2文字以上とは異なる処理をされていることが分かります．
文字数の違いで挙動が異なるのは数式を書き始めるとすぐに分かります．例えば適当に`$xy$`と書いてみると`error: unknown variable: xy`と出てコンパイルに失敗します． これを`$x y$`とするとコンパイルが通り，$xy$と表示されます．コンパイルが通るということは`error: unknown variable: x`(もしくは`error: unknown variable: y`)とはならないことを意味しています．
2文字以上の文字列の取り扱いに関しては[Typstの公式ドキュメントのVariablesの項目](https://typst.app/docs/reference/math/#variables)で

> Multiple letters, however, are interpreted as variables and functions.

と述べられており，2文字以上の文字列は変数や函数として解釈されることが分かります． 逆の言い方をすると1文字は変数や函数として解釈されないということです． このことから前述の文字数で挙動が異なることは理解できると思います．

::: details 1文字の変数の参照方法
1文字を数式中に書いた場合，常に文字としてそのまま表示されると述べましたが，それでは1文字で定義した変数や函数はどのように参照すればよいでしょうか？
以下のように名前の前に`#`を付けて`#x`のようにすると呼び出しになり，変数の値が代入されます．

![](/images/a-typst-upright-in-math/Fig1.png  =700x)
:::

一部のプログラミング言語において文字を表す`Char`型と文字列を表す`String`型が区別されているように，Typstでも1文字と複数の文字から成る文字列が区別されていると考えると理解しやすいかもしれません．

それでは1文字を立体にするにはどうすればよいでしょうか？
そのために`upright`命令を用います．次節で説明します．

## 1文字の場合は`upright`命令を使う

1文字の場合でも立体にするには`upright`命令を使います． `$k_upright(B)$`と書くと$k_\mathrm{B}$と表示されます．
2文字以上の場合に`upright`は使えないのかというと使えます． しかし`$D_upright(KL)$`と書くと前節で説明した通り`error: unknown variable: KL`とコンパイルエラーになるため，`$D_upright(K L)$`あるいは`$D_upright("KL")$`と書く必要があります． 前者は意味を考えるとスペースを入れるのは不自然です．後者は`$D_"KL"$`と書けば良いことは既に説明した通りですので冗長な書き方になっています．このように2文字以上の文字列に`upright`命令を使うことはあまり意味がありません．


## まとめ

Typstで入力した文字が自動的に斜体になる数式環境で文字をまっすぐ（立体）にする方法について説明しました． 使い分けをフローチャートの形にまとめると以下のようになります^[このフローチャートは[fletcher](https://typst.app/universe/package/fletcher)というTypstのパッケージを使って作成しました．]．
適切な命令を使い分けて素敵な美文書を作成しましょう．

![](/images/a-typst-upright-in-math/Fig2.png =700x)


#### [補足1]

より正確には「テキスト演算子として定義済みか？」ということです．ここでは本文を読まずに見に来た方向けの分かりやすい表現としたため例外がいくつかあります．
当然ですが有名かどうかは主観的なもので，有名だと思われるが定義されていない例として本文中に出てきた[線形包](https://ja.wikipedia.org/wiki/%E7%B7%9A%E5%9E%8B%E5%8C%85)を表す`span`や[留数](https://ja.wikipedia.org/wiki/%E7%95%99%E6%95%B0)を表す`res`があります． 逆に，分野や慣習の違いだと思いますが私は見たことがないものも定義されています．
また，大文字を含むテキスト演算子はほとんど定義されていませんが，例外として確率$\mathrm{Pr}$を表すであろう`Pr`と[物質微分](https://ja.wikipedia.org/wiki/%E7%89%A9%E8%B3%AA%E5%BE%AE%E5%88%86)$\mathrm{D}$を表すであろう`Dif`が定義されています．
テキスト演算子や定義済みテキスト演算子一覧については本文の[数学的操作を表す場合はテキスト演算子を使う](#数学的操作を表す場合はテキスト演算子を使う)やTypst公式ドキュメントの[定義済みテキスト演算子一覧](https://typst.app/docs/reference/math/op/#predefined)を参照してください．

::: details テキスト演算子は要らないのでは？と思ったあなたへ
1文字なら`upright`，2文字以上なら`"sin"`のように二重引用符で囲めば良いと思うと以下のフローチャートのようになりテキスト演算子は不要と思うかもしれません．
![](/images/a-typst-upright-in-math/Fig3.png =700x)

実はテキスト演算子には立体にする以外の効果があります．以下の画像を見てください．
![](/images/a-typst-upright-in-math/Fig4.png =700x)
テキスト演算子を使わず二重引用符で囲んだ場合はその後に続く変数との間が詰まりすぎたり空きすぎたりしていることが分かります．また，スペースの有無によって表示される空白の大きさが変わっていることも分かります．

`math.op`を使った場合についても確認してみましょう．
![](/images/a-typst-upright-in-math/Fig5.png =700x)
`math.op`を使って`res`を定義すると定義済みの`sin`と同じ大きさの空白が入っていることが分かります． また，`math.op`を使った場合はその後に続く変数との間のスペースの有無に表示される空白の大きさが影響を受けていないことも分かります．ついでに`upright`で無理やり定義した場合についても載せています．間が詰まりすぎていることが分かります．
:::

:::details 1文字の場合はテキスト演算子を使わなくて良いのか？
数学的操作を表す場合は使った方が良いです．1文字の場合は`op(upright(B))`という書き方になります． 以下のように違いが確認できます．
![](/images/a-typst-upright-in-math/Fig6.png =700x)
フローチャートが多少複雑化することと使うことはあまりなさそうなことから省略しました．

真実（？）が知りたい方向けに作成した完全版のフローチャートは以下のようになります．
![](/images/a-typst-upright-in-math/Fig7.png =700x)
:::
