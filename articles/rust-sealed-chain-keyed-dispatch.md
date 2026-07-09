---
title: "型パラメータの座席は意味論的負荷で決まる：Rustテンソルライブラリ8ヶ月の紆余曲折"
emoji: "🪑"
type: "tech"
topics: ["rust", "tensornetwork", "設計"]
published: false
---

## この記事は何か

自作のテンソルネットワークライブラリ [ariadnetor](https://github.com/ultimatile/ariadnetor) で、中心となる `Tensor` 型のジェネリックシグネチャが約8ヶ月のあいだに5回変わりました。パラメータは増えただけではなく、導入されて3ヶ月後に丸ごと削除されたものもあります。さらにシグネチャが安定した後にも、`Tensor` を扱うディスパッチトレイトの key（何に対して `impl` するか）が付け替えられました。

この記事はその変遷を時系列で追いながら、個々の判断を貫いていた一般原理をひとつ取り出します。結論は次のとおりです。

- 型パラメータ・型の層・トレイトの key といった「型システム上の一等地」（本記事では**座席**と呼びます）に座れるのは、**意味論的負荷**を持つ軸だけである
- ある軸が意味論的負荷を持つかどうかは、実装が進んで負荷の所在が動くまで観測できない
- したがって最初から正しい形は書けないが、負荷の移動への追随はできる

ここで「意味論的負荷を持つ」とは、その軸の値の違いが単なる実装差ではなく、呼び出し側の書くコード・型検査の結果・演算の意味を独立に変えることを指します。以下の各章は、この語彙で読み直せる実例集です。

なお ariadnetor はテンソルネットワーク計算（行列積状態などを使った量子多体系の数値計算手法）のためのライブラリですが、この記事の内容は Rust のジェネリクス設計の話であり、テンソルネットワークの知識は要りません。「多次元配列を扱う型があり、密な格納形式とブロックスパースな格納形式がある」ことだけ分かれば読めます。

## 変遷の全体像

全体像は次の1枚の表のとおりです。各行の詳細は後の章で扱います。

| 時期 | `Tensor` の形 | 何が起きたか |
| --- | --- | --- |
| 2025-10 | `FatTensor { tensor: RawTensor<T>, labels }` | 二層構造で出発 |
| 2026-02 | `Tensor<T>`（内部に storage の enum） | 二層を単一型に統合（[#5](https://github.com/ultimatile/ariadnetor/issues/5)） |
| 2026-03 | `Tensor<T, B>` | テンソルごとの backend パラメータ `B` が着席 |
| 2026-03 | `Tensor<R, B>` | storage の enum をジェネリクスに置換（[#85](https://github.com/ultimatile/ariadnetor/issues/85)） |
| 2026-05 | `Tensor<St, L, B>` | storage / layout を分離（[#274](https://github.com/ultimatile/ariadnetor/issues/274)） |
| 2026-06 | `Tensor<St, L>` | `B` が退席し、呼び出し側供給へ（[#348](https://github.com/ultimatile/ariadnetor/issues/348)） |
| 2026-06 | （シグネチャ不変） | ディスパッチトレイトの key を layout から chain へ（[#302](https://github.com/ultimatile/ariadnetor/issues/302)） |

パラメータ数だけ見ると 1 → 2 → 2 → 3 → 2 と往復しています。以下、山場となる3つの変化（二層構造の統合、`B` の往復、key の付け替え）を厚く、間の変化を短く追います。

## 前史：FatTensor / RawTensor の二層構造

出発点は既存ライブラリの模倣でした。テンソルネットワーク計算の先行ライブラリである [Cytnx](https://github.com/Cytnx-dev/Cytnx)（`Tensor` / `UniTensor`）や [ITensors.jl](https://github.com/ITensor/ITensors.jl)（`NDTensors.Tensor` / `ITensor`）は、生の多次元配列の層と、インデックスラベルなどのメタデータを持つ層の二層構造を採っています。ariadnetor もそれに倣い、下層 `RawTensor`（格納と演算実装、縮約の意味論を持たない）と上層 `FatTensor`（ラベルを持ち、ラベルベースの自動縮約 API を提供する）に分けました。

```rust
// 下層: 格納形式の enum。演算子 * は意図的に持たない
pub enum RawTensor<T = f64> {
    Dense(DenseTensor<T>),
    // TODO: Phase 1+ - Sparse tensor support
    // TODO: Phase 2+ - Block-sparse tensor support
}

// 上層: メタデータ付き。公開 API は type Tensor = FatTensor
pub struct FatTensor<T = f64> {
    pub tensor: RawTensor<T>,
    pub labels: Vec<LabelId>,
}
```

型で層を分けたのは安全のためでもありました。`RawTensor × FatTensor` の混在演算をコンパイルエラーで禁止し、縮約の曖昧さを型で根絶する、というのが当時の設計メモの言い分です。

この構造は約3.5ヶ月で廃止されます。実装を進めるうちに露呈した問題は2つありました。

第一に、メソッドの二重保守です。`scale` / `norm` / `normalize` といった演算はすべて `RawTensor` に実装され、`FatTensor` は同名メソッドをラベル維持のためだけに再宣言して転送していました。この転送だけのメソッドが13個あり、上層の実体はほぼボイラープレートでした。

```rust
// FatTensor 側の典型的なメソッド: 転送してラベルを付け直すだけ
pub fn scaled(&self, factor: T) -> Self {
    Self { tensor: self.tensor.scaled(factor), labels: self.labels.clone() }
}
```

第二に、上層の目玉機能だった遅延縮約演算子（`*` が縮約式を返し、後から評価する API）は、設計メモに仕様だけ書かれたまま一度も実装されずに層ごと廃止されました。混在演算の型レベル禁止とラベルベース自動縮約という二層構造の存在理由のうち、後者は最後まで紙の上にしかなかったことになります。

とどめを刺したのはラベルの軽量化です。当初 `FatTensor` は ITensor 流の重い `Index` 集合（タグ・prime level 付き）を持つ設計でしたが、設計からわずか2週間後にこれを値型の `LabelId(u64)` に置き換えました。軽いラベルなら prime level のような仕掛けは不要になり、メタデータ層の中身が痩せます。その後、残ったラベルはテンソル単体ではなくネットワークのトポロジーに属する情報だとして別型 `TensorNetwork` へ移し、対称性のブロック構造は格納形式側の仕事だと整理した時点で、当時の設計メモに「Fat 層に残るものがない」と書かれる状態になりました。統合コミットの diff は553行追加・926行削除、つまり層を消しただけで正味373行減っています。

座席の語彙で言い直すと、こうなります。「型の層」という座席は、その層がメタデータという負荷を担っているあいだだけ正当でした。ラベルが `TensorNetwork` へ、対称性が storage へ引っ越した瞬間に座席は空席になり、空席の層は転送ボイラープレートの製造装置でしかなくなります。模倣元の Cytnx や ITensors.jl の上層が正当なのは、そこにタグ・prime level・量子数の向きといった重い負荷が現に載っているからで、二層構造そのものに価値があるわけではありませんでした。

## 幕間：enum の退場と backend の着席

統合後の `Tensor<T>` は格納形式を enum で持っていましたが、これは2026年3月にジェネリクスへ置き換えられます（[#83](https://github.com/ultimatile/ariadnetor/issues/83)）。決め手は将来のブロックスパース対応でした。ブロックスパース形式は対称性の型 `S` を持つため、enum のままでは `TensorStorage<T, S>` → `Tensor<T, S, B>` という形で `S` が全シグネチャに伝播し、密テンソルしか使わないコードにまで `S` を書かせることになります。また enum では `data()` のようなアクセサが非対応 variant で `None` を返すしかなく、型で保証できるはずの不変条件が実行時チェックに落ちていました。格納形式を型パラメータにすれば、どちらの問題も消えます。

同じ時期に、テンソルごとの計算 backend パラメータ `B` が着席しています。`Tensor<T, B: ComputeBackend>` が `Arc<B>` を保持し、CPU ユーザーはデフォルトの `NativeBackend` により `Tensor<f64>` とだけ書けばよい、という設計です。この時点では妥当に見えた判断が3ヶ月後にどうなるかは、次の次の章で扱います。

## 座席の新設：storage / layout の分離

2026年5月、格納形式パラメータがさらに `St`（純粋なバイト列としての storage）と `L`（shape やメモリ順序を持つ layout）に分かれ、`Tensor<St, L, B>` になりました。[PyTorch](https://github.com/pytorch/pytorch) が opaque な `Storage` の上に strides / sizes を持つ `Tensor` を重ねているのと同じ分割です。

この分離の伏線は、メモリ順序（row-major / column-major）が長らく座席を持たない**暗黙の規約**として運用されていたことです。テンソル自身はメモリ順序を知らず、「backend の preferred order で埋まっているはず」という了解だけがコードベースを支えていました。この了解は実際にバグを生んでいます。row-major で埋めたテスト用データを column-major 前提の構築函数に渡していたのに、fixture が Hermite 行列で転置不変だったためにテストが通り続けていた、という事例です（[#202](https://github.com/ultimatile/ariadnetor/issues/202)）。応急処置としてメモリ順序のタグを storage に付けましたが、当時の設計ノート自身がこれを中間状態と認めており、最終的に「解釈のメタデータは layout に、バイト列は storage に」という形で座席を新設して決着しました。

なおこの移行は一発で着地していません。最初の実装 PR（[#260](https://github.com/ultimatile/ariadnetor/issues/260)）は、内部型 `TensorData` が公開 API に漏れて不正なメモリ順序の構築を許すという設計問題がレビューで露呈し、丸ごと破棄されました。仕切り直し（[#262](https://github.com/ultimatile/ariadnetor/issues/262)）では `Tensor` だけを公開面に残す方針へ改め、混在メモリ順序のバグ族を構築時と演算入口の検査で構造的に閉じています。

## 往復した backend パラメータ

山場の2つ目は `B` の削除です。2026年3月に着席した per-tensor backend は、6月に丸ごと退席しました（[#348](https://github.com/ultimatile/ariadnetor/issues/348)）。`Tensor<St, L, B>` から `B` と `Arc<B>` フィールドが消え、現在の形になります。

```rust
pub struct Tensor<St, L>
where
    St: Storage + StorageFor<L>,
    L: TensorLayout,
{
    data: TensorData<St, L>,
}
```

削除の引き金は GPU などの状態を持つ backend の検討でした。各テンソルが自分の backend を抱えていると、N 個のテンソルからなる行列積状態を構築するとき、N 個のサイト backend と1個のチェーン backend という「N+1 個の権威」の実行時照合を強いられます。どの backend が正なのかという問いに構造的な答えがなく、コンストラクタごとに照合コードが増殖していました。

診断はこうです。デバイス（このデータがホストメモリにあるか GPU メモリにあるか）は storage の事実であり、`St` を見れば決まります。つまり `B` は `St` から従属的に決まる軸であって、型レベルで独立に変わる軸ではありませんでした。独立に変わらない軸へ座席を与えると、情報が二重になり、二重化した情報は照合を要求します。N+1 権威問題はその照合コストの現れでした。

退席した `B` の引っ越し先は2つです。値としての backend は各演算の**呼び出し側引数**になり（`svd(&tensor, &backend, ...)` の形）、「この backend はこの storage を処理できるか」という適合性だけがコンパイル時のマーカートレイト `OpsFor<St>` として型システムに残りました。[Kokkos](https://github.com/kokkos/kokkos) の `SpaceAccessibility` と同じ発想です。着席時の判断が誤りだったというより、backend が従属軸だという事実は、状態を持つ backend を検討して初めて観測可能になりました。

## key も座席である：ディスパッチトレイトの封印

最後の山場はシグネチャに現れません。`Tensor` の形が安定した後、行列積状態のアルゴリズム群を密・ブロックスパース両対応でジェネリックに書くためのディスパッチトレイト `MpsOps` の key が付け替えられました（[#302](https://github.com/ultimatile/ariadnetor/issues/302)、実装は [#427](https://github.com/ultimatile/ariadnetor/issues/427) / [#429](https://github.com/ultimatile/ariadnetor/issues/429)）。

このトレイトの生い立ちから話す必要があります。密テンソル一本だった時代、ディスパッチトレイトは存在しませんでした。ブロックスパース対応で密・ブロックスパース2本のカーネルを1つのジェネリック函数から呼び分ける必要が生じたとき（[#221](https://github.com/ultimatile/ariadnetor/issues/221)）、手近にあった layout 型を key に流用してトレイトが生まれます。

```rust
// before: layout が key
pub trait MpsOps<T: Scalar>: TensorLayout + Sized {
    type Storage: Storage + StorageFor<Self>;
    // ... カーネルメソッド群
}
impl<T: Scalar> MpsOps<T> for DenseLayout { /* ... */ }
```

これで動きはするのですが、公開面に問題が出ます。公開の自由函数やソルバーはこのトレイトを境界に使います。そのため「格納形式は Dense と BlockSparse に分かれる」という内部の分類学（taxonomy）が `L::Storage` 射影ごと公開 API へ漏れ、ユーザーの実装すべきでないトレイトを実装可能な形で晒してしまいます。

最初の案は「トレイトを `pub(crate)` に降格する」でした。これは Rust の言語仕様で不可能です。`pub fn` の境界に `pub(crate)` トレイトを置くと `private_bounds` エラーになるため、公開函数から使われる限りトレイトは `pub` でなければなりません。可能なのは降格ではなく **seal**（`pub` のまま、非公開の supertrait を要求して外部実装だけを禁じる）でした。

seal と同時に key を付け替えます。`impl` の対象を layout 原子から、ユーザーが実際に触るチェーン型そのものへ変えました。

```rust
// after: chain が key、sealed
pub trait MpsOps<T: Scalar>: sealed::Sealed {
    type Layout: TensorLayout;
    type Storage: Storage + StorageFor<Self::Layout>;
    // ... カーネルメソッド群
}
impl<T: Scalar> MpsOps<T> for Mps<DenseStorage<T>, DenseLayout> { /* ... */ }
```

これでジェネリック函数の型パラメータは「layout `L`」から「チェーン `M`」に変わり、公開面に現れる型はユーザーが構築する `Mps` / `Mpo` だけになりました。

なお、事前の想定とずれた点が2つありました。第一に、taxonomy は消去できず封印止まりでした。`Self = Mps<St, L>` から `L` を型レベルで取り出し直すことはできないため、`Storage` / `Layout` は関連型としてトレイト表面に残っています。ただし sealed なので外部から実装も参照拡張もできず、「分類学は存在するが、外からは増やせないし依存もできない」という状態です。第二に、backend 適合性を chain-keyed の `BackendFor<M>` に置き換える案は型検査を通りませんでした（`B: BackendFor<Mps<...>>` から `B: OpsFor<DenseStorage<T>>` をコンパイラが復元できない）。封印された関連型経由で `OpsFor<Self::Storage>` を要求する形が着地点です。

さて、この記事の観点で重要なのは「なぜ最初から chain-keyed にしなかったのか」です。答えは、layout がかつて意味論的負荷を持っていたからです。storage / layout 分離の直後、メモリ順序の検査という仕事は layout 型の関連定数・関連函数に載っており、layout はただの実装詳細ではなく準 domain object でした。その負荷が線形代数層の入口検査に移り、layout が純粋な実装詳細に戻ったことを確認した調査（[#270](https://github.com/ultimatile/ariadnetor/issues/270)）が「layout-keyed は局所最適であって必然ではない」と結論して、初めて chain への付け替えが可能になりました。トレイトの key は「この抽象を何で索引するか」という座席であり、domain object だけが座れます。しかしどれが domain object なのかは、実装側の分類学が意味論的負荷を手放すまで判別できないのです。

## 座席を失った軸はどこへ行くか

ここまでの変遷を「座席の改廃」として整理すると、退席した軸の引っ越し先には決まったパターンがあると分かります。設計を見直すとき、このカタログは「型パラメータを消したいが情報は残したい」場面の選択肢一覧として使えます。

| 引っ越し元 | 引っ越し先 | この記事での例 |
| --- | --- | --- |
| 型の層（wrapper 型） | 別の型・内部フィールド | labels → `TensorNetwork`、対称性 → storage 内部 |
| enum の variant | 型パラメータ | `TensorStorage::Dense` → `Tensor<DenseStorage<T>, _>` |
| 型パラメータ | 呼び出し側の引数 | `B` → 各演算の backend 引数 |
| 型パラメータ（の公開性） | sealed な関連型 | ディスパッチトレイトの `Storage` / `Layout` |
| トレイトの key | 別の key（domain object） | layout-keyed → chain-keyed |
| 暗黙の規約 | 新設の型パラメータ | メモリ順序 → `DenseLayout`（`L`） |

向きは一方通行ではありません。メモリ順序のように、座席なし（暗黙の規約）からバグを経由して座席を獲得した軸もあります。判定基準はどの行でも同じで、「その軸は型レベルで独立に変わり、その違いが呼び出し側の意味を変えるか」です。変えるなら座席を与え、変えないなら座席から降ろして従属先に畳み込む、というだけの話を、このライブラリは8ヶ月かけて6回やったことになります。

## まとめ

冒頭の原理を、実例を通った後の言葉で言い直します。

- 型パラメータ・型の層・トレイトの key は希少な一等地であり、そこに座れるのは意味論的負荷を持つ軸だけである。負荷のない座席は転送ボイラープレート（FatTensor）、実行時照合（`B` の N+1 権威）、taxonomy の漏出（layout-keyed トレイト）として設計にコストを請求してくる
- どの軸が負荷を持つかは静的には決められない。`B` の従属性は状態を持つ backend を検討して初めて見え、layout の負荷解放は別目的のリファクタ3件の帰結として事後に観測された
- したがって設計の巧拙は「最初に正しい座席表を書けたか」ではなく「負荷の移動を観測したとき追随できたか」に現れる

最後の点には、それを実務で支えていた条件がひとつあります。このライブラリでは各時点の設計判断が、その判断の依拠する前提ごと記録されていました。layout-keyed を「局所最適」と名指しして付け替えを後続タスクに切り出したのも、storage / layout 分離の最初の実装を破棄して仕切り直せたのも、「当時なぜそうしたか」が前提付きで残っていたからです。負荷の移動が事後にしか見えない以上、今の形の正当化とその前提を書き残すことが、将来の自分が安全に座席表を書き換えるための条件になります。
