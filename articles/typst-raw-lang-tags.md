---
title: "Typstのコードブロックでシンタックスハイライトを指定できる言語のタグ一覧"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["typst"]
published: false
---

:::message
本記事はTypst v0.14.2で確認した内容に基づいています。
:::

## はじめに

Typstでは（拡張）Markdownと同様に、トリプルバッククォートを使用してテキストを書いた通りに出力するコードブロックを作成できます。
このとき開きトリプルバッククォートの直後に言語を指定する（例` ```cpp `）ことで、シンタックスハイライトができます。
細かい話になりますが、トリプルバッククォートによるコードブロックはTypstでは`raw`関数の糖衣構文として提供されています。

[`raw`関数のドキュメント](https://typst.app/docs/reference/text/raw/)を確認してみると、指定可能な言語については

> Apart from typical language tags known from Markdown, this supports the "typ", "typc", and "typm" tags for Typst markup, Typst code, and Typst math, respectively.

と書かれており、Typst関連の言語以外に関してはよくわかりません。
なぜならMarkdown自身は言語タグについて特に定めておらず、ハイライトを担当するシンタックスハイライター実装によってサポートされる言語タグが異なるからです。
具体的な実装として[PrismJS/prism](https://github.com/PrismJS/prism)や[shikijs/shiki](https://github.com/shikijs/shiki)などがあり、Zennは2026年1月にPrismからShikiに移行しました^[https://info.zenn.dev/2026-01-14-update-syntax-highlighter]。

それではTypstはどうなのかというと、Rust製のcat代替である[sharkdp/bat](https://github.com/sharkdp/bat)のシンタックスハイライト機能を利用しているようです^[構文定義にはYAML形式の[sublime text syntax](https://www.sublimetext.com/docs/syntax.html)が使用されているようです]。

実際Typstで使用可能な言語タグの確認方法ですが、`typst`クレートの`typst::text::RawElem::languages()`関数を呼び出すと確認できます。
上記関数を呼び出すだけなのですが、Typstの実装に触らないといけないためRustです。

これだけのためにRustを触るのは面倒だと思うので結果を取得しました。

結果はこちら

<https://github.com/ultimatile/typst-raw-lang-tags/blob/master/result.md>

基本的に対応する拡張子を書けば良いことがわかります。

なお、`cat`代替である`bat`のシンタックスハイライト機能を利用しているため、ファイル名を受け取る`bat`は拡張子を見るはずという予想はできます。

結果を取得するのに使用したコードのリポジトリはこちら

<https://github.com/ultimatile/typst-raw-lang-tags>

です。`Cargo.toml`に記載された`typst`クレートのバージョンを変更すれば、Typstのバージョンを変えて確認できます。
