---
title: "thiserror で error をどう書くか: chain walker への責務認識から決める"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["rust", "error", "thiserror", "anyhow"]
published: false
---

## TL;DR

- `thiserror` は `Display` を `#[error("...")]` で、`source()` チェーンを `#[source]` / `#[from]` で書けるマクロ。便利だが、**何を書くか** までは決めてくれない。
- 書き手が決める policy は実質 2 軸: (a) `#[error("...")]` で **自レイヤの context だけ書くか / 内側の `Display` を補間するか** (= School A vs School B)、(b) `#[source]` で **内側 error を露出するか / しないか**。
- どちらも、caller が `source()` を walk するかどうか — つまり **chain walker への責務をどう分担するか** — で決まる。
- 機械的に補間 (School B) すると、chain walker と組み合わせたとき **重複出力** が起きる。`#[error(transparent)]` (純ラップ用) と `#[error("...: {0}")]` (context あり用) の使い分けで緩和できるが、根は policy 軸の意識的な選択にある。

## 1. thiserror が提供するもの

`thiserror` を使うと、error の `Display` 実装を `#[error("...")]` 属性で書ける:

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("backend operation failed")]
    Backend,
}
```

これは `impl fmt::Display for MyError { ... }` を手書きする代わりの糖衣。出力したいメッセージを変数のように属性に書くだけで `Display` が生成される。

加えて `#[source]` (or `#[from]`) を付けると `std::error::Error::source()` が自動実装され、内側の error が **caller から walk できるようになる**:

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("backend operation failed")]
    Backend(#[source] BackendError),
}
```

`source()` チェーンは error の "原因スタック" を表現する仕組みで、caller 側のフォーマッタ (例: `anyhow::Error` の `{:#}` / `{:?}`、`tracing-error` の `SpanTrace`) が walk して原因を順に表示できる。caller がこの walk を行う側を **chain walker** と呼ぶことにする。

`thiserror` は `#[error("...")]` と `#[source]` を提供するが、**何を書くか・どこに `#[source]` を付けるか** は書き手が決める。ここに 2 つの policy 軸が隠れている。

## 2. policy は chain walker への責務分担で決まる

書き手側で起きる判断は、突き詰めると caller の前提に対する **責務分担** の決定:

- caller が chain walker (= `source()` を辿って詳細を組み立てる側) **である** 前提 → 自レイヤは context だけ書けばよい。詳細は caller が組み立ててくれる。
- caller が chain walker **でない** 前提 (= 例えば `error.to_string()` だけ呼んで終わる) → 詳細を見せるなら自レイヤの `Display` に内側情報を畳み込む必要がある。

この前提が 2 つの軸を駆動する。

## 3. 軸 A: `#[error("...")]` で何を書くか

### School A: 自レイヤの context のみ

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("backend operation failed")]
    Backend(#[source] BackendError),
}
```

`Display` は **その layer が何で失敗したか** だけ書く。内側 error は `source()` 経由で取らせる。

`error.to_string()` 単独だと "backend operation failed" だけ。詳細を見たい caller は `source()` を walk する責務を負う。

### School B: 内側の `Display` を補間

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("backend operation failed: {0}")]
    Backend(#[source] BackendError),
}
```

`#[error("...: {0}")]` で内側の `Display` を取り込む。`error.to_string()` 一発でチェーン全体が読める。

### どちらを選ぶか

caller が chain walker 前提なら School A で十分 — caller 側で `source()` を walk して詳細が見える。`error.to_string()` 単独でも詳細を提示したいなら School B。

## 4. 軸 B: `#[source]` を書くか

### 書く

```rust
enum MyError {
    #[error("backend operation failed")]
    Backend(#[source] BackendError),  // chain walker から見える
}
```

caller が chain walker (`anyhow::Error`、`tracing-error`、自前 walker など) を介して内側 error を辿れる。debug 時に **どの段で何が起きたか** が回復可能。

### 書かない

```rust
enum MyError {
    #[error("backend operation failed: {detail}")]
    Backend { detail: String },  // String にしてしまう
}
```

内側 error を `String` 化して持つだけ、`#[source]` は付けない。chain walker は内側を辿れない。`Display` だけが情報源になる (= School B 強制)。

### どちらを選ぶか

`#[source]` を **書くのが default**。書かないとチェーンが切れて debug 困難になる。書かない選択が正当化されるのは、内側 error を構造として保持する意味が薄いケース (例: 外部 OS から受け取った文字列メッセージで、それ以上掘れない情報) くらい。

軸 A (Display で何を書くか) と軸 B (source を露出するか) は **logically 独立**:

| `#[source]` | School A | School B |
| --- | --- | --- |
| あり | caller が chain walker のとき詳細を回復可、`to_string()` は context のみ | `to_string()` で詳細、chain walker でも詳細回復可 (ただし重複の罠あり、後述) |
| なし | `to_string()` も chain walker も内側を見られない (情報損失) | `to_string()` のみで詳細、chain walker からは追えない |

実用上、**`#[source]` あり** を default にしたうえで、軸 A (School A / School B) を caller の前提に応じて選ぶのが筋。

## 5. 重複出力の footgun

機械的に「全部 School B にすれば `to_string()` で全部見える!」とやると、chain walker と組み合わせたとき困る。

3 段の error を考える:

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

この例は `programs/rust-error-display-two-schools` で再現できる。

```console
cd programs/rust-error-display-two-schools
cargo run
```

これを `anyhow::Error` 化して chain walker 系のフォーマッタで出力してみる。

`{:#}` (alternate `Display`、`:` 区切りの 1 行チェーン):

```text
request handling failed: backend operation failed: file not found: foo.txt: backend operation failed: file not found: foo.txt: file not found: foo.txt
```

`{:?}` (`Debug`、"Caused by:" 形式):

```text
request handling failed: backend operation failed: file not found: foo.txt

Caused by:
    0: backend operation failed: file not found: foo.txt
    1: file not found: foo.txt
```

leaf の "file not found: foo.txt" が **3 回** 現れる。各 layer の `Display` が補間で内側を取り込んでいて、その上で chain walker が `source()` を walk するため、同じ情報が二重三重に積み重なる。

この footgun の根は、**軸 A (Display) と軸 B (source) の前提が衝突している** こと: School B は「`to_string()` だけ読まれる」前提で内側を畳み込むのに、`#[source]` 付きだと chain walker から **同じ内側がもう 1 回見える**。

## 6. 直し方: School A と transparent の使い分け

`thiserror` には `#[error(transparent)]` があり、これが「自前メッセージなし、内側の `Display` をそのまま委譲」を表す:

```rust
enum TopError {
    #[error(transparent)]
    Mid(#[from] MidError),
}
```

`TopError::Mid(_)` の `Display` は中の `MidError` の `Display` そのまま。"request handling failed" は付かない。

判断基準:

- **pure-wrap variant** (自前 context を持たず、ただ内側を運ぶだけ) → `#[error(transparent)]`
- **context-bearing variant** (自前 context あり、内側も運ぶ) → `#[error("...: {0}")]` か `#[error("...")]`

例えば「site index N で Lanczos が失敗した」のように自前 context (= site index N) を持つなら interpolation か School A、「Backend エラーをそのまま上に運ぶだけ」なら transparent。

これで pure-wrap 層は追加メッセージを持たず、その層由来の重複は増えない。ただし、context-bearing variant で `source` を `Display` に補間する限り、chain walker は同じ source を次の cause としてもう一度表示する。

つまり、chain walker 側で重複を完全に避けたいなら School A に寄せる:

```rust
#[derive(thiserror::Error, Debug)]
enum SweepError {
    #[error("step failed at site {site}")]             // context のみ (School A)
    Step { site: usize, #[source] source: HeffError },

    #[error(transparent)]                              // 純ラップ → transparent
    Backend(#[from] BackendError),
}
```

一方、`error.to_string()` 単独でも詳細を読めることを優先するなら、context-bearing variant では補間を使う:

```rust
#[derive(thiserror::Error, Debug)]
enum SweepError {
    #[error("step failed at site {site}: {source}")]   // context + 補間 (School B)
    Step { site: usize, #[source] source: HeffError },

    #[error(transparent)]                              // 純ラップ → transparent
    Backend(#[from] BackendError),
}
```

## 7. まとめ

- `thiserror` は **書きやすくする糖衣** であり、policy は決めない。
- 隠れている policy 軸は 2 つ:
  - 軸 A: `#[error("...")]` で自レイヤ context のみか (School A)、内側 `Display` を補間するか (School B)。
  - 軸 B: `#[source]` を書いて chain walker に内側を露出するか、しないか。
- どちらも、caller が chain walker かどうか — つまり **詳細を組み立てる責務を caller に持たせるか / 自レイヤで持たせるか** — で決まる。
- 機械的に補間 (School B) すると重複出力する。`#[error(transparent)]` と `#[error("...: {0}")]` の使い分けで pure-wrap 層の重複は消せるが、context-bearing variant では chain walker での source 重複は残る。完全に避けるなら School A に寄せる。

## 参考

- [thiserror docs](https://docs.rs/thiserror) — `#[error(transparent)]` と `#[source]` の項
- [anyhow docs](https://docs.rs/anyhow) — chain walker としての `{:#}` / `{:?}` フォーマッタ
- `std::error::Error::source()` の RFC 系議論 (Error Handling Project Group 周辺)
