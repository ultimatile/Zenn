---
title: "Rust のテスト名は嘘をつく——semantic hygiene の 4 つの failure mode と対応策"
emoji: "🦀"
type: "idea" # tech: 技術記事 / idea: アイデア
topics: ["Rust", "テスト", "リファクタリング", "ソフトウェアテスト"]
published: false
---

## 問題意識

Rust の `#[test]` は関数を test runner に登録するだけの marker であり、 関数名・docstring・assertion 内容のあいだに言語レベルの semantic な紐付けは一切ない。 結果として、 テスト名が中身と乖離していても、 中身が空洞化していても、 一見はパスし続ける。

```rust
#[test]
fn test_returns_clone() {
    // 何も clone を検証していない
    let x = 1 + 1;
    assert_eq!(x, 2);
}
```

これは極端な例だが、 実際のコードベースで起きるのはもっと subtle な drift である。 本稿ではこの「テスト名と中身が semantic に整合しているか」という問題 (以下 **semantic hygiene** と呼ぶ) を 4 つの failure mode に分解し、 それぞれ Rust エコシステムにある どの道具で対応できる/できないかを整理する。

## 4 つの failure mode

### Mode 1: name ↔ assertion drift

テスト名は X を主張しているが、 assertion は Y を検証している。

```rust
#[test]
fn slice_returns_identity_for_scalar() {
    let t = make_scalar(42.0);
    let s = t.slice(&[]);
    assert_eq!(s.shape(), &[]);
    // identity の検証 (data == &[42.0]) を忘れている
}
```

名前は `returns_identity_for_scalar` と読めるが、 中身は shape の検証だけで、 data が保たれているかは見ていない。 typo・refactor・コピペで容易に発生する。

### Mode 2: sibling 間の copy-paste 誤り

近似の sibling test を 2 つ書く時、 片方を書いてからコピペして tag だけ変える運用は、 本文の assertion を書き換え忘れる/取り違える事故を起こしやすい。

```rust
#[test]
fn slice_scalar_row_major() {
    let t = Dense::new(vec![42.0], vec![], MemoryOrder::RowMajor);
    let s = t.slice(&[]);
    assert_eq!(s.order(), MemoryOrder::RowMajor);
}

#[test]
fn slice_scalar_column_major() {
    let t = Dense::new(vec![42.0], vec![], MemoryOrder::ColumnMajor);
    let s = t.slice(&[]);
    assert_eq!(s.order(), MemoryOrder::RowMajor); // ← コピペ事故、 RowMajor のまま
}
```

両方ともパスするので CI は気付かない。 関数名の `column_major` と中身の `RowMajor` が乖離しているが、 Rust 側に検出機構はない。

### Mode 3: stale assertion

元々ある bug を検出していた assertion が、 bug 修正後・周辺の API 変更後に「別の理由でたまたま pass し続ける」状態。 テストは緑のまま、 contract は事実上消失する。

典型的なのは 「最初は tight だった predicate が、 bug 修正後に loose な真理値命題に劣化する」 パターン。 たとえば 元々 `parse("42")` が bug で `0` を返していたのを catch するため こう書いたとする:

```rust
#[test]
fn parse_number_returns_positive() {
    assert!(parse("42") > 0); // 元 bug: parse は常に 0 を返していた
}
```

bug を fix して `parse("42")` が `42` を返すようになると、 test は当然 pass する。 ところがこの assertion は **「元の bug 1 つ」 を catch するためには十分だったが、 fix 後はほとんど何も guard していない**。 後の refactor で `parse("42")` が `100` を返すように壊れても、 `100 > 0` なので test は緑のまま通る。

別パターン:

```rust
// 元 bug: divisor が 0 のとき panic
fn safe_divide(a: f64, b: f64) -> f64 {
    if b == 0.0 { f64::INFINITY } else { a / b }
}

#[test]
fn safe_divide_no_panic() {
    let _ = safe_divide(1.0, 0.0); // panic しないことを暗黙に確認
}
```

この test は `safe_divide` の戻り値を一切見ていない。 元 bug ( panic ) を catch する目的では機能したが、 「`f64::INFINITY` ではなく誤って `0.0` を返す」 ような regression が入っても素通しする。 contract は test 名と実装変遷の隙間に落ちて消えている。

人間 review では見抜けないことが多い。

### Mode 4: degenerate-input-only な「general 主張」テスト

「general property」を主張しているのに、 実際は identity 行列・1 要素・対称行列など非常に狭い退化入力でしか検証していない。

```rust
#[test]
fn matmul_is_associative_for_general_matrices() {
    // 単位行列だけで検証——これは any matrix の associativity の証拠ではない
    let i = identity(3);
    assert_eq!(matmul(&i, &matmul(&i, &i)), matmul(&matmul(&i, &i), &i));
}
```

testing pyramid の上で大きな顔をしているわりに、 実際のカバレッジは退化入力の 1 点だけ。

## 各 failure mode に効く道具

4 つの mode は **直交している**。 1 つの道具で全部塞ぐことはできず、 stack を組む発想が必要になる。

### table-based testing は何を解決するか

`rstest` (de facto standard, 2026 時点)・`test-case` などで test 本体を 1 つに集約し、 ケースを data row として与える方式。

```rust
use rstest::rstest;

#[rstest]
#[case(MemoryOrder::RowMajor)]
#[case(MemoryOrder::ColumnMajor)]
fn slice_scalar_is_identity(#[case] order: MemoryOrder) {
    let t = Dense::new(vec![42.0], vec![], order);
    let s = t.slice(&[]);
    assert_eq!(s.shape(), &[] as &[usize]);
    assert_eq!(s.data(), &[42.0]);
    assert_eq!(s.order(), order);
}
```

| mode | 解決? | 理由 |
|---|---|---|
| (1) name drift | ❌ | 関数名と本体の乖離は構造的に変わらない |
| (2) copy-paste 誤り | ✅ **構造的に抑える** | 本体は 1 つ、 ケースは data row。 sibling 本文の片側だけ assertion を書き換え忘れる事故は構造的に起きにくくなる (case row 側の値を誤る事故は残る) |
| (3) stale assertion | ❌ | row が増えても assertion 空洞化は検出できない |
| (4) coverage gap | ❌ | hand-picked row をいくつ並べても general property の証明にはならない |

つまり table-based は **mode 2 専用の道具** であり、 「テスト衛生全般を改善する」 と期待すると裏切られる。 ただし mode 2 が起きうる状況 (RM/CM のような同型 sibling) では極めて effective で、 cargo / rust-analyzer の test filter も `case_1`, `case_2` で個別に効くため debugging で困らない。

### Rust の table-based testing 比較 (2026 時点)

| crate | 強み | 弱み | filter |
|---|---|---|---|
| **rstest** 0.26.x | proc-macro、 cartesian via `#[values]`、 fixture 関数注入、 rust-analyzer Test Explorer 対応 | proc-macro 由来の追加 compile cost はあるが、 通常規模では支配的でない | `cargo test fn::case_1` |
| **test-case** 3.3.x | label を `;` で inline、 1 行 1 case で読みやすい | fixture なし、 rstest の機能 subset | label を snake_case 化したものでfilter |
| **`paste!` hand-rolled** | proc-macro 禁止環境用 | trace が macro 展開を指して debug 困難、 2022 年的 legacy | OK |
| **`for` loop in 1 test** | zero-dep | first failure で abort, IDE 表示なし, cargo filter 不能 | 1 つのみ |

実用上の第一候補は `rstest` でよい。 `test-case` は fixture を使わない短い表で readability が一段上だが、 機能的には rstest の subset。

### mutation testing が解決する mode

`cargo-mutants` は production code に変異を加えてテストが落ちるかを観測する。 「テストがパスし続けるが本来 guard したい性質を guard していない」 状態の **構文的に表現できる範囲** を暴く。

| mode | 解決? | 理由 |
|---|---|---|
| (1) name drift | ❌ | テスト名は読まない (テストは function 単位の pass/fail のみ観測) |
| (2) copy-paste 誤り | △ | 両 sibling が同じ mutant を catch すると「両方とも die」 だけ観測でき、 重複自体は flag されない |
| (3) stale assertion | △ **syntactic mutation の射程内のみ** | mutator が生成する構文変異 (`+ → -`、 リテラル置換、 比較演算子反転、 boundary `<` ↔ `<=` 等) について「変異させても test が通る = assertion 空洞化」 が surface する |
| (4) coverage gap | △ partial | 退化入力で到達しない branch を変異させると missed mutant になる。 ただし「到達はしているが assertion が semantic を guard していない」 ケースは対象外 |

#### syntactic mutation の限界

mutation testing の決定的な性質: cargo-mutants が生成するのは **syntactic mutation** であり、 **semantic mutation ではない**。 mutator は固定のパターン集合 (二項演算子の置換、 リテラル値の差し替え、 条件式の反転、 早期 return 挿入、 等) から変異を生成する。 この集合に含まれる構文変化が semantic な違反を生めば missed mutant として surface するが、 集合の **外側** にある semantic 違反 (典型的には: 軸の取り違え、 layout 不変条件の破壊、 stride 計算の semantic 誤り、 数値積算の順序依存、 並行性に関する仮定違反、 …) は **どんなに stale な assertion を抱えていても missed mutant として現れない**。

これは原理的限界で、 mutator のパターン集合を拡張しても本質的に解決しない。 production code の semantic な不変条件を mutator が「知って」 違反する変異を生成するには、 仕様を機械可読な形で別途与える必要があり、 そうなるともはや mutation testing ではなく formal verification (kani 等) の領域に入る。

それでも cargo-mutants をやる意味は十分ある: 構文変異の射程内に落ちる stale assertion は実務上かなり多く、 それらを mechanical に拾えるだけで postmortem 由来の review 負荷は確実に下がる。 「全 stale assertion を捕まえる完全な道具」 ではなく 「捕まえやすい subset を機械化する道具」 と位置付けるのが正しい。

運用 cost は高い: 全 mutant に対し full rebuild + test 実行が走るため遅く、 unviable mutant の suppression に `mutants.toml` のチューニングが要る。 CI gate に乗せるなら slice 単位 / file 単位の sharding が現実的。

### property-based testing が解決する mode

`proptest` (active maintenance) で「入力空間の任意元に対する property」 として書く。

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn reverse_twice_restores_input(
        xs in proptest::collection::vec(any::<i32>(), 0..128)
    ) {
        let ys = xs.iter().copied().rev().collect::<Vec<_>>();
        let zs = ys.iter().copied().rev().collect::<Vec<_>>();
        prop_assert_eq!(zs, xs);
    }
}
```

(matmul 結合則を `prop_assert_eq!` で書きたくなりがちだが、 浮動小数だと結合順序の違いで丸め誤差が変わるため exact equality は成立しない。 整数リストの reverse 二回 = 恒等のような closed-form な代数的同値で、 まず proptest の論点だけを浮かび上がらせる例にしておく。)

| mode | 解決? | 理由 |
|---|---|---|
| (1) name drift | ❌ | property の記述は依然として人間が書く prose |
| (2) copy-paste 誤り | ❌ (orthogonal) | sibling とは別軸 |
| (3) stale assertion | △ | 入力域を広げることで、 特定入力にだけ偶然成立する weak assertion を見抜きやすくする (exhaustive ではなく sampling なので統計的な検出) |
| (4) coverage gap | △〜○ | generator が主張したい入力空間を適切に表せていれば強い。 ただし sampling であり証明ではない |

「general property」 を口にしたくなったら、 まず proptest を検討する。 ただし proptest 自体は exhaustive search ではなく randomized sampling (default 256 cases、 PROPTEST_CASES で調整可) で、 generator が claim に対応していなければ「退化入力しか見ていない」 問題を別の形で再生産する。 generator design (= 入力空間の表現) こそが真の難所で、 「proptest を入れた = general property を guard した」 ではない。

### Mode 1 はなぜ機械的に解決できないか

「関数名 (英語の自然言語文字列) が assertion (logical predicate) と semantic に一致しているか」 は、 自然言語 parser + AST 解析を要する課題で、 Rust には当然そのような検出器はない。 周辺で部分的に効く道具を挙げると:

- **doctest**: `///` に埋めた例コードが compile/run し、 例中の assertion も実行される。 public API の **使用例コードが陳腐化する** drift は防ぎやすい。 ただし自然言語の説明文そのものとコードの semantic 一致は判定しないので、 「説明文は X と書いているが例は Y を示している」 形の drift は検出範囲外
- **`googletest-rs` の matcher**: `expect_that!(x, eq(expected))` のような structured matcher は人間 review での読みやすさを上げ、 名前と中身の乖離が目視で気付きやすくなる。 mechanical enforcement はゼロ
- **cucumber-rs (BDD)**: feature ファイルに contract を English で書き、 step 定義と紐付ける。 text drift を「feature ファイル vs step」 という co-located な surface に押し込める。 ceremony cost が高く、 100 test 規模の library では割に合わない

結局 mode 1 は **process でしか塞げない**。 review 文化、 contract test の elevation 規律 (postmortem 後に implicit な spec を test に立てる)、 docstring の drift sweep。 これらは人間が回す。

### その他の test infra の hygiene 寄与

| tool | mode 1 | mode 2 | mode 3 | mode 4 | note |
|---|---|---|---|---|---|
| **cargo nextest** | ❌ | ❌ | △ | ❌ | speed/CI 用、 hygiene 副産物のみ (process isolation で global pollution 暴露) |
| **kani** (formal) | ❌ | ❌ | ✅ 強力 | ✅ 強力 | bounded proof。 panic / overflow / custom assertion / `unsafe` 由来の安全性も対象。 proof harness 設計と問題の切り出しが必要、 適用範囲と cost は重い (concurrency は未対応) |
| **miri** | ❌ | ❌ | △ | ❌ | UB 起因の偽 pass のみ、 `unsafe` 周辺で必須 |
| **loom** | ❌ | ❌ | △ | ❌ | concurrency primitives のみ |
| **insta** (snapshot) | ❌ | △ | ❌ **悪化リスク** | ❌ | `cargo insta accept` で誤値固定する anti-pattern |
| **cargo-llvm-cov** | ❌ | ❌ | ❌ | △ | line/branch の未到達箇所発見には有効。 ただし退化入力だけで general claim を装う問題 (=branch には触れているが degenerate input でしか触れていない) は coverage では直接 surface しない |

## 推奨 stack

ROI 順:

1. **`rstest` を導入** — sibling pair が登場する箇所 (RM/CM、 f32/f64、 row/col、 …) を 1 fn に圧縮。 dev-dep 1 個、 mode 2 (本体側の copy-paste drift) を構造的に抑える
2. **`cargo-mutants` を CI に乗せる** — 主要 file を slice 単位で定期実行、 missed mutants list を triage する flow。 mode 3 のうち syntactic mutation の射程内に落ちる subset と mode 4 の partial を捕捉。 semantic mutation を表現できない原理的限界は別道具 (proptest, kani) で補う
3. **`proptest` は選択的に** — 「any / general / for all」 を主張したい test (algebraic identity, layout invariance 等) に限って導入。 全 test を property 化するのではなく、 量化したい contract のみ
4. **mode 1 は process で対処** — bug-to-contract 規律、 docstring drift sweep、 contract test の elevation を review pipeline に組み込む

`miri` は `unsafe` を含む箇所のみ、 `kani` は適用範囲次第で非常に強いが proof harness 設計のため初期 cost が大きく、 0.1.x 段階の library には先行投資としては重い。 `nextest` は hygiene には効かないが CI speed には効くので別軸で採用判断。

## まとめ

- Rust の `#[test]` は単なる marker であり、 名前・docstring・assertion の semantic 整合は言語に保証されない
- 4 つの failure mode (name drift, copy-paste, stale assertion, degenerate-input) は直交しており、 1 つの道具で全部塞ぐことはできない
- table-based testing (`rstest`) は **mode 2 専用** の構造的な抑制策。 期待を広げすぎない (case data 側の値間違いは別途残る)
- mode 3 は `cargo-mutants` (ただし syntactic mutation の射程内のみ。 semantic mutation は原理的に対象外)、 mode 4 は `proptest` (ただし sampling であって exhaustive ではなく、 generator design がそのまま guard 強度になる)
- mode 1 は **機械的に解決する道具が存在しない**。 process 規律でしか塞げない、 という事実を直視するところから始める
