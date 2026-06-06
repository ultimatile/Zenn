---
title: "Rustでエラー原因をsourceとDisplayの両方に書いてはいけない理由"
emoji: "🦀"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["rust", "thiserror", "anyhow"]
published: true
---

:::message

## TL;DR

- 責務分担: `Display`は自エラーの説明。`source()`は原因へのリンク。reporterは全体の表示。
- 原因を`#[source]`/`#[from]`で露出するなら、同じ原因を`#[error("...: {0}")]`で`Display`に重ねない。
- 重ねると`anyhow`等のreporterが`source()`を辿り、同じ原因が重複表示される。
- 文脈ありなら`#[error("自レイヤの文脈")]`+`#[source]`。文脈なしラッパーなら`#[error(transparent)]`。
- `error.to_string()`単独なら例外的にありうる。reporter併用ではfootgunになる。

:::

## はじめに

[`std::error::Error`](https://doc.rust-lang.org/std/error/trait.Error.html)のドキュメントには、あるエラーが内側のエラーをラップするときのガイドラインがあります。

> In error types that wrap an underlying error, the underlying error should be either returned by the outer error’s `Error::source()`, or rendered by the outer error’s `Display` implementation, but not both.

<!-- textlint-disable ja-technical-writing/ja-no-mixed-period -->

つまり、内側のエラーは

- `source()`で返す
- `Display`に描画する

のどちらか一方を行いますが、両方行ってはいけないと言っています。

<!-- textlint-enable ja-technical-writing/ja-no-mixed-period -->

なぜでしょうか？公式ガイドラインだけでは理由がわかりません。
本記事では、実際にまずいことになる例を見てみます。
`thiserror`では次のようなコードが自然に書けるので、なぜ避けるべきなのかが見えにくいです。

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("backend operation failed: {0}")]
    Backend(#[source] BackendError),
}
```

`error.to_string()`だけを見ると、これは便利に見えます。

```text:出力
backend operation failed: connection refused
```

この出力のうち`backend operation failed`は、`MyError`自身が`#[error("...")]`で付けた文言です。
`connection refused`は内側の`BackendError`の`Display`出力です。
`#[error("...: {0}")]`の`{0}`が、内側のエラーの表示文字列をここに埋め込んでいます。

しかし、この型は同じ`BackendError`を2つの経路で外に出しています。

- `Display`: `: {0}`で内側のエラーの文言を埋め込む
- `source()`: `#[source]`で内側のエラーそのものを返す

これが重複表示の原因になります。

## Rustのエラーチェーンの責務分担

Rustの`Error`は、単一の文字列ではなくエラーチェーンを表現できます。

- top error
  - caused by: middle error
    - caused by: leaf error

このとき、それぞれの責務を分けて考えるとわかりやすいです。

| 要素       | 責務                             |
| ---------- | -------------------------------- |
| `Display`  | そのエラー自身の文脈を説明する   |
| `source()` | 原因エラーへのリンクを返す       |
| reporter   | `source()`を辿って全体を表示する |

たとえば「設定ファイルの読み込みに失敗した。原因は`io::Error`」なら、外側のエラーはこう書きます。

```rust
#[derive(thiserror::Error, Debug)]
enum ConfigError {
    #[error("failed to read config")]
    Read(#[source] std::io::Error),
}
```

`ConfigError::Read`の`Display`は自分の層の文脈だけを示します。

```text:出力
failed to read config
```

原因の`io::Error`は消えておらず、`source()`に残っています。
必要なら`anyhow`、`eyre`、`miette`、自前のフォーマッターなどがチェーンを辿って表示します。

この分担にすると、各層の`Display`は局所的に保てます。
外側のエラーが子孫エラーの表示形式まで面倒を見る必要はありません。

## thiserrorで踏みやすいfootgun

`thiserror`は`#[error("...")]`で`Display`を、`#[source]`/`#[from]`で`source()`を実装できます。

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("backend operation failed")]
    Backend(#[source] BackendError),
}
```

これは`Display`と`source()`の責務が分かれています。

一方、次のように書くと責務が重なります。

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("backend operation failed: {0}")]
    Backend(#[source] BackendError),
}
```

`#[error("...: {0}")]`は内側のエラーの`Display`を外側の`Display`に埋め込みます。
さらに`#[source]`は同じ内側のエラーをreporterにも見せます。

`error.to_string()`だけなら、たしかに情報量が増えて便利に見えます。
しかしreporterから見ると、同じ原因が`Display`と`source()`の両方に現れます。

## 重複出力の例

3段のエラーを考えます。

```rust
#[derive(thiserror::Error, Debug)]
enum LeafError {
    #[error("file not found: {0}")]
    NotFound(String),
}

#[derive(thiserror::Error, Debug)]
enum MidError {
    #[error("backend operation failed: {0}")]
    Backend(#[from] LeafError),
}

#[derive(thiserror::Error, Debug)]
enum TopError {
    #[error("request handling failed: {0}")]
    Mid(#[from] MidError),
}
```

これを`anyhow::Error`化してreporter系のフォーマッターで出力します。

### `{:#}`（alternate Display）

alternate[^alternate] な `Display` で、`:` 区切りの1行チェーンになります。

```text:出力
request handling failed: backend operation failed: file not found: foo.txt: backend operation failed: file not found: foo.txt: file not found: foo.txt
```

### `{:?}`（Debug）

`Debug`で、"Caused by:"形式になります。

```text:出力
request handling failed: backend operation failed: file not found: foo.txt

Caused by:
    0: backend operation failed: file not found: foo.txt
    1: file not found: foo.txt
```

leafの`"file not found: foo.txt"`が何度も出ます。

理由は単純で、各層の`Display`が内側のエラーの文言をすでに含んでいるためです。そのうえでreporterが`source()`を辿り、同じ内側のエラーをもう一度表示します。

これはreporterの問題ではありません。エラー型が同じ情報を2つの経路で渡していることが原因です。

## 基本形: 文脈を持つエラーは自レイヤだけを書く

文脈を持つエラーは、`Display`に自レイヤの文脈だけを書きます。

```rust
#[derive(thiserror::Error, Debug)]
enum BatchError {
    #[error("failed to process item {index}")]
    Item {
        index: usize,
        #[source]
        source: WorkerError,
    },
}
```

この型の`Display`は次のとおりです。

```text:出力
failed to process item 3
```

原因の`WorkerError`は`source()`から辿れます。

```text:出力
failed to process item 3

Caused by:
    0: worker failed to run
    1: connection refused
```

この形なら、各層は自分の文脈だけを持ち、最終的な表示はreporterが決められます。

ここで`#[source]`を使い`#[from]`を使っていないのは、`Item`が`index`という自前フィールドを持つためです。`#[from]`は基本的にsourceだけのフィールドのとき（`Backtrace`などの特殊フィールドは例外）に使います。これは変換`From`も同時に生成したいときの選択です。`index`のような追加の文脈を併せ持つvariantでは`#[source]`を使います。どちらもsourceを露出する点は同じで、フィールド構成で選び分けます。

## 基本形: 文脈を持たないラッパーはtransparent

自前の文脈を持たず、内側のエラーをそのまま上に運ぶだけのvariantには`#[error(transparent)]`を使います。

```rust
#[derive(thiserror::Error, Debug)]
enum AppError {
    #[error(transparent)]
    Backend(#[from] BackendError),
}
```

これは`Display`と`source()`を内側のエラーに委譲します。
ただし、`source()`が内側のエラー自身を返すという意味ではありません。
内側の`source()`をそのまま通すだけなので、透明ラッパーはチェーンに段を足しません。
reporterから見ると、内側のエラーがそのまま現れます。

「`Backend`というvariantに入れたいだけで、追加の文脈はない」というケースで、外側に余計な文言を足さないための指定です。

判断基準はこうです。

- 自前の文脈がある → `#[error("自レイヤの文脈")]` + `#[source]`
- 自前の文脈がない → `#[error(transparent)]`

たとえば「item index Nで失敗した」は自前の文脈があるのでtransparentではありません。一方、「下位エラー型をAPI上のenumに詰め替えるだけ」はtransparentです。

フィールドを持たない固定文字列の文脈（たとえば`#[error("backend operation failed")]`）も「自前の文脈」に数えます。`transparent`にするのは、内側のエラーと区別する文言が一切ない純粋な詰め替えだけです。「どの層で失敗したか」を一言でも示すなら、それは自レイヤの文脈なので、`#[error("...")]` + `#[source]`を使います。

## 例外: Displayに含めてもよいケース

`Display`に内側の情報を含めることが常に悪いわけではありません。

たとえば、内側に構造化されたエラーが存在せず、外部システムから文字列しか得られないなら、その文字列を`Display`に含めるしかありません。

```rust
#[derive(thiserror::Error, Debug)]
enum ExternalError {
    #[error("external command failed: {message}")]
    Command { message: String },
}
```

この場合、`message`は`source()`で辿れるエラーではありません。`Display`に出しても2つの経路にはなりません。

また、小さなアプリケーションで`error.to_string()`しか使わないと決めているなら、`#[error("...: {source}")]`と書く割り切りもあり得ます。

```rust
#[derive(thiserror::Error, Debug)]
enum AppError {
    #[error("failed to read config: {source}")]
    ReadConfig {
        #[source]
        source: std::io::Error,
    },
}
```

ただし、この型を`anyhow`などのreporterに渡すと重複し得ます。ライブラリのパブリックなエラー型や、複数のreporterに流れるエラー型では避けた方がよいです。

`{e}`（`Display`単独）では原因が見えないので、`Display`に埋め込みたくなる場面もあります。
ただ、原因は`source()`チェーンに残っていて消えてはいないので、詳細が要るreporterはそこから組み立てられます。
アプリ内部で完結する型なら埋め込む割り切りもありますが、パブリックなエラー型では前述の重複を避ける方が無難です。

最終的に1行で原因まで表示したいなら、エラー型の`Display`に原因を畳み込むのではなく、最終表示境界でチェーンをflattenする方が扱いやすいです。

```rust
fn format_error_chain(error: &(dyn std::error::Error)) -> String {
    let mut message = error.to_string();
    let mut source = error.source();

    while let Some(error) = source {
        message.push_str(": ");
        message.push_str(&error.to_string());
        source = error.source();
    }

    message
}
```

この方が「エラー型が何を表すか」と「ユーザーにどう表示するか」を分けられます。

`anyhow`を使うなら、この`format_error_chain`相当を`{:#}`が最初からやってくれます。reporterを使う前提なら自前のflattenヘルパーすら要らず、「`Display`に畳み込まない」だけで1行表示が得られます。

## まとめ

- `#[error("...")]`は`Display`を生成、`#[source]`/`#[from]`は`source()`チェーンを生成。
- `#[source]`で返す内側のエラーを`#[error("...: {0}")]`でも表示すると、同じ原因が2つの経路に出る。
- reporterが`source()`を辿ると、その二重化が重複表示として現れる。
- 基本形は、文脈を持つエラーでは自レイヤの文脈だけを`Display`に書くこと。
- 文脈を持たないラッパーは`#[error(transparent)]`。固定文字列でも自レイヤの文脈があるならtransparentではなく`#[error("...")]`+`#[source]`。
- `#[from]`は基本的にsourceだけのとき（`Backtrace`等を除く）、`#[source]`は文脈フィールドを併せ持つとき。`Display`の方針とは別軸。
- 原因まで含めた1行表示は、エラー型の`Display`ではなく最終表示境界のreporter（`anyhow`なら`{:#}`）で作る。

## 参考

- [std::error::Error docs](https://doc.rust-lang.org/std/error/trait.Error.html) — `Display`と`source()`のguideline
- [What the Error Handling Project Group is Working Towards](https://blog.rust-lang.org/inside-rust/2021/07/01/What-the-error-handling-project-group-is-working-towards/) — Duplicate Information Issue
- [thiserror docs](https://docs.rs/thiserror) — `#[error(transparent)]`と`#[source]`
- [anyhow docs](https://docs.rs/anyhow) — reporterとしての`{:#}` / `{:?}`フォーマッター
- [eyre docs](https://docs.rs/eyre) — anyhow系のreporter
- [miette docs](https://docs.rs/miette) — 診断表示向けのreporter

[^alternate]: 整形指定子 `#` で立つRust標準の整形フラグです。`Display`/`Debug` の実装内で `Formatter::alternate()` が `true` になり、出力を切り替えられます。`anyhow::Error` の `{:#}` が `source()` チェーンを `:` で連結するのも、このフラグによるものです。詳しくは [std::fmt の整形フラグ](https://doc.rust-lang.org/std/fmt/index.html#sign0) を参照してください。
