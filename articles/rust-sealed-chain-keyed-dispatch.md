---
title: "ディスパッチトレイトの key を layout から chain へ（仮）"
emoji: "🔑"
type: "tech"
topics: ["rust", "tensornetwork", "設計"]
published: false
---

> **【ドラフト / スケルトンメモ】** #302 完了時にフル執筆する。
> 現時点は「経緯の骨子」と「参照すべき issue / PR / commit / コード位置」の控え。
> 叙述の順序とオチ（一般原理）は確定済み。確定コードは #302 マージ後に流し込む。

## 想定タイトル候補

- ディスパッチトレイトの key を layout から chain へ：正しい抽象の key は意味論的負荷で決まる
- `pub(crate)` にできないトレイトを seal する：テンソルネットワークライブラリの公開面設計
- 「なぜ最初からこうじゃなかったのか」に答える chain-keyed リファクタの考古学

## 角度（thesis）

自作テンソルネットワークライブラリ ariadnetor で、MPS/DMRG の「自由函数を generic に書きたい」要求から生まれた**ストレージ/レイアウトのディスパッチトレイト**（`MpsOps` 等）が公開面に漏れている。これを正す過程で出た3つの非自明な結論を軸にする：

1. **`pub(crate)` には demote できない**（Rust の `private_bounds`）。実現手段は seal。
2. **seal はプラガビリティと矛盾しない**。backend プラガビリティ軸（`ComputeBackend`/`OpsFor`）と storage/layout 軸は直交。後者は linalg が具象である以上「外部には閉じ、内部で増える」taxon で、seal はその透過的反映。
3. **正しい抽象の key（layout か chain か）は、意味論的負荷がどこに載っているかで決まる**。layout が Tier 2 を担っていた間は layout-keyed が局所最適だった。Tier 2 が抜けて初めて chain が唯一の domain object になった。「最初からこうできなかった理由」はこれ。

## ストーリーの骨子（叙述順）

### 導入：phantom blocker から入る

- 「#302 は #107 にブロックされている」という申し送りの検証から始まる。
- 調べると #302 の依存チェーン主張（`#372 + #373 + #107(split_leg) → MPS body unification → #302`）は2つのゴールを混同していた：**(a) ディスパッチトレイトの demote** と **(b) body unification（_dense/_bsp kernel の統合＝トレイト削除）**。
- 「demote する trait は削除できない」ので両者は両立しない別物。#107 が本当に要るのは (b) だけ。→ #107 は #302 の phantom blocker。
- 真の依存は #262 着地のみ（#270 が明記）。

### 本筋1：そもそもトレイトは要るのか（#270 の決着）

- 候補：(i) トレイト廃止＝自由函数化／(ii) chain-keyed sealed trait／(iii)(iv) 部分対応。
- 結論：トレイトには本物の仕事（kernel dispatch）があり完全には消せない。だが public に taxonomy を晒す必要はない。→ (ii) が best。
- 「Tier 2 が `.order()` を要るから layout-keyed が必然」という唯一の口実を #270 が反証（`LayoutOrderCheck` で concrete-layout-free に書ける）。

### 本筋2：`pub(crate)` は無理、seal が答え

- public 自由函数 / DMRG ドライバ（`sweep_2site`/`dmrg_2site`）が trait に bound し、外部テストクレートから消費される。
- `pub fn` が `pub(crate)` trait に bound → `private_bounds` / `private_interfaces`。最小再現で確認。
- ∴ trait は `pub` のまま seal（`pub(crate)` sealed supertrait）。#302 タイトルの「demote to pub(crate)」は不正確 → seal にリタイトル。

### 本筋3：seal はプラガビリティと矛盾しない

- 誤解：「seal するとユーザーが backend を作れない」。
- 実際：backend 軸 = `ComputeBackend`/`OpsFor`（非 sealed、外部実装が現に存在）。`MpsOps` の seal とは別トレイト・無関係。
- `MpsOps` の seal が閉じるのは storage/layout フレーバ追加軸。だが linalg kernel が具象なので**外部からは元々追加不能**＝seal は「既に閉じている事実の明示」。
- storage taxon の将来メンバ棚卸し：本命は **Diagonal**（ITensor の `Diag`、今は演算）、長期で **SU(2) fusion-tree**、fermionic は layout 寄り。一般 Sparse は TN では弱い（対称性スパース＝既に BlockSparse）。StridedArray は taxon の peer でなく Dense の下。
- どれも in-crate でしか増えない（linalg kernel が要る）→ seal を内側から越えて増えるので矛盾しない。`DispatchScalar`（{f32,f64,c32,c64} を seal）と同型。

### 本筋4：chain-key 化とは何か

- layout-keyed：`impl MpsOps for DenseLayout`。`type Storage` 射影、`Mps<Self::Storage, Self>`。→ `L::Storage` が公開面に漏れる。
- chain-keyed：`impl MpsOps for Mps<DenseStorage<T>, DenseLayout>`。`Self`=chain、`type Operator`=Mpo。公開面は `Mps`/`Mpo`/`Operator` の wrapper 型だけ。
- 自由函数の generic param が `L`（layout 原子）→ `M`（chain）に変わるのが核心。kernel 本体は不変。
- residue：backend capability bound `OpsFor<Storage>` だけは storage を参照しがち。完全除去には (あ) host-pin or (い) `BackendFor<M>` の chain-keyed capability を1枚。

### オチ：なぜ最初からこうじゃなかったのか

- (1) 最初は Dense 単一（#185）→ ディスパッチトレイト自体が不要だった。
- (2) 2つ目（BlockSparse）統合時（#221）、既存の layout 型を key に流用するのが局所最小。
- (3) 当時は layout が Tier 2 を担う準-domain-object だったので layout-keyed に具体的正当化があった（#262）。
- (4) その後 #328（call-site-supply）・Tier 2 の linalg 移行・#262（Tensor-only）が制約を一枚ずつ剥がし、layout が純粋な実装詳細に戻って初めて chain が唯一の domain object に。
- **一般原理：抽象は domain object で索引すべきだが、どれが domain object かは実装 taxon が semantic load を手放すまで判別できない。正しい key は意味論的負荷の所在で決まり、それが動けば key も動く。**
- 見落としではなく、#270 が "local minimum" と名指し follow-up（#302）に正しく defer した規律の話でもある。

## 参照スケルトン（最小）

### Issue / PR

| 番号 | 役割 |
|---|---|
| #185 | DMRG 2-site **Dense first** — storage 単一の起点、トレイト不在 |
| #221 | Phase 7: Dense+BlockSparse sweep の trait unification — **ディスパッチトレイト誕生（layout-keyed）** |
| #262 | Tensor architecture redo（Tensor-only surface）+ Tier 2 order-assertion を layout-keyed で符号化 |
| #270 | Trait surface opaqueness feasibility study — layout-keyed を "local minimum / not a necessity" と名指し、chain-keyed (ii) を best 評価、inconclusive 項目（Mpo split/unified, StepResult leak） |
| #271 | post-#262 follow-up filing queue — #302 の出所 |
| #302 | **本題**：seal the dispatch-trait surface（旧題 "demote to pub(crate)" からリタイトル） |
| #107 | BlockSparse permute/fuse_legs/**split_leg**/reshape — phantom blocker の元 |
| #328 | Backend unbundling（call-site-supply）— 制約を剥がした動きの一つ |
| #372 / #373 | linalg harmonize contract / diagonal_scale — 誤った依存チェーンに混ぜられていた（両者 CLOSED 済み） |

### #302 上の一次資料（コメント）

- 2026-06-20 依存チェーン主張（誤）: issue 302 #issuecomment-4759752880
- #107 phantom blocker 訂正（本調査で投稿）: issue 302 #issuecomment-4825516802
- `pub(crate)` 不能 / seal / スコープ A・B 再評価（本調査で投稿）: issue 302 #issuecomment-4826020876

### コード位置（ariadnetor、執筆時点の現行 main）

| 位置 | 役割 |
|---|---|
| `crates/ariadnetor-mps/src/dispatch.rs` | `MpsOps` トレイト + 8 自由函数（layout-keyed の実物。before の引用元） |
| `crates/ariadnetor-algorithms/src/dmrg/dispatch.rs` | `DmrgOps` + `StepResult` leak |
| `crates/ariadnetor-core/src/backend.rs:371` | `ComputeBackend`（**非 sealed**） |
| `crates/ariadnetor-core/src/backend.rs:314` | `DispatchScalar`（**sealed** 先例＝閉じた taxon） |
| `crates/ariadnetor-tensor/src/capability.rs:22` | `OpsFor<St>`（非 sealed） |
| `crates/ariadnetor-tensor/src/capability.rs:107` | `AltHostBackend` 外部実装＝**backend 軸が開いている証拠** |

## 執筆時 TODO（#302 完了後に埋める）

- [ ] Tier 2 → linalg entry check 移行の**具体 PR / commit を特定**（現状は end state〔`LayoutOrderCheck` 不在〕のみ確認。移行コミットの番号は未取得 → fabricate せず要調査）
- [ ] #302 採用スコープ（A: seal のみ / B: chain-key + seal、+ backend residue の (あ)/(い)）の**最終決定と実装 PR** を反映
- [ ] before/after の**確定コード**を dispatch.rs から引用（マージ後の実物に差し替え）
- [ ] seal パターンの実コード（`mod sealed { pub trait Sealed {} }`）を repo の既存例（backend.rs / scalar.rs）と並べる
- [ ] `private_bounds` 最小再現コードを掲載用に整える
- [ ] 図：layout-keyed → chain-keyed の key シフト、backend 軸との直交、semantic load の移動
