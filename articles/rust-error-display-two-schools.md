---
title: "thiserror の Display で何を書くか: 隠れた policy 軸"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["rust", "error", "thiserror", "anyhow"]
published: false
---

## TL;DR

- Rust の library で `thiserror` を採用するとき、`#[error("...")]` の **中身に何を書くか** には大きく 2 流派ある。
- 自レイヤの context のみ書く **School A** (`source()` チェーンを caller が walk する前提) と、内側の `Display` を補間する **School B** (`to_string()` 単独で完結する) が独立した policy 軸として存在する。
- 機械的に School B 化すると、`source()` チェーンを walk する caller (例: `anyhow::Error` の `{:#}` / `{:?}`) と組み合わせたとき **重複出力** が起きる。チェーン表示前提なら School A、`to_string()` 単独完結も欲しいなら `#[error(transparent)]` (純ラップ用) と `#[error("...: {0}")]` (context あり用) の **使い分け** が要る。
- 「library だから `thiserror`」で議論を止めると、その下の Display policy 判断が抜け落ちる。

## 1. library なら thiserror、その先の判断

Rust で library を書くとき、error 型は variant を `match` できる typed enum にしたい — caller が recover できるように。手書きで `impl Display` / `impl Error::source()` / `impl From<...>` を書くこともできるが、生成されるコードと意味的に同等で boilerplate が増えるだけなので、`thiserror` を採用するのが素直。

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("...")]
    Variant(#[source] Inner),
    // ...
}
```

ここまでは結論が出やすい。問題はその先 — `#[error("...")]` の **中身に何を書くか** には複数の方針があり、機械的に書くと caller 側で困ったことになる。

## 2. `Display` の 2 流派

`#[error("...")]` で出力する内容には 2 通りの哲学がある。

### School A: 自レイヤの context のみ

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("backend operation failed")]
    Backend(#[source] BackendError),
}
```

ポイント: `Display` は **その layer が何で失敗したか** だけ書く。内側の error は `source()` 経由で返すだけで、`Display` には混ぜない。

`to_string()` 単独だと "backend operation failed" だけが出る。actionable な詳細を見たい caller は `source()` を walk する責任を持つ。

これは `std::error::Error::source()` を素直に使うモデル。

### School B: 内側の `Display` を補間

```rust
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("backend operation failed: {0}")]
    Backend(#[source] BackendError),
}
```

`Display` の中で内側の `Display` を取り込む。`to_string()` 一発でチェーン全体が読める。

`#[error("...: {0}")]` はこちらを書きやすくする糖衣。`#[source]` 属性を付けると `Error::source()` も自動実装される。

### policy は 1 軸独立に決まる

`thiserror` を採用しても School A / School B の選択は **自動では決まらない**。`#[error("...")]` の中身として書き手が明示的に選ぶ。これが本記事で言う "隠れた policy 軸"。

## 3. 重複出力の footgun

機械的に「全部 School B 化すれば `to_string()` で全部見える!」とやると、`source()` チェーンを walk する caller (例: `anyhow::Error` の `{:#}` / `{:?}`) と組み合わせたときに困る。

### 再現

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
$ cd programs/rust-error-display-two-schools
$ cargo run
```

これを `anyhow::Error` 化して `{:#}` (alternate `Display`, `: ` 区切りの 1 行チェーン) で出力すると:

```text
request handling failed: backend operation failed: file not found: foo.txt: backend operation failed: file not found: foo.txt: file not found: foo.txt
```

`{:?}` (`Debug`, "Caused by:" 形式) で出力すると:

```text
request handling failed: backend operation failed: file not found: foo.txt

Caused by:
    0: backend operation failed: file not found: foo.txt
    1: file not found: foo.txt
```

`leaf` の "file not found: foo.txt" が **3 回** 現れる。各 layer が補間で内側を取り込んでいて、その上で caller がチェーンを walk するため。

### 直し方: School A と transparent の使い分け

`thiserror` には `#[error(transparent)]` があり、これが「自前メッセージなし、内側の `Display` をそのまま委譲」を表す:

```rust
#[derive(thiserror::Error, Debug)]
enum TopError {
    #[error(transparent)]
    Mid(#[from] MidError),
}
```

これで `TopError::Mid(_)` の `Display` は中の `MidError` の `Display` そのまま。"request handling failed" という被せメッセージは付かない。

判断基準は単純:

- **pure-wrap variant** (自前 context を持たず、ただ内側を運ぶだけ) → `#[error(transparent)]`
- **context-bearing variant** (自前 context あり、内側も運ぶ) → `#[error("...: {0}")]`

例えば「site index N で Lanczos が失敗した」のように自前 context (= site index N) を持つなら interpolation、「Backend エラーをそのまま上に運ぶだけ」なら transparent。

これで pure-wrap 層は追加メッセージを持たないので、その層に由来する重複は増えない。ただし、context-bearing variant で `source` を `Display` に補間する限り、チェーンウォーカーは同じ `source` を次の cause としてもう一度表示する。

つまり、チェーン表示で重複を完全に避けたいなら School A に寄せる:

```rust
#[derive(thiserror::Error, Debug)]
enum SweepError {
    #[error("step failed at site {site}")]             // context のみ
    Step { site: usize, #[source] source: HeffError },

    #[error(transparent)]                              // 純ラップ → transparent
    Backend(#[from] BackendError),
}
```

一方、`{e}` 単独でも詳細を読めることを優先するなら、context-bearing variant では補間を使う:

```rust
#[derive(thiserror::Error, Debug)]
enum SweepError {
    #[error("step failed at site {site}: {source}")]   // context あり → interpolation
    Step { site: usize, #[source] source: HeffError },

    #[error(transparent)]                              // 純ラップ → transparent
    Backend(#[from] BackendError),
}
```

## 4. policy 設計のフロー

`thiserror` を採用したうえで、各 error 型ごとに次を判断する:

1. **caller の前提**: caller が **チェーンウォーカー前提** で読むか、`{e}` 単独完結を期待するか。
   - チェーンウォーカー前提なら **School A**。`source()` を walk する側で詳細が見える。
   - `{e}` 単独で動かすなら **School B**。
   - 混在前提 (どちらの caller も来る) なら、pure-wrap は `transparent`、context-bearing variant は補間する、という使い分けが現実的な妥協点。ただしチェーン表示での source 重複は残る。
2. **エコシステム慣習**: 周りのクレートとの一貫性。`thiserror` 圏内なら transparent / interpolation の使い分けが de-facto。

## 5. まとめ

- `thiserror` は「`Display` をどう書くか」を決めない。policy は書き手が独立に選ぶ軸。
- 機械的に補間 (School B) すると、`source()` チェーンを walk する caller で重複出力する。
- `#[error(transparent)]` と `#[error("...: {0}")]` は **policy 軸の使い分け** を表現するための道具。pure-wrap か context-bearing かで使い分ける。
- 「library だから `thiserror`」で停止せず、その下の Display policy を意識的に設計すると、外部 caller の体験が綺麗になる。

## 参考

- [thiserror docs](https://docs.rs/thiserror) — 特に `#[error(transparent)]` と `#[source]` の項
- [anyhow docs](https://docs.rs/anyhow) — `{:#}` / `{:?}` のチェーン表示フォーマッタ
- `std::error::Error::source()` の RFC 系議論 (Error Handling Project Group 周辺)
