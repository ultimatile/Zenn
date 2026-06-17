---
title: "MPO-MPS積を計算する密度行列法"
emoji: "🧮"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["tensornetwork", "matrixproductstate","tensortrain"]
published: false
---

## はじめに

本記事は[MPO-MPS積の圧縮：3手法の比較と選び方](https://zenn.dev/ultimatile/articles/tn-mpo-mps-comparison)の続きで、記号と問題設定——ターゲット $\ket{\varphi} = \hat{W}\ket{\psi}$（ボンド次元 $D_\text{MPS} D_\text{MPO}$）をボンド次元 $D'_\text{MPS}$ のMPSに圧縮する問題——はそちらを前提とします。

ここでは3手法のうち**密度行列法 (density-matrix method)** の中身を解説します。
ターゲット $\ket{\varphi}$ の縮約密度行列を各カットで直接組んで対角化し、支配的固有ベクトルを新MPSテンソルにする、という手法です。
3手法のなかでの位置づけ（精度は ジップアップ法 < 密度行列法 < 変分フィッティング法 の中間、ただしMPOボンドが2乗で効くのが弱点）は入口記事にまとめてあります。

### この手法のリファレンスについて

最初に断っておくと、**密度行列法には専用の原論文がありません**。
ジップアップ法はStoudenmire–White [^stoudenmire2010]、変分フィッティング法はVerstraete–Cirac [^verstraete2004] という出典がありますが、密度行列法はそうした「名前のついた論文」を持ちません。
実体は、**WhiteのDMRGにおける密度行列切り捨て** [^white] を、ターゲット状態$\hat{W}\ket{\psi}$に対して適用しただけのものです。
実務上のリファレンスは、ITensorの実装と、tensornetwork.orgの解説ページ [^tnorg] になります（後者は「Glen Evenbly・Steven R. White・Ian McCullochとの議論から生まれた」と謝辞に記すのみで、論文citationはありません）。

レビュー類での扱いも示唆的です。
Schollwöckのレビュー [^schollwock2011] は「密度行列の対角化とSVD切り捨ては同じ最適基底を与える（act identically）」と整理しており、Paeckelらのレビュー [^paeckel2019] のMPO適用節は **direct / variational / zip-up** の3つだけを挙げ、密度行列法を独立の手法としては立てていません（SVD切り捨てに吸収して扱っている、という整理です）。

[^white]: S. R. White, *Phys. Rev. Lett.* **69**, 2863 (1992); S. R. White, *Phys. Rev. B* **48**, 10345 (1993). 簡約密度行列の支配的固有ベクトルを残す、というDMRGの切り捨ての原典です。

[^tnorg]: <https://tensornetwork.org/mps/algorithms/denmat_mpo_mps/>。本手法の事実上の一次資料。MPO-MPS積とその共役の partial trace として密度行列を組む構成が図解されています。

[^schollwock2011]: U. Schollwöck, *The density-matrix renormalization group in the age of matrix product states*, *Ann. Phys.* **326**, 96 (2011), [arXiv:1008.3477](https://arxiv.org/abs/1008.3477). 「SVDと密度行列対角化の等価性」と圧縮の誤差評価（第4節）。

[^stoudenmire2010]: E. M. Stoudenmire and S. R. White, *Minimally Entangled Typical Thermal State Algorithms*, *New J. Phys.* **12**, 055026 (2010), [arXiv:1002.1305](https://arxiv.org/abs/1002.1305). ジップアップ法の原典。MPO-MPS積の手法として変分フィッティング法（Verstraete–Cirac由来）とジップアップ法を論じています。

[^verstraete2004]: 変分フィッティング法（$\ket{\varphi}$を$\hat W\ket{\psi}$にフィットして$\| \ket{\varphi} - \hat W\ket{\psi}\|^2$を最小化する手法）は、Stoudenmire–White [^stoudenmire2010] が F. Verstraete・J. I. Cirac らの2004年の仕事（単一サイト版）に帰しています。正確な書誌は同論文の該当引用を参照してください。

[^paeckel2019]: S. Paeckel, T. Köhler, A. Swoboda, S. R. Manmana, U. Schollwöck, C. Hubig, *Time-evolution methods for matrix-product states*, *Ann. Phys.* **411**, 167998 (2019), [arXiv:1901.05824](https://arxiv.org/abs/1901.05824). MPO適用節はdirect/variational/zip-upの3手法を比較しています。

## 準備：記号と最適切り捨て

記号は入口記事に従います。
本記事で特に要なのは、ターゲット $\ket{\varphi} = \hat{W}\ket{\psi}$ のサイトテンソル

$$
B^{[s]}_{(l, b), \sigma_s', (r, b')} = \sum_{\sigma_s} W^{[s]}_{b, \sigma_s', \sigma_s, b'} A^{[s]}_{l, \sigma_s, r}
$$

（ボンド次元 $D_\text{MPS} D_\text{MPO}$）と、圧縮の「正解」を与える**簡約密度行列**です。
入口記事の「最適切り捨ての基礎」のとおり、状態をあるカットで左右に分けたとき、左ブロックの簡約密度行列 $\rho = \mathrm{Tr}_\text{右}\ket{\varphi}\bra{\varphi}$ の支配的な $D'_\text{MPS}$ 個の固有ベクトルが、そのカットでの2-ノルム最適な切り捨て基底を与えます。
誤差は捨てた固有値の和で $\| \ket{\varphi} - \ket{\tilde{\varphi}} \|^2 \le 2 \sum_{i} \epsilon_i$ と抑えられます[^schollwock2011]。

密度行列法は、この「$\rho$ の支配的固有ベクトルを残す」操作を、$\ket{\varphi} = \hat{W}\ket{\psi}$ を陽に組み立てることなく実行します。

## アイデア：$\hat{W}\ket{\psi}$の縮約密度行列を直接対角化する

発想は単純です。
各カットで$\ket{\varphi}$の簡約密度行列$\rho$を、MPOとMPSの縮約から**直接**組み、対角化して支配的固有ベクトルを取る。
これを掃引で繰り返せば、新MPSが出来上がります。

ポイントは、$\rho$が$\ket{\varphi}\bra{\varphi}$の形なので、**$\hat{W}$がbra側とket側の両方に現れる**ことです。
tensornetwork.orgの言葉では「MPO-MPS積とそのエルミート共役の partial trace」[^tnorg]。
このため$\rho$を組む縮約には、ketのMPOボンド$b'$とbraのMPOボンド$\tilde{b}'$が独立に現れ、**MPOボンドが2乗で効きます**。これが計算量の弱点の根です（後述）。

逆に、$\rho$は$\ket{\varphi}$**そのものの**性質（ゲージに依らない）なので、ジップアップ法と違って**入力MPSを特定の標準形に揃える必要がありません**。各カットで厳密な$\rho$を組んで対角化する以上、得られる切り捨てはそのカットで厳密に最適です。

## アルゴリズム詳細

左→右の掃引で、左標準形の新MPS $M^{[1]}, \ldots, M^{[L]}$を組む版で書きます（tensornetwork.orgは左から overlap 環境を貯めて右→左に対角化する鏡像版ですが、左右を反転しただけで同値です）。

### 右環境の用意

カット$s$での左ブロック密度行列を組むには、右ブロック$[s+1, \ldots, L]$をトレースした**右環境** $G^{[s]}$が要ります。
$G^{[s]}$は、$\ket{\varphi}$の右ブロックをbra・ketで縮約し、物理脚をトレースした4脚テンソル

$$
G^{[s]}_{(r, b'), (\tilde{r}, \tilde{b}')}
= \sum_{\text{右ブロック}}
B^{[s+1\cdots L]}_{(r,b'),\ldots} \,
\bigl(B^{[s+1\cdots L]}_{(\tilde{r},\tilde{b}'),\ldots}\bigr)^{*}
$$

で、ket側の複合ボンド$(r, b')$とbra側の$(\tilde{r}, \tilde{b}')$を持ちます。
サイズは$(D_\text{MPS} D_\text{MPO})^2$。
右端から一つずつ、$G^{[s+1]}$に$A^{[s+1]}, W^{[s+1]}$とその複素共役を縮約して$G^{[s]}$を作る漸化式で、掃引前に用意します。
$\hat{W}$がbra・ket双方に乗るため、ここに$b'$と$\tilde{b}'$が独立に現れ、$D_\text{MPO}^2$が立ちます。

### サイト$s = 1, \ldots, L$のループ

**Step 1（局所テンソルの用意）**: 確定済みの左標準形$M^{[1\cdots s-1]}$で、切り詰めた左基底$m_{s-1}$（次元$\le D'_\text{MPS}$）に移したサイト$s$の局所テンソルを作ります。

$$
\Phi^{[s]}_{m_{s-1}, \sigma_s', (r, b')}
=
\sum_{l, b, \sigma_s}
(P_{s-1})_{m_{s-1}, (l, b)}
\, W^{[s]}_{b, \sigma_s', \sigma_s, b'}
\, A^{[s]}_{l, \sigma_s, r}
$$

ここで$P_{s-1}$は、$M^{[1\cdots s-1]}$から決まる「太い左ボンド$(l,b)$から切り詰めた$m_{s-1}$への射影」です（$s=1$では自明）。

**Step 2（密度行列の構成）**: $\Phi^{[s]}$、右環境$G^{[s]}$、$\Phi^{[s]*}$を縮約して、$(m_{s-1}, \sigma_s')$空間（次元$\le D'_\text{MPS} d$）の簡約密度行列を組みます。

$$
\rho^{[s]}_{(m_{s-1}\sigma_s'),\,(\tilde{m}_{s-1}\tilde{\sigma}_s')}
=
\sum_{(r,b'), (\tilde{r},\tilde{b}')}
\Phi^{[s]}_{m_{s-1},\sigma_s',(r,b')}
\,
G^{[s]}_{(r,b'),(\tilde{r},\tilde{b}')}
\,
\bigl(\Phi^{[s]}_{\tilde{m}_{s-1},\tilde{\sigma}_s',(\tilde{r},\tilde{b}')}\bigr)^{*}
$$

図にすると、$\Phi^{[s]}$（ket）と$\Phi^{[s]*}$（bra）を右環境$G^{[s]}$で繋いだ「蝶ネクタイ」型で、開いた4脚が$\rho^{[s]}$の2つの複合インデックスになります。

![reduced density matrix of W|psi> built from Phi and the right environment](/images/tn-mpo-density-matrix/dm-construct.png)

**Step 3（対角化と切り捨て）**: $\rho^{[s]}$はエルミートなので、固有値分解

$$
\rho^{[s]} = U^{[s]} \Lambda^{[s]} U^{[s]\dagger}
$$

し、固有値$\Lambda^{[s]}$の大きい順に$D'_\text{MPS}$個まで（または閾値で）残します。
残した固有ベクトル$U^{[s]}$が、そのまま新サイトテンソルです。

$$
M^{[s]}_{m_{s-1}, \sigma_s', m_s} = U^{[s]}_{(m_{s-1}\sigma_s'), m_s}.
$$

![diagonalize rho and keep the dominant eigenvectors as the new site tensor](/images/tn-mpo-density-matrix/dm-eig.png)

$U^{[s]}$は固有ベクトルなので自動的に直交し、$M^{[s]}$は**左標準形**になります。

**Step 4（前進）**: $M^{[s]}$で射影$P_s$を更新し、次のサイト$s+1$へ進みます。
右環境$G^{[s]}$は前処理で用意済みのものを使います。

掃引が右端に達した時点で、左標準形の新MPS $M^{[1]} \cdots M^{[L]}$が出来上がります。後処理は不要です。

## 密度行列の対角化とSVDの関係

ここは出自を整理する節です。
よくある誤解を避けるため、密度行列の対角化とSVDの関係を正確に述べます。

二分割した係数行列を$\Psi_{(A),(B)}$とすると、SVDは$\Psi = U S V^\dagger$（$S$が特異値）、左ブロックの簡約密度行列は

$$
\rho_A = \mathrm{Tr}_B \ket{\psi}\bra{\psi} = \Psi \Psi^\dagger = U S^2 U^\dagger
$$

です。
つまり**$\rho_A$の固有ベクトルは$\Psi$の左特異ベクトル$U$、固有値は特異値の二乗$s_a^2$**。
$\Psi$をSVDすると、その左特異ベクトル$U$が$\rho_A = \Psi\Psi^\dagger$を対角化している（同時に右特異ベクトル$V$が$\rho_B = \Psi^\dagger\Psi$を対角化する）、という関係です。
だから「上位$D'_\text{MPS}$個の特異値を残す」と「$\rho$の上位$D'_\text{MPS}$個の固有値を残す」は、**同じ最適基底・同じ切り捨て**を与えます（Schollwöckのレビューが "act identically" と述べるのはこの意味です [^schollwock2011]）。

ただし両者は「同じもの」ではなく、**同じ切り捨てを与える別々の2操作**です。違いは次の通り。

- **対象が違う**: 一方は$\Psi$、もう一方は$\rho = \Psi\Psi^\dagger$。
- **数値特性が違う**: $\rho$を作ると固有値が$s^2$になりダイナミックレンジが二乗になるので、小さい特異値の分解能はむしろ$\Psi$を直接SVDする方が良い。$\rho$経由が精度で勝るわけではない。
- **$\rho$経由でしかできないことがある**: 後述するように、複数の寄与を一つの$\rho$に足し込んでから対角化できる（単一の$\Psi$が存在しない場合に効く）。

だからこそ、密度行列法は「独立した手法の論文」を持たないわけです。
得られる切り捨て自体は$\ket{\varphi} = \hat{W}\ket{\psi}$に対する最適なSVD切り捨てと同じで、それを「$\Psi$を直接SVDするのではなく、$\rho$を組んで対角化する」経路で実行しているだけ。
この経路を取る積極的な理由は、次節以降の「厳密な右環境を組み込める」「複数項を合算できる」点にあります。

ではジップアップ法と何が違うのか。

- **ジップアップ法**は局所テンソル$C^{[s]}$（持ち越し$R_{s-1}$と$A^{[s]}, W^{[s]}$の縮約）をSVDします。右側の厳密な環境は入っておらず、入力の右標準形性を前提にした**局所近似**です。
- **密度行列法**は右環境$G^{[s]}$（右ブロックの厳密なGram）を組み込んだ$\rho^{[s]}$を対角化します。つまり**そのカットでの$\ket{\varphi}$の厳密な簡約密度行列**を対角化するので、切り捨てがそのカットで厳密に最適です。

変分フィッティング法との違いは、**一回の掃引で済む**点（反復も初期値も不要）です。

## 計算量

密度行列法の重い部分は、右環境$G^{[s]}$の構成と、$\rho^{[s]}$を組む縮約です。

$G^{[s]}$は$(r, b', \tilde{r}, \tilde{b}')$の4脚で、サイズ$D_\text{MPS}^2 D_\text{MPO}^2$。
これを右端から漸化式で更新するコストが、各サイトで支配的になります。
$\hat{W}$がbra・ket双方に乗るので**$D_\text{MPO}^2$が立つ**。これは本質的な特徴で、ジップアップ法（$D_\text{MPO}$が主、$D_\text{MPO}^2$は副次項）や変分フィッティング法に対する明確な弱点です。
最適な縮約順序は$D_\text{MPS}$と$D_\text{MPO}$の大小に依存します [^tnorg]。

なお、tensornetwork.orgや上記レビューは密度行列法の閉じたコスト式を与えていないため、ここで$O(\cdots)$の確定値は主張しません。
定性的に確実なのは「右環境とその更新に$D_\text{MPS}^2 D_\text{MPO}^2$規模のテンソルが現れ、メモリ・計算量ともにMPOボンドが2乗で効く」という点で、これが「速さで選ぶ手法ではない」理由です。

## 精度

- **各カットで右環境込みの最適**: 厳密な右環境を含む$\rho$を対角化するので、各カットの切り捨ては「すでに確定した左を所与として」2-ノルム最適。右環境を入れない局所近似のジップアップ法より精度が高い。
- **大域的には準最適**: ただし一回の掃引で左を確定したら再最適化しないので、全ボンドを同時最適化する（収束した）変分フィッティング法には及ばない。誤差は$2\sum_i \epsilon_i$で抑えられる準最適圧縮になる。精度順序は ジップアップ法 < 密度行列法 < 収束した変分フィッティング法。
- **初期値・反復が不要**: 変分フィッティング法と違い一発で高品質な結果が出る。逆に、密度行列法の出力を変分フィッティング法の初期値にする、という併用も自然。
- **標準形の前提が不要**: ジップアップ法と違い、入力MPSを右標準形に揃える前処理が原理的に要らない（厳密な$\rho$を組むため）。

## 実装上の注意点

### 数値精度の注意（$\rho$は二乗が効く）

前述のとおり$\rho = \Psi\Psi^\dagger$を作ると固有値が特異値の二乗$s^2$になり、ダイナミックレンジが二乗に広がります。
このため、**ごく小さい特異値の分解能は$\Psi$を直接SVDする方が良く、$\rho$経由は精度面でむしろ不利**です。
高精度に小さい特異値まで追いたい場面では、この点を意識しておく必要があります。
密度行列法を使う積極的な理由は数値精度ではなく、次の「厳密な右環境を組み込める」「複数項を合算できる」という構造的な利点にあります（DMRGが伝統的に密度行列解析を使ってきたのも、ハミルトニアンや複数状態を同じ基底に押し込めるこの合算のしやすさが大きい）。

### 複数項を一つの$\rho$にまとめられる

密度行列法の地味だが本質的な強みは、**複数の寄与を一つの密度行列に足し込める**ことです。
たとえば$\hat{W} = \sum_k \hat{W}_k$のようなMPOの和や、複数状態のターゲティングを、

$$
\rho = \sum_k \mathrm{Tr}_\text{右}\, \hat{W}_k\ket{\psi}\bra{\psi}\hat{W}_k^\dagger
$$

のように一つの$\rho$へ合算してから対角化すれば、和を取った状態に対して一括で最適な基底が得られます。
これはWhiteの多状態ターゲティングや密度行列摂動と同じ系譜の発想です。

### 対称性付きMPSとの相性

対称性を組み込んだMPS（[Abelian対称性テンソルの記事](https://zenn.dev/ultimatile/articles/intro-abelian-symmetric-tensor)）では、$\rho^{[s]}$がチャージごとにブロック対角化され、固有値分解を各チャージブロックで独立に走らせれば軽くなります。

### いつ密度行列法を選ぶか

$D_\text{MPO}^2$のコストがあるため、単純な「速いMPO-MPS積」が欲しいだけならジップアップ法が有利です。
密度行列法が効くのは、**精度を一発で取りに行きたい**とき、**標準形の前処理を避けたい**とき、あるいは**複数項を一括圧縮したい**ときです。

## まとめ

整理しなおすと：

1. **問題**: $\hat{W}\ket{\psi}$をボンド次元$D'_\text{MPS}$のMPSで最良近似したい（ジップアップ法・変分フィッティング法と同じ問題）。
2. **アイデア**: $\ket{\varphi} = \hat{W}\ket{\psi}$の簡約密度行列$\rho$を各カットで直接組み、支配的固有ベクトルを新MPSテンソルにする。$\hat{W}$がbra・ket両方に出る。
3. **アルゴリズム**: 右環境$G^{[s]}$を用意し、$\rho^{[s]} = \Phi^{[s]} G^{[s]} \Phi^{[s]\dagger}$を対角化、上位$D'_\text{MPS}$固有ベクトル$=M^{[s]}$。
4. **出自**: 専用論文は無い。WhiteのDMRG密度行列切り捨てを$\hat{W}\ket{\psi}$に適用したもので、密度行列対角化はSVD切り捨てと等価。実務リファレンスはITensorとtensornetwork.org。
5. **計算量**: MPOボンドが2乗で効く（右環境$\sim D_\text{MPS}^2 D_\text{MPO}^2$）。速さでは選ばない。
6. **精度**: **ジップアップ法 < 密度行列法 <（収束した）変分フィッティング法** の中間。各カットを厳密な右環境込みで切るためジップアップ法より上、一掃引の貪欲法で再最適化しないため収束した変分フィッティング法には及ばない。初期値・反復・標準形の前処理は不要。

密度行列法は、「速さより精度・頑健性・一括圧縮」を取りたいときの選択肢です。
[ジップアップ法](https://zenn.dev/ultimatile/articles/tn-mps-zipup)（速い／局所近似）と[変分フィッティング法](https://zenn.dev/ultimatile/articles/tn-mpo-variational-fitting)（反復で大域最適に迫る）と合わせ、要求と計算資源で使い分けます。3手法の比較は[入口記事](https://zenn.dev/ultimatile/articles/tn-mpo-mps-comparison)を参照してください。
