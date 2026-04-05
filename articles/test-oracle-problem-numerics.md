---
title: "実践的な数値計算テストの考え方——テストオラクル問題の脱神秘化"
emoji: "🔢"
type: "idea" # tech: 技術記事 / idea: アイデア
topics: ["テスト", "数値計算", "ソフトウェアテスト"]
published: false
---

## 導入: テストオラクル問題のフレーミングの問題

テストオラクル問題は一般に「正解がわからない」問題として紹介されることが多いですが、この表現はミスリーディングで、2つの異なる問題を混在させています。

| 表現 | 実際の意味 |
|---|---|
| オラクル未知 | 判定手続き $D$ の構成法がわからない（正解 $G$ は存在する） |
| オラクル不在 | 正解 $G$ 自体が存在しない（未解決の科学の問題） |

Barr et al. (2015) のサーベイによれば、テストオラクル問題とは「テストオラクル（正しいか否かを判定する手続き $D$）の**自動構成**が困難」という問題であり、正解（ground truth $G$）の**存在**は前提されています。「テストオラクル問題」という名前は仰々しすぎます。実態は「テストオラクル自動構成問題」であり、論文自身も "test oracle automation" という表現を多用しています。

しかしこの整理でもまだ不十分です。「オラクル未知」とされるものの多くは、実は**テストの枠組みで扱うべき問題ではありません**。

### テストオラクルのsoundnessとcompleteness

Barr et al.はテストオラクル $D$ を $T_A \to \text{Bool}$ の**部分関数**[^partial]として定義し、ground truth $G$（常に正解を返す全関数）に対するsoundness/completenessを定義しています。

[^partial]: 部分関数とは、定義域のすべての要素に対して値が定まるとは限らない関数のことです。テストオラクル $D$ が部分関数であるとは、あるテスト入力に対して $D$ が判定を返さない（pass/failのどちらとも言えない）場合がありうることを意味します。全入力に対して正しく判定を返す全関数のオラクルは $G$ そのものと等価であり、構成不可能です。

- **Sound**: $D(a) \Rightarrow G(a)$（$D$ が受理したものは本当に正しい）
- **Complete**: $G(a) \Rightarrow D(a)$（正しいものは全て $D$ が受理する）

テスト用語との対応は以下の通りです:

- soundness違反 = **偽陰性**（テストが通るが実際はバグ——バグの見逃し）
- completeness違反 = **偽陽性**（テストが落ちるが実際は正しい——誤検出）

$D$ が部分関数なのは形式的な都合ではなく、原理的にそうならざるを得ません。Riceの定理により、プログラムの非自明な意味論的性質は全て決定不能であり、soundかつcompleteな全関数 $D$ は $G$ 自体と等価で構成不可能です。Dijkstraの「テストはバグの存在を示せるが、不在を証明できない」も同じことを言っています。

## テストと実験の区別

数値計算の品質保証には、テストの枠組みで扱えるものと扱えないものがあります。この区別が「テストオラクル問題」の混乱の根本にあります。

| | テスト | 実験的検証 |
|---|---|---|
| 判定 | pass/fail（二値） | 比較・傾向・解釈（連続） |
| 自動化 | CI/CDで毎回回す | 人間が設計し解釈する |
| 対象 | 実装の正しさ | 手法の妥当性・品質 |
| 数値計算での例 | 不変量チェック、差分テスト | 収束テスト、パラメータスタディ |
| DLでの例 | grad check、形状チェック | アブレーションスタディ、ベンチマーク |
| UXでの例 | スモークテスト、a11yチェック | A/Bテスト、ユーザーリサーチ |

「テストオラクルがない」とされる問題の多くは、pass/failに落とせない品質評価をテストの枠組みで扱おうとして生じています。オラクルがないのではなく、**テストという形式が合っていない**のです。各分野はテストとは呼ばない形で品質保証の方法論を確立しています。

## 2レベルの検査

数値計算には2レベルの検査が必要で、大雑把には機能要件と非機能要件に対応します。

### レベル1: 機能要件——仕様通りの実装か

「この実装は設計通りに動いているか」を検証します。pass/failで判定可能であり、テストの射程内です。

典型的な実装では不変条件は古くから知られているか、仕様から明らかなことが多いです。SVDなら:

- 再構成: $\|A - U\Sigma V^*\| < \varepsilon$
- 直交性: $\|U^\top U - I\| < \varepsilon$
- 特異値の非負性・降順

$U, V$ そのものは縮退で一意でないので比較してはいけませんが、テスト自体は書けます。不変量を「発見」する必要はなく、**定式化から読み取って書くだけ**です。テストオラクル問題は存在しません。

単体テストレベルではこれで十分であり、「テストオラクルがない」と感じるのは**不変量を書くボキャブラリーが不足している**だけのことが多いです。

### レベル2: 非機能要件——アルゴリズムの品質は十分か

「この近似解は十分良いか」「このアルゴリズムは精度改善をしているか」を評価します。これはテストの枠組みを超えており、**品質保証・実験的検証の領域**です。

- 数値計算: 収束テスト（メッシュを細かくしたら収束次数が出るか）、パラメータスタディ
- DL: アブレーションスタディ、学習曲線の監視、ベンチマークデータセットでの評価
- UX: ユーザーリサーチ、A/Bテスト

これらをテストフレームワークに乗せようとするのは危ういです。pass/failに落とした瞬間に連続的な品質情報が潰れます。テストオラクル問題が「ある」のではなく、**テストという枠組みが不適切**です。

### 中間レベル: 合成による不変性の曖昧化

単体レベルの不変量は仕様から明らかです。品質評価はテストの射程外です。問題は**中間レベル**——コンポーネントを合成した結果、不変条件が非自明になるケースです。

ただし正直なところ、問題設定レベルの不変性は合成しても残るはずです（エネルギー保存則は系を合成しても消えません）。中間レベルの「非自明さ」は不変性の不在ではなく、**合成による不変性の追跡の困難さ**であることが多いです。

この領域で実践的に有効なのは以下の手法です:

- **メタモルフィックテスト**: 入力変換に対する出力の関係を検証します。正解値は不要で、関係性がオラクルになります
- **差分テスト**: 参照実装との比較です。正解値は不要で、一致がオラクルになります
- **感度分析**: 入力を摂動して出力の変化を観測します。爆発的な応答はバグか不良設定かを示唆します

これらは「正解はわからないが、少なくともこういう性質は満たすはず」という**外堀を埋める**手法です。外堀を十分に埋めた上で、本丸（品質評価）はドメイン知識に基づく判断に委ねます。実務的にはこの「外堀を埋めてお祈り」が現実的な折衷です。

## テストオラクル問題は「テスト対象の曖昧さ」に帰着する

同じコードでも、テスト対象の定義によってオラクルの有無が変わります。

例: モンテカルロ法（メトロポリス法）

| テスト対象 | レベル | オラクルはあるか | 根拠 |
|---|---|---|---|
| メトロポリス法の実装 | 機能要件 | ある | 2Dイジング模型の厳密解との一致 |
| 乱数生成器 | 機能要件 | ある | 統計的検定 |
| 3Dイジングの相転移温度 | 品質評価 | ない | 厳密解が存在しない |

「メトロポリス法が正しく実装されているか」と「3Dイジングの相転移温度はいくつか」は全く違う問いで、前者はテスト、後者は実験です。テストオラクル問題が現れるのは後者ですが、それはテストの問題ではなく**未解決の科学の問題**です。

## 不良設定問題: テスト手法の共通の盲点

テスト手法は全て**well-conditionedを暗黙に仮定しています**。

| 手法 | 暗黙の前提 |
|---|---|
| Backward error | 条件数が適度 → forward errorも小さい |
| メタモルフィックテスト | 変換後も問題がwell-conditioned |
| 差分テスト | 両実装ともwell-conditionedな領域で比較 |

ill-conditionedな入力に対しては、どの手法を使っても偽陽性（completeness違反）が生じえます。

### backward errorの限界

backward errorは「アルゴリズムの質」を測りますが、「答えの質」は測りません。

$$
\text{forward error} \leq \text{condition number} \times \text{backward error}
$$

- backward errorが小さい = アルゴリズムは安定して動いた
- しかし条件数が大きければ、forward errorは大きい（答えは正解から遠い）
- 不安定固定点のアナロジー: 「近くの固定点の厳密解です」と言われても、微小摂動で軌道が発散するなら意味がありません

backward error testingは**暗黙にwell-conditionednessを仮定しています**。

### 数値計算における「失敗」の3分類

数値計算では「期待値との差 $\neq$ 失敗」です。近似計算が本質なので、通常のソフトウェアとは失敗の定義が異なります。

1. **数学的失敗（problem ill-conditioning）**: 問題自体が悪く、小さな摂動で解が大きく変わります。アルゴリズムの問題ではありません
   - 例: ユニタリ行列のSVD（全特異値=1で完全縮退、特異ベクトルが一意でない）、重複固有値、ほぼ特異な行列
   - 正しい挙動: condition numberの報告、warning、エラー返却
2. **アルゴリズム失敗（algorithm failure）**: 問題は普通ですがアルゴリズムが壊れます。収束しない、NaN、明らかに大きな誤差
3. **API契約違反（software failure）**: 通常のソフトウェアバグです。エラーコードが出ない、NaNをsilently返す等

テストで捕捉すべきは2と3のみです。1はテスト入力の問題です。

### LAPACKの設計に学ぶ

LAPACKはill-conditioningの扱いで2段階の設計を持っています:

| ドライバー | 判定 | コスト |
|---|---|---|
| 簡易（`dgesv`等） | ゼロピボット = exactly singular | ほぼゼロ（LU分解の副産物） |
| エキスパート（`dgesvx`等） | RCOND推定 = computationally singular | $O(n^2)$ 追加 |

エキスパートドライバーは**ill-conditionedでも解を返しつつ、条件数をAPIで報告**します。判断は呼び出し側に委ねる設計です。テスト側で「条件数がこの閾値以上ならtoleranceを緩める or スキップ」が可能になります。

不良設定をどうエージェントに教えるかは[別記事](./ill-conditioning-harness-engineering)で扱います。

## 解法のボキャブラリー

「テストオラクルがない」で思考停止しないための道具立てを整理します。これらは主にレベル1（機能要件）と中間レベルの外堀を埋めるものです。

| 手法 | 何を提供しているか | レベル |
|---|---|---|
| 不変量テスト | 仕様から導かれる性質の検証 | レベル1 |
| メタモルフィックテスト | 入力変換に対する出力の関係 | 中間 |
| 差分テスト | 参照実装との比較 | 中間 |
| backward error | 近傍問題の厳密解か | レベル1 |
| 統計的テスト | 分布的性質 | レベル1 |
| 感度分析 | 摂動に対する出力の変化 | 中間 |
| 既知特殊ケース | 解析解が存在する部分問題 | レベル1 |

これらの解法が解決しているのは「正解がない」問題ではなく、**「exact outputとの一致比較しかテスト手法を知らない」**状態です。オラクルの形を変えれば大抵解決します。

### メタモルフィックテストと感度分析

中間レベルで最も実践的なのはメタモルフィックテストと感度分析です。入力を変換・摂動して出力の変化を観測する手法で、正解値を必要としません。

- スケーリング: $f(cA)$ と $cf(A)$ の関係
- 対称性: $f(\text{Perm}(x))$ と $\text{Perm}(f(x))$ の関係
- 摂動応答: 入力を微小に動かしたときの出力変化が妥当か

これらは**テストではなく解析に近い**ものです。pass/failに落とせる部分だけをテストにし、残りは実験的検証として扱うのが健全です。

## まとめ

「テストオラクル問題」の正体は3つに仕分けできます:

1. **外堀を書いていないだけ**: 不変量・メタモルフィック関係・差分テスト等のボキャブラリーを使えば、機能要件レベルのテストは書けます。不変量は仕様から明らかなことが多く、自動発見は通常不要です
2. **テストと実験を混同している**: 「この近似は十分良いか」はテストではなく品質保証・実験的検証の問題です。テストフレームワークに乗せようとするのが不適切です。数値計算なら収束テストやパラメータスタディ、DLならアブレーションスタディ等、各分野の実験的検証手法を使うべきです
3. **本当にオラクルがない**: テスト対象が未解決の科学の問題（例: 3Dイジングの厳密解）です。これはテストの問題ではありません

「テストオラクル問題」と呼ばれているものの大部分は1と2であり、テスト手法の問題ではなく**フレーミングの問題**です。外堀を書き、テストと実験を区別し、本当に未解決な部分を正直に認識すること——これが実践的な数値計算テストの考え方です。

## 参考リンク集

### テストオラクル問題 一般

- [The Oracle Problem in Software Testing: A Survey - IEEE TSE 2015](https://ieeexplore.ieee.org/document/6963470/) ([PDF](https://eecs481.org/readings/testoracles.pdf))
  - Barr, Harman, McMinn, Shahbaz, Yoo. テストオラクル問題の包括的サーベイ（694論文を分析）。テストオラクルを4分類: Specified（317）、Derived（245）、Implicit（76）、No oracle（56）。オラクルを $D: T_A \to \text{Bool}$ の部分関数として形式化し、soundness/completenessを定義
- [「正解が分からない」アルゴリズムをどうテストするか - Zenn](https://zenn.dev/hacobell_dev/articles/48672302988d40)
- [テストオラクルとは何か - kzsuzuki](https://www.kzsuzuki.com/entry/2021/04/12/083000)
- [テストオラクルとは？ - Apidog](https://apidog.com/jp/blog/test-oracle-jp/)

### メタモルフィックテスト

- [Metamorphic Testing: A Review of Challenges and Opportunities - ACM Computing Surveys](https://dl.acm.org/doi/10.1145/3143561)
- [Discovering Metamorphic Relations for Scientific Software - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8129917/)
- [Hierarchical Metamorphic Relations for Testing Scientific Software (PDF)](https://homepages.uc.edu/~niunn/papers/SE4Science18.pdf)
- [Metamorphic Testing - Wikipedia](https://en.wikipedia.org/wiki/Metamorphic_testing)
- [機械学習システムのためのメタモルフィックテスティング入門 - Qiita](https://qiita.com/tokumoto/items/cd3d17cae3b099badaf6)
- [メタモルフィックテスティングとは何か - kzsuzuki](https://www.kzsuzuki.com/entry/MetamorphicTesting)
- [メタモルフィックテスティングの2次元物理エンジンへの適用 (PDF)](https://www.ieice.org/publications/conference-FIT-DVDs/FIT2021/data/pdf/C-013.pdf)
- [日立 メタモルフィックテスティング資料 (PDF)](https://www.jasst.jp/symposium/jasst19hokkaido/pdf/S3-1-2.pdf)

### 数値計算のサンプリング・ファジング

- [Efficient Generation of Error-Inducing Floating-Point Inputs (ICSE 2020, PDF)](https://web.cs.ucdavis.edu/~rubio/includes/icse20.pdf)
- [Detecting Floating-Point Errors via Atomic Conditions (POPL 2020, PDF)](https://people.inf.ethz.ch/suz/publications/popl20.pdf)
- [NUMFUZZ: Floating-Point Format Aware Fuzzer (PDF)](https://lqchen.github.io/files/APSEC22_NFuzz.pdf)
- [Fuzzing Floating Point Code - Erik Rigtorp](https://rigtorp.se/fuzzing-floating-point-code/)
- [Just fuzz it: coverage-guided fuzzing for FP constraints (ESEC/FSE 2019)](https://dl.acm.org/doi/10.1145/3338906.3338921)
- [Herbie: Automatically Improving Accuracy for FP Expressions (PLDI 2015, PDF)](https://herbie.uwplse.org/pldi15-paper.pdf)

### 数値計算のテスト一般

- [Microsoft Cloud Numerics の数学関数をテストする - Microsoft Docs](https://learn.microsoft.com/ja-jp/archive/msdn-magazine/2012/october/numerics-testing-math-functions-in-microsoft-cloud-numerics)
- [Unit Testing Numerical Routines - Hacker News](https://news.ycombinator.com/item?id=42115161)
