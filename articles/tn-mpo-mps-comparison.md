---
title: "MPO-MPS積の圧縮：3手法の比較と選び方"
emoji: "🧭"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["tensornetwork", "matrixproductstate","tensortrain"]
published: false
---

## はじめに

行列積状態(MPS)に行列積演算子(MPO)を作用させる操作——**MPO-MPS積(MMP)**——は、テンソルネットワーク計算の至るところに現れます。
時間発展でも、虚時間冷却でも、演算子の期待値でも、「MPOをMPSに掛けて、増えたボンド次元を圧縮する」という操作が繰り返し走ります。

この圧縮には主要な手法が3つあります。

- **zip-upアルゴリズム**
- **密度行列法 (density-matrix method)**
- **variational fitting**

本記事は**この3手法を選ぶための入口（エントリポイント）**です。
アルゴリズムの実装詳細には踏み込まず、**共通の記号と問題意識を導入し、「環境精度」と「反復」という2軸で3手法を整理**します。
読み終えたとき、**「自分の用途ではどれを使うべきか」を実装の中身を知らなくても判断できる**ことを目標にします。
各手法のアルゴリズムの中身（縮約・SVD・図解）は、以降の個別記事で順次解説します。

なお本記事の記号と問題設定は、以降の3記事すべての共通の前提です。

## 問題設定：ボンド次元の指数爆発

長さ$L$の一次元格子、サイトの物理次元を$d$とします。

MPS $\ket{\psi}$とMPO $\hat{W}$を

$$
\ket{\psi} = \sum_{\{\sigma\}} A^{[1]}_{\sigma_1} \cdots A^{[L]}_{\sigma_L} \ket{\sigma_1 \cdots \sigma_L},
\qquad
\hat{W} = \sum_{\{\sigma, \sigma'\}} W^{[1]}_{\sigma_1' \sigma_1} \cdots W^{[L]}_{\sigma_L' \sigma_L} \ket{\sigma'_1 \cdots}\bra{\sigma_1 \cdots}
$$

と書きます。

問題は、MMP $\hat{W}\ket{\psi}$を素直に計算すると**ボンド次元が掛け算で増える**ことです。
MPSのボンド次元を$D_\text{MPS}$、MPOのボンド次元を$D_\text{MPO}$とすると、サイトごとのテンソルは

$$
B^{[s]}_{(l, b), \sigma_s', (r, b')} = \sum_{\sigma_s} W^{[s]}_{b, \sigma_s', \sigma_s, b'} A^{[s]}_{l, \sigma_s, r}
$$

となり、ボンドが$(l,b)$・$(r,b')$という複合インデックスに膨らんで、ボンド次元が$D_\text{MPS} D_\text{MPO}$になります。
このままMMPを繰り返すと$D_\text{MPS} D_\text{MPO}, D_\text{MPS} D_\text{MPO}^2, \ldots$と**指数的に増加して破綻**します。
したがって、掛けた直後にどこかで「増えたボンド次元を$D'_\text{MPS}$程度に圧縮する」操作が要ります。

**3手法は、この圧縮の異なるやり方**です。
ターゲット状態$\ket{\varphi} = \hat{W}\ket{\psi}$（ボンド次元$D_\text{MPS} D_\text{MPO}$）を、ボンド次元$D'_\text{MPS}$のMPS

$$
\ket{\tilde{\varphi}} = \sum_{\{\sigma'\}} M^{[1]}_{\sigma_1'} \cdots M^{[L]}_{\sigma_L'} \ket{\sigma'_1 \cdots \sigma'_L}
$$

で最良近似したい、というのが共通の問題です。

### 記号の確認

以降の記事も含め、記号は次で固定します。

- $A^{[s]}_{l, \sigma_s, r}$: MPSのサイトテンソル（3脚、$l, r$がボンド、$\sigma_s$が物理脚）、最大ボンド次元$D_\text{MPS}$。
- $W^{[s]}_{b, \sigma_s', \sigma_s, b'}$: MPOのサイトテンソル（4脚、$b, b'$がMPOボンド、$\sigma_s$が入射物理脚、$\sigma_s'$が出射物理脚）、最大ボンド次元$D_\text{MPO}$。
- $\ket{\varphi} = \hat{W}\ket{\psi}$: ターゲット状態。サイトテンソルは$B^{[s]}$、ボンド次元$D_\text{MPS} D_\text{MPO}$。
- $\ket{\tilde{\varphi}}$: 求める圧縮MPS。サイトテンソル$M^{[s]}$、目標ボンド次元$D'_\text{MPS}$。
- **標準形(canonical form)**: 各サイトテンソルを直交化したMPSの表現。左標準形・右標準形・（直交中心を1点に置いた）混合標準形があり、手法によって入力に要求したり出力で得られたりします。

## 最適切り捨ての基礎（共通の土台）

3手法の精度差を語るために、圧縮の「正解」を先に確認します。

状態をあるカットで左ブロックと右ブロックに分けたとき、**左ブロックの簡約密度行列$\rho = \mathrm{Tr}_\text{右}\ket{\varphi}\bra{\varphi}$の支配的な$D'_\text{MPS}$個の固有ベクトル**が、そのカットでボンド次元$D'_\text{MPS}$に切り詰める際の2-ノルム最適な基底を与えます（Schmidt分解 / Eckart–Young）。
これは係数行列のSVDで上位$D'_\text{MPS}$個の特異値を残すのと同じことで、誤差は捨てた特異値の二乗和で評価できます[^schollwock2011]。

ポイントは、各カットの最適切り捨ては**そのカットでの「環境」（残りのネットワーク）に依存する**ことです。
3手法の違いは、煎じ詰めれば**この環境をどれだけ忠実に扱うか**に集約されます。

## 整理の2軸：環境精度 × 反復

各サイトを切り詰めるとき、残りのネットワーク（＝**環境**）の扱い方で2つの軸が立ちます。

- **軸1：環境精度** — 各局所切り捨てで、環境を**近似**するか**厳密**に計算するか。
- **軸2：反復（自己無撞着）** — 環境を**既知の元状態で1回**使うか、**最終的に圧縮された状態**の環境に**自己無撞着**になるまで反復するか。

この2軸で3手法が一列に並びます。

| 手法 | 軸1：環境精度 | 軸2：反復 | PEPSの類推 |
|---|---|---|---|
| **zip-up** | 近似（右側を直交とみなす） | なし（1掃引） | simple update |
| **密度行列法** | 厳密（簡約密度行列を組む） | なし（非対称な1掃引） | full update |
| **variational fitting** | 厳密 | あり（自己無撞着まで反復） | variational（自己無撞着）update |

### なぜ反復が要るのか

軸2の核心は「**大域環境が未知**」という点です。
最適な局所テンソルは、**最終的に切り詰めた他のテンソル**が作る環境に依存します。
ところがその「最終的に切り詰めた残り」は、圧縮を解き終わるまで分からない——答えに依存する環境を使わねばならない、という自己無撞着（鶏卵）問題です。

- **zip-up・密度行列法**は、未知の「最終状態の環境」の代わりに**既知の「元状態$\ket{\varphi}$の環境」**で代用し、一掃引で済ませます。zip-upはその環境をさらに直交近似（simple）、密度行列法は厳密に計算（full）します。
- **variational fitting**は「最終状態の環境」への**自己無撞着**を要求し、往復掃引で環境とテンソルが整合する不動点まで反復します。

## 3手法の比較

アルゴリズムの中身には踏み込まず、性格だけ並べます。

**zip-up**: 左から一回だけ掃引し、局所テンソルをSVDで切り捨てる。各カットは右側を直交とみなす局所近似で、環境を厳密には見ない。3手法で最も**安く**、最も**粗い**[^stoudenmire2010]。

**密度行列法**: ターゲット$\ket{\varphi}=\hat{W}\ket{\psi}$の簡約密度行列を各カットで厳密に組んで対角化し、支配的固有ベクトルを残す。WhiteのDMRGの密度行列切り捨て[^white]を$\hat{W}\ket{\psi}$に当てたもので、専用論文を持たない（実務リファレンスはITensorとtensornetwork.org[^tnorg]）。一掃引で**準最適**だが、$\hat{W}$がbra・ket両方に出るため**MPOボンドが2乗で効き**、メモリ・計算が重い。

**variational fitting**: 距離$\| \ket{\tilde{\varphi}} - \hat{W}\ket{\psi} \|^2$を反復掃引で最小化する[^verstraete2004]。最終圧縮状態の環境に自己無撞着まで反復するので、収束すれば**（局所）変分最適**。初期値（zip-upや密度行列法の出力）と反復回数が要る。

### 精度

$$
\text{zip-up} \;<\; \text{密度行列法} \;<\; \text{（収束した）variational fitting}
$$

- 密度行列法がzip-upに勝つのは、各カットで**厳密な環境**を使うから（軸1）。
- variational fittingが密度行列法に勝るのは、**最終状態の環境に自己無撞着**まで詰めるから（軸2）。一掃引で左を確定したら戻らない密度行列法は、そこで止まる準最適。

つまり密度行列法は「**一掃引で到達できる上限**」、それをさらに反復で磨いたものがvariational fittingです。

### 計算量（定性）

| 手法 | 速さ・コストの性格 |
|---|---|
| **zip-up** | 最も安い。$D_\text{MPO}$が主、$D_\text{MPO}^2$は副次項。1掃引。 |
| **密度行列法** | **$D_\text{MPO}^2$が本質的に効く**（環境$\sim D_\text{MPS}^2 D_\text{MPO}^2$）。メモリも最大。1掃引だが重い。 |
| **variational fitting** | 1掃引はzip-up並みだが、収束まで**反復回数$n_\text{sweep}$倍**かかる。 |

素朴な「全部繋いでから圧縮」に対しては、zip-up・variational fittingが$D_\text{MPO}$について軽くなります。密度行列法は$D_\text{MPO}^2$を払う代わりに各カットを厳密にします。

### 要件と性質

| | 入力の標準形 | 初期値 | 反復 | 備考 |
|---|---|---|---|---|
| **zip-up** | 右標準形が前提 | 不要 | 不要 | 出力は左標準形 |
| **密度行列法** | 原理的に不要 | 不要 | 不要 | 複数項を一つの密度行列に合算できる |
| **variational fitting** | 混合標準形を使う | **要**（良い初期値が重要） | **要** | 大域最適に最も近い |

## 選び方

ユーザー視点での目安です。

- **とにかく速く、精度はそこそこでよい** → **zip-up**。
- **一発で高精度がほしい**。かつ$D_\text{MPO}$が小さめ、標準形の前処理を避けたい、あるいは複数項を一括圧縮したい → **密度行列法**。
- **究極の精度（変分最適）がほしく、反復コストを払える** → **variational fitting**（zip-upや密度行列法の出力を初期値にする）。
- **定番の併用**: まずzip-upか密度行列法で安く初期値を作り、**variational fittingで磨く**。精度がクリティカルな場面（長時間発展、虚時間冷却）で標準的なパターンです。

要するに、**速さなら zip-up、一発の精度なら密度行列法、究極の精度なら variational fitting**。そして3つは排他ではなく、初期値→精密化として**繋いで使う**のが実務の定石です。

## 各手法の実装詳細（以降の記事）

本記事の記号・問題設定を前提に、各手法のアルゴリズムの中身（縮約・SVD・図解）を個別記事で解説します。

- [zip-upアルゴリズム](https://zenn.dev/ultimatile/articles/tn-mps-zipup)
- [密度行列法](https://zenn.dev/ultimatile/articles/tn-mpo-density-matrix)
- [variational fitting](https://zenn.dev/ultimatile/articles/tn-mpo-variational-fitting)

[^schollwock2011]: U. Schollwöck, *The density-matrix renormalization group in the age of matrix product states*, *Ann. Phys.* **326**, 96 (2011), [arXiv:1008.3477](https://arxiv.org/abs/1008.3477). 圧縮（SVD圧縮と変分圧縮）と簡約密度行列の扱いは第4節。

[^stoudenmire2010]: E. M. Stoudenmire and S. R. White, *Minimally Entangled Typical Thermal State Algorithms*, *New J. Phys.* **12**, 055026 (2010), [arXiv:1002.1305](https://arxiv.org/abs/1002.1305). zip-upの原典。fit法（Verstraete–Cirac由来）との対比も論じられています。

[^white]: S. R. White, *Phys. Rev. Lett.* **69**, 2863 (1992); *Phys. Rev. B* **48**, 10345 (1993). 簡約密度行列の支配的固有ベクトルを残すDMRGの切り捨ての原典。

[^tnorg]: <https://tensornetwork.org/mps/algorithms/denmat_mpo_mps/>。密度行列法の事実上の一次資料。

[^verstraete2004]: variational fitting（$\ket{\tilde\varphi}$を$\hat W\ket{\psi}$にフィットする手法）は、Stoudenmire–White [^stoudenmire2010] がF. Verstraete・J. I. Ciracらの2004年の仕事に帰しています。
