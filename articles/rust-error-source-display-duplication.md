---
title: "Rustでエラー原因をsourceとDisplayの両方に書いてはいけない理由"
emoji: "🦀"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["rust", "thiserror", "anyhow"]
published: false
---

## TL;DR

- Rustのエラーチェーンでは、`Display`は**そのエラー自身の説明**、`source()`は**原因エラーへのリンク**、reporterは**全体の表示**、という責務分担にするのが基本です。
- `#[source]`/`#[from]`で原因を露出しているなら、同じ原因を`#[error("...: {0}")]`で`Display`にも埋め込むべきではありません。
- 両方やると、`anyhow`などのreporterが`source()`を辿ったときに**同じ原因が重複表示**されます。
- 文脈を持つエラーは`#[error("自レイヤの文脈")]`+`#[source]`、文脈を持たないラッパーは`#[error(transparent)]`が基本形です。
- `error.to_string()`単独で原因まで見せたい場合は例外的にあり得ますが、reporterと組み合わせるならfootgunになります。

## はじめに

`std::error::Error`のドキュメントには、あるエラーが内側のエラーをラップするときのガイドラインがあります。

> In error types that wrap an underlying error, the underlying error should be either returned by the outer error’s `Error::source()`, or rendered by the outer error’s `Display` implementation, but not both.

つまり、内側のエラーは:

- `source()`で返す
- `Display`に描画する

のどちらか一方を行いますが、両方行ってはいけないと言っています。

なぜでしょうか？公式ガイドラインだけでは理由はわかりません。
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

```text
backend operation failed: connection refused
```

しかし、この型は同じ`BackendError`を2つの経路で外に出しています。

- `Display`: `: {0}`で内側のエラーの文言を埋め込む
- `source()`: `#[source]`で内側のエラーそのものを返す

これが重複表示の原因になります。

## Rustのエラーチェーンの責務分担

Rustの`Error`は、単一の文字列ではなくエラーチェーンを表現できます。

```text
top error
  caused by: middle error
    caused by: leaf error
```

このとき、それぞれの責務を分けて考えるとわかりやすいです。

```text
Display:   そのエラー自身の文脈を説明する
source():  原因エラーへのリンクを返す
reporter:  source()を辿って全体を表示する
```

たとえば「設定ファイルの読み込みに失敗した。原因は`io::Error`」なら、外側のエラーはこう書きます。

```rust
#[derive(thiserror::Error, Debug)]
enum ConfigError {
    #[error("failed to read config")]
    Read(#[source] std::io::Error),
}
```

`ConfigError::Read`の`Display`は自分の層の文脈だけを示します。

```text
failed to read config
```

原因の`io::Error`は消えておらず、`source()`に残っています。
必要なら`anyhow`、`eyre`、`miette`、自前のフォーマッタなどがチェーンを辿って表示します。

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

これを`anyhow::Error`化してreporter系のフォーマッタで出力します。

`{:#}` (alternate `Display`、`:`区切りの1行チェーン):

```text
request handling failed: backend operation failed: file not found: foo.txt: backend operation failed: file not found: foo.txt: file not found: foo.txt
```

`{:?}` (`Debug`、"Caused by:"形式):

```text
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

この型の`Display`は:

```text
failed to process item 3
```

原因の`WorkerError`は`source()`から辿れます。

```text
failed to process item 3

Caused by:
    0: worker failed to run
    1: connection refused
```

この形なら、各層は自分の文脈だけを持ち、最終的な表示はreporterが決められます。

ここで`#[source]`を使い`#[from]`を使っていないのは、`Item`が`index`という自前フィールドを持つためです。`#[from]`はsourceが唯一のフィールドのとき（変換`From`も同時に生成したいとき）に使い、`index`のような追加の文脈を併せ持つvariantでは`#[source]`を使います。どちらもsourceを露出する点は同じで、フィールド構成で選び分けます。

## 6. 文脈を持たないラッパーはtransparent

自前の文脈を持たず、内側のエラーをそのまま上に運ぶだけのvariantには`#[error(transparent)]`を使います。

```rust
#[derive(thiserror::Error, Debug)]
enum AppError {
    #[error(transparent)]
    Backend(#[from] BackendError),
}
```

これは`Display`と`source()`を内側のエラーに委譲します。

「`Backend`というvariantに入れたいだけで、追加の文脈はない」というケースで、外側に余計な文言を足さないための指定です。

判断基準はこうです。

```text
自前の文脈がある-> #[error("自レイヤの文脈")] + #[source]
自前の文脈がない-> #[error(transparent)]
```

たとえば「item index Nで失敗した」は自前の文脈があるのでtransparentではありません。一方、「下位エラー型をAPI上のenumに詰め替えるだけ」はtransparentです。

フィールドを持たない固定文字列のcontext（たとえば`#[error("backend operation failed")]`）も「自前の文脈」に数えます。`transparent`にするのは、内側のエラーと区別する文言が一切ない純粋な詰め替えだけです。「どの層で失敗したか」を一言でも示すなら、それは自レイヤの文脈なので、`#[error("...")]` + `#[source]`を使います。

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

この場合、`message`は`source()`で辿れるエラーではありません。`Display`に出しても二重経路にはなりません。

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

ただし、この型を`anyhow`などのreporterに渡すと重複し得ます。ライブラリのpublic エラー型や、複数のreporterに流れるエラー型では避けた方がよいです。

レビューで「`{e}`だけだと原因が見えないので`Display`に埋め込んでほしい」と求められることがあります。アプリ内部で完結する型ならその割り切りもありますが、ライブラリのpublic エラー型では上記の重複が押し返しの根拠になります。原因は`source()`チェーンに残っていて消えてはいないので、詳細が要るreporterはそこから組み立てられます。

最終的に一行で原因まで表示したいなら、エラー型の`Display`に原因を畳み込むのではなく、最終表示境界でチェーンをflattenする方が扱いやすいです。

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

`anyhow`を使うなら、この`format_error_chain`相当を`{:#}`が最初からやってくれます。reporterを使う前提なら自前のflatten helperすら要らず、「`Display`に畳み込まない」だけで一行表示が得られます。

## まとめ

- `thiserror`の`#[error("...")]`は`Display`を生成します。
- `#[source]` / `#[from]`は`source()`チェーンを生成します。
- `#[source]`で返す内側のエラーを`#[error("...: {0}")]`でも表示すると、同じ原因が二重経路になります。
- reporterが`source()`を辿ると、その二重化が重複表示として現れます。
- 基本形は、文脈を持つエラーでは**自レイヤの文脈だけを`Display`に書く**ことです。
- 文脈を持たないラッパーには`#[error(transparent)]`を使います。固定文字列でも自レイヤの文脈があるなら、transparentではなく`#[error("...")]` + `#[source]`です。
- `#[from]`はsourceが唯一フィールドのとき、`#[source]`は文脈フィールドを併せ持つとき。`Display`の方針とは別軸の選択です。
- 原因まで含めた一行表示は、エラー型の`Display`ではなく最終表示境界のreporter（`anyhow`なら`{:#}`）で作ります。

## 参考

- [std::error::Error docs](https://doc.rust-lang.org/std/error/trait.Error.html) — `Display`と`source()`のguideline
- [What the Error Handling Project Group is Working Towards](https://blog.rust-lang.org/inside-rust/2021/07/01/What-the-error-handling-project-group-is-working-towards/) — Duplicate Information Issue
- [thiserror docs](https://docs.rs/thiserror) — `#[error(transparent)]`と`#[source]`
- [anyhow docs](https://docs.rs/anyhow) — reporterとしての`{:#}` / `{:?}`フォーマッタ
