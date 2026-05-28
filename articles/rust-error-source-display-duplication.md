---
title: "Rustでエラー原因をsourceとDisplayの両方に書いてはいけない理由"
emoji: "🦀"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["rust", "thiserror", "anyhow"]
published: false
---

## TL;DR

- Rustのerror chainでは、`Display`は**そのerror自身の説明**、`source()`は**原因errorへのリンク**、chain walkerは**全体の表示**、という責務分担にするのが基本です。
- `#[source]`/`#[from]`で原因を露出しているなら、同じ原因を`#[error("...: {0}")]`で`Display`にも埋め込むべきではありません。
- 両方やると、`anyhow`などのchain walkerが`source()`を辿ったときに**同じ原因が重複表示**されます。
- context-bearing errorは`#[error("自レイヤの文脈")]` + `#[source]`、pure wrapperは`#[error(transparent)]`が基本形です。
- `error.to_string()`単独で原因まで見せたい場合は例外的にあり得ますが、chain walkerと組み合わせるならfootgunになります。

## はじめに

`std::error::Error`のドキュメントには、errorがunderlying errorをwrapするときのガイドラインがあります。

> In error types that wrap an underlying error, the underlying error should be either returned by the outer error’s `Error::source()`, or rendered by the outer error’s `Display` implementation, but not both.

つまり、内側のerrorは:

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

- `Display`: `: {0}`でinner errorの文言を埋め込む
- `source()`: `#[source]`でinner errorそのものを返す

これが重複表示の原因になります。

## 2. Rustのerror chainの責務分担

Rustの`Error`は、単一の文字列ではなくchainを表現できます。

```text
top error
  caused by: middle error
    caused by: leaf error
```

このとき、それぞれの責務を分けて考えるとわかりやすいです。

```text
Display:   そのerror自身の文脈を説明する
source():  原因errorへのリンクを返す
reporter:  source()をwalkして全体を表示する
```

たとえば「設定ファイルの読み込みに失敗した。原因は`io::Error`」なら、外側のerrorはこう書きます。

```rust
#[derive(thiserror::Error, Debug)]
enum ConfigError {
    #[error("failed to read config")]
    Read(#[source] std::io::Error),
}
```

`ConfigError::Read`の`Display`は自分の層の文脈だけを言います。

```text
failed to read config
```

原因の`io::Error`は消えていません。`source()`に残っています。必要なら`anyhow`、`eyre`、`miette`、自前formatterなどがchainを辿って表示します。

この分担にすると、各layerの`Display`は局所的に保てます。外側のerrorが子孫errorの表示形式まで面倒を見る必要はありません。

## 3. thiserrorで踏みやすいfootgun

`thiserror`は`#[error("...")]`で`Display`を、`#[source]` / `#[from]`で`source()`を実装できます。

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

`#[error("...: {0}")]`はinner errorの`Display`を外側の`Display`に埋め込みます。さらに`#[source]`は同じinner errorをchain walkerにも見せます。

`error.to_string()`だけなら、たしかに情報量が増えて便利に見えます。しかしchain walkerから見ると、同じ原因が`Display`と`source()`の両方に現れます。

## 4. 重複出力の例

3段のerrorを考えます。

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

この例は`programs/rust-error-source-display-duplication`で再現できます。

```console
cd programs/rust-error-source-display-duplication
cargo run
```

これを`anyhow::Error`化してchain walker系のフォーマッタで出力します。

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

理由は単純で、各layerの`Display`がinner errorの文言をすでに含んでいるためです。そのうえでreporterが`source()`をwalkし、同じinner errorをもう一度表示します。

これはreporterの問題ではありません。error型が同じ情報を2つの経路で渡していることが原因です。

## 5. 基本形: context-bearing errorは自レイヤだけを書く

contextを持つerrorは、`Display`に自レイヤの文脈だけを書きます。

```rust
#[derive(thiserror::Error, Debug)]
enum SweepError {
    #[error("step failed at site {site}")]
    Step {
        site: usize,
        #[source]
        source: HeffError,
    },
}
```

この型の`Display`は:

```text
step failed at site 3
```

原因の`HeffError`は`source()`から辿れます。

```text
step failed at site 3

Caused by:
    0: failed to diagonalize effective Hamiltonian
    1: LAPACK error ...
```

この形なら、各layerは自分の文脈だけを持ち、最終的な表示はreporterが決められます。

## 6. pure wrapperはtransparent

自前のcontextを持たず、内側errorをそのまま上に運ぶだけのvariantには`#[error(transparent)]`を使います。

```rust
#[derive(thiserror::Error, Debug)]
enum AppError {
    #[error(transparent)]
    Backend(#[from] BackendError),
}
```

これは`Display`と`source()`をinner errorに委譲します。

「Backend errorというvariantに入れたいだけで、追加の文脈はない」というケースで、外側に余計な文言を足さないための指定です。

判断基準はこうです。

```text
自前contextがある-> #[error("自レイヤの文脈")] + #[source]
自前contextがない-> #[error(transparent)]
```

たとえば「site index Nで失敗した」は自前contextがあるのでtransparentではありません。一方、「下位error型をAPI上のenumに詰め替えるだけ」はtransparentです。

## 7. 例外: Displayに含めてもよいケース

`Display`にinner情報を含めることが常に悪いわけではありません。

たとえば、内側に構造化されたerrorが存在せず、外部システムから文字列しか得られないなら、その文字列を`Display`に含めるしかありません。

```rust
#[derive(thiserror::Error, Debug)]
enum ExternalError {
    #[error("external command failed: {message}")]
    Command { message: String },
}
```

この場合、`message`は`source()`で辿れるerrorではありません。`Display`に出しても二重経路にはなりません。

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

ただし、この型を`anyhow`などのchain walkerに渡すと重複し得ます。ライブラリのpublic error型や、複数のreporterに流れるerror型では避けた方がよいです。

最終的に一行で原因まで表示したいなら、error型の`Display`に原因を畳み込むのではなく、最終表示境界でchainをflattenする方が扱いやすいです。

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

この方が「error型が何を表すか」と「ユーザーにどう表示するか」を分けられます。

## 8. まとめ

- `thiserror`の`#[error("...")]`は`Display`を生成します。
- `#[source]` / `#[from]`は`source()` chainを生成します。
- `#[source]`で返すinner errorを`#[error("...: {0}")]`でも表示すると、同じ原因が二重経路になります。
- chain walkerが`source()`を辿ると、その二重化が重複表示として現れます。
- 基本形は、context-bearing errorでは**自レイヤの文脈だけを`Display`に書く**ことです。
- pure wrapperには`#[error(transparent)]`を使います。
- 原因まで含めた一行表示は、error型の`Display`ではなく最終表示境界のreporterで作ります。

## 参考

- [std::error::Error docs](https://doc.rust-lang.org/std/error/trait.Error.html) — `Display`と`source()`のguideline
- [What the Error Handling Project Group is Working Towards](https://blog.rust-lang.org/inside-rust/2021/07/01/What-the-error-handling-project-group-is-working-towards/) — Duplicate Information Issue
- [thiserror docs](https://docs.rs/thiserror) — `#[error(transparent)]`と`#[source]`
- [anyhow docs](https://docs.rs/anyhow) — chain walkerとしての`{:#}` / `{:?}`フォーマッタ
