---
title: "MPO-MPS積を計算するvariational fittingアルゴリズム"
emoji: "🎯"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["tensornetwork", "matrixproductstate","tensortrain"]
published: false
---

## はじめに

本記事は[MPO-MPS積の圧縮：3手法の比較と選び方](https://zenn.dev/ultimatile/articles/tn-mpo-mps-comparison)の続きで、記号と問題設定——MMP とボンド次元の指数爆発、ターゲット $\ket{\varphi} = \hat{W}\ket{\psi}$ をボンド次元 $D'_\text{MPS}$ のMPS $\ket{\tilde{\varphi}}$ に圧縮する問題——はそちらを前提とします。

ここでは3手法のうち**variational fitting**（変分フィッティング、variational compressionとも）の中身を解説します。
zip-upや密度行列法が「一掃引」で済ませるのに対し、variational fittingは**「誤差最小化MPSを求める」問題そのものを最適化問題として直接解き、収束まで反復掃引する**手法です。
すなわち、ボンド次元 $D'_\text{MPS}$ のMPS $\ket{\tilde{\varphi}}$ を変数とみなし、距離

$$
\| \ket{\tilde{\varphi}} - \hat{W}\ket{\psi} \|^2
$$

を最小化します。
DMRGと同じく「1サイトずつ局所最適化して左右に掃引する」交互最適化(alternating least squares, ALS)で解くのがポイントです。

本記事は標準的なレビュー[^schollwock2011]、tensornetwork.orgの解説[^tnorg]、および各種手法を比較したレビュー[^paeckel2019]を念頭に置いています。

[^schollwock2011]: U. Schollwöck, *The density-matrix renormalization group in the age of matrix product states*, *Ann. Phys.* **326**, 96 (2011), [arXiv:1008.3477](https://arxiv.org/abs/1008.3477). MPSの圧縮（variational compression）は第4.5節に詳しい解説があります。

[^tnorg]: <https://tensornetwork.org/mps/algorithms/denmpo/>。密度行列法と並べて変分法の位置づけが整理されています。

[^paeckel2019]: S. Paeckel, T. Köhler, A. Swoboda, S. R. Manmana, U. Schollwöck, C. Hubig, *Time-evolution methods for matrix-product states*, *Ann. Phys.* **411**, 167998 (2019), [arXiv:1901.05824](https://arxiv.org/abs/1901.05824). variational fitting・zip-up・密度行列法の精度と計算量の比較があります。

## 準備：変数と混合標準形

記号は入口記事に従います（$A^{[s]}_{l, \sigma_s, r}$、$W^{[s]}_{b, \sigma_s', \sigma_s, b'}$、ターゲット $\ket{\varphi} = \hat{W}\ket{\psi}$、ボンド次元 $D_\text{MPS}$・$D_\text{MPO}$）。

最適化の**変数**は、求める圧縮MPS $\ket{\tilde{\varphi}}$ のサイトテンソルです。

$$
\ket{\tilde{\varphi}} = \sum_{\{\sigma'\}} M^{[1]}_{\sigma_1'} \cdots M^{[L]}_{\sigma_L'} \ket{\sigma'_1 \cdots \sigma'_L}
$$

$M^{[s]}_{m_{s-1}, \sigma_s', m_s}$ のボンド次元を $\le D'_\text{MPS}$ に制限し、この $M^{[s]}$ たちを最適化します。

### 混合標準形(mixed-canonical form)

variational fittingでは、サイト$s$に直交中心(orthogonality center)を置いた**混合標準形**を使います。
すなわち、$s$より左のテンソルは左標準形

$$
\sum_{m_{s-1}, \sigma_s'} M^{[s]}_{m_{s-1}, \sigma_s', m_s} (M^{[s]}_{m_{s-1}, \sigma_s', m_s'})^* = \delta_{m_s m_s'}
$$

を、$s$より右のテンソルは右標準形

$$
\sum_{\sigma_s', m_s} M^{[s]}_{m_{s-1}, \sigma_s', m_s} (M^{[s]}_{m_{s-1}', \sigma_s', m_s})^* = \delta_{m_{s-1} m_{s-1}'}
$$

を満たし、中心サイト$s$だけが任意、という形です。
後で見るように、この標準形にしておくと局所最適化問題の係数行列が恒等になり、解が「縮約一発」で求まります。

## 問題設定：距離の最小化

variational fittingが解く問題はこうです。

$$
\ket{\tilde{\varphi}}^\star = \operatorname*{arg\,min}_{\ket{\tilde{\varphi}}\,:\,\text{bond} \le D'_\text{MPS}} \| \ket{\tilde{\varphi}} - \hat{W}\ket{\psi} \|^2
$$

距離を展開すると

$$
\| \ket{\tilde{\varphi}} - \hat{W}\ket{\psi} \|^2
= \braket{\tilde{\varphi} | \tilde{\varphi}} - 2\,\mathrm{Re}\braket{\tilde{\varphi} | \hat{W} | \psi} + \braket{\psi | \hat{W}^\dagger \hat{W} | \psi}
$$

となります。
第3項は$\ket{\tilde{\varphi}}$に依らない定数なので、最小化に効くのは

$$
f(\ket{\tilde{\varphi}}) = \braket{\tilde{\varphi} | \tilde{\varphi}} - 2\,\mathrm{Re}\braket{\tilde{\varphi} | \hat{W} | \psi}
$$

だけです。
ここで重要なのは、$\hat{W}\ket{\psi}$を**陽に組み立てる必要がない**ことです。
$\braket{\tilde{\varphi} | \hat{W} | \psi}$はテンソルネットワークの縮約として直接評価でき、$D_\text{MPS} D_\text{MPO}$の太いボンドを持つMPSを一度も作らずに済みます。
これがzip-upと共通する「太いボンドを丸ごと保持しない」という発想です。

問題は、$f$を$\ket{\tilde{\varphi}}$の全テンソル$\{M^{[s]}\}$について同時に最小化するのが非線形だということです。
全変数を一度に解くのは難しいので、**1サイトだけ動かして残りを固定する**局所問題に分解します。

## アイデア：1サイトずつ解いて掃引する

$f$は、注目サイトのテンソル$M^{[s]}$**だけ**を変数とみなし他を固定すれば、$M^{[s]}$について二次形式になります：

$$
f(M^{[s]}) = (M^{[s]})^\dagger N\, M^{[s]} - 2\,\mathrm{Re}\!\left[(M^{[s]})^\dagger b\right] + \text{const}.
$$

ここで

- $N$は$\braket{\tilde{\varphi}|\tilde{\varphi}}$から$M^{[s]}$とその複素共役を取り除いた**ノルム行列(norm matrix)**、
- $b$は$\braket{\tilde{\varphi} | \hat{W} | \psi}$から$M^{[s]*}$（bra側のサイト$s$）を取り除いた**有効ベクトル**、

です。
$M^{[s]}$をベクトルとみなした二次形式なので、停留条件$\partial f / \partial (M^{[s]})^* = 0$から正規方程式

$$
N\, M^{[s]} = b
$$

が出ます。
これは線形方程式なので、各サイトの局所問題は厳密に解けます。

ここで**混合標準形が効きます**。
直交中心をサイト$s$に置いておくと、左側は左標準形・右側は右標準形なので、$\braket{\tilde{\varphi}|\tilde{\varphi}}$は$M^{[s]}$周りで恒等に潰れ、$N = I$になります。
すると正規方程式は

$$
M^{[s]} = b
$$

と自明化し、$b$を縮約で求めるだけで局所最適解が得られます。
SVDや線形ソルバすら不要で、「環境テンソルと$A^{[s]}, W^{[s]}$を縮約して新しい$M^{[s]}$を作る」という一手に帰着します。

掃引中の状態は次の図のようになります。

![variational fitting mid-sweep state with environments](/images/tn-mpo-variational-fitting/varfit-env.png)

ここで$L_{s-1}$と$R_{s+1}$は、重なり$\braket{\tilde{\varphi} | \hat{W} | \psi}$のテンソルネットワーク（新MPSのbra・MPO・元MPSのketの3段構造）を、サイト$s$より左／右でそれぞれ縮約してまとめた**環境テンソル(environment tensor)**です。
各々が脚を3本持ちます（新MPSボンド・MPOボンド・元MPSボンド）。

局所更新は、$L_{s-1}$、$A^{[s]}$、$W^{[s]}$、$R_{s+1}$を縮約して新しい$M^{[s]}$を作るだけです。

![variational fitting local update: contract environments and local tensors](/images/tn-mpo-variational-fitting/varfit-update.png)

これを左→右→左と何度も掃引し、収束するまで繰り返します。
zip-upが一回掃引で終わるのに対し、こちらは収束するまで複数回掃引する点が決定的な違いです。

## アルゴリズム詳細

具体的に書き下します。

### 初期化

- **新MPS $\ket{\tilde{\varphi}}$の初期値**を用意します。後述するように、ここはzip-upや密度行列法の出力を使うのが定石です。乱数MPSでも動きますが収束が遅く、局所解に落ちやすくなります。
- $\ket{\tilde{\varphi}}$を右標準形に揃え、直交中心を左端（サイト1）に置きます。
- 右環境$R_2, R_3, \ldots, R_L$を右端から順に縮約して用意しておきます。$R_{L+1}$は自明なscalar 1。

右環境の漸化式は

$$
(R_{s+1})_{m_s, b', r}
= \sum_{m_{s+1}, b, r', \sigma_{s+1}, \sigma_{s+1}'}
(M^{[s+1]}_{m_s, \sigma_{s+1}', m_{s+1}})^{*}
\, W^{[s+1]}_{b', \sigma_{s+1}', \sigma_{s+1}, b}
\, A^{[s+1]}_{r, \sigma_{s+1}, r'}
\, (R_{s+2})_{m_{s+1}, b, r'}
$$

です（左環境$L_{s-1}$も左端から同様の漸化式で作れます）。

### 左→右の掃引

サイト$s = 1, \ldots, L$について：

**Step 1（局所解）**: 環境テンソルと局所テンソルを縮約して新しい中心テンソルを作ります。

$$
\tilde{M}^{[s]}_{m_{s-1}, \sigma_s', m_s}
=
\sum_{l, b, b', r, \sigma_s}
(L_{s-1})_{m_{s-1}, b, l}
\, A^{[s]}_{l, \sigma_s, r}
\, W^{[s]}_{b, \sigma_s', \sigma_s, b'}
\, (R_{s+1})_{m_s, b', r}
$$

混合標準形のおかげで、これがそのまま局所最適解$M^{[s]} = \tilde{M}^{[s]}$です。

**Step 2（直交中心の移動）**: 次のサイトに進むため、$\tilde{M}^{[s]}$をQR分解（または特異値で切り捨てたいならSVD）して

$$
\tilde{M}^{[s]}_{(m_{s-1}, \sigma_s'), m_s} = \sum_{m_s'} Q_{(m_{s-1}, \sigma_s'), m_s'} R_{m_s', m_s}
$$

とし、$M^{[s]} \leftarrow Q$（左標準形）として確定、残り$R$は右隣$M^{[s+1]}$に吸収します。
これで直交中心が$s+1$に移ります。

**Step 3（環境の更新）**: 確定した$M^{[s]}$を使って左環境を一つ伸ばし$L_s$を作ります。
$R_{s+1}$は前掃引の値を再利用します。

右端$s=L$まで進んだら、今度は逆向き（右→左、直交中心を左端へ戻す）に同じことをします。
これで1往復(sweep)です。

### 収束判定

掃引のたびに距離（または等価な指標）を測り、変化が閾値を切ったら停止します。
代表的な指標は

$$
\| \ket{\tilde{\varphi}} - \hat{W}\ket{\psi} \|^2
= \braket{\tilde{\varphi}|\tilde{\varphi}} - 2\,\mathrm{Re}\braket{\tilde{\varphi}|\hat{W}|\psi} + \braket{\psi|\hat{W}^\dagger\hat{W}|\psi}
$$

の単調減少です。
第3項は定数なので毎回計算する必要はなく、$\braket{\tilde{\varphi}|\tilde{\varphi}} - 2\,\mathrm{Re}\braket{\tilde{\varphi}|\hat{W}|\psi}$の変化を見れば十分です。
あるいは規格化したフィデリティ$|\braket{\tilde{\varphi}|\hat{W}|\psi}|^2 / (\braket{\tilde{\varphi}|\tilde{\varphi}}\braket{\psi|\hat{W}^\dagger\hat{W}|\psi})$が1に十分近づいたか、で判定する実装もあります。
典型的には数回〜十数回の掃引で収束します。

## なぜ混合標準形にすると線形ソルバが要らないのか

ここがzip-upとの設計思想の違いがもっとも出る部分です。

一般には、局所問題は正規方程式$N M^{[s]} = b$を解く必要があり、$N$は$\braket{\tilde{\varphi}|\tilde{\varphi}}$の「サイト$s$を抜いた環境」、すなわち新MPSの自己重なりから来る正定値行列です。
$N$が一般の行列だと、各サイトで$O((D'_\text{MPS} d)^3)$の線形ソルバ（あるいはCG法）を回すことになります。

しかし直交中心をサイト$s$に置いた混合標準形では、

- $s$より左の$M$は左標準形 → bra-ketを縮約すると恒等に潰れる
- $s$より右の$M$は右標準形 → 同様に恒等に潰れる

ので、$N = I$（恒等）になります。
正規方程式は$M^{[s]} = b$に縮退し、線形ソルバが消えて「$b$を縮約するだけ」になります。
直交中心を掃引に合わせて隣へ動かす（Step 2のQR）コストは$O(D_\text{MPS}^3 d)$と軽く、これで毎サイトの線形ソルバを丸ごと節約できる、という取引です。

この「ゲージを固定して$N=I$にする」テクニックは、DMRGで有効ハミルトニアンの一般化固有値問題を通常の固有値問題に落とすのと全く同じ仕掛けです。
標準形が崩れていると$N \ne I$になり、$M^{[s]} = b$という単純な更新が成り立たなくなるので、掃引中は常に直交中心を正しく追従させる必要があります。

## 計算量

各サイトでの最も重いステップはStep 1の環境縮約です。

**Step 1（局所解の縮約）**: $L_{s-1}$ ($D'_\text{MPS} \times D_\text{MPO} \times D_\text{MPS}$)、$A^{[s]}$ ($D_\text{MPS} \times d \times D_\text{MPS}$)、$W^{[s]}$ ($D_\text{MPO} \times d \times d \times D_\text{MPO}$)、$R_{s+1}$ ($D'_\text{MPS} \times D_\text{MPO} \times D_\text{MPS}$)の4つを縮約します。
適切な順序（例: $L_{s-1}$と$A^{[s]}$を先、次に$W^{[s]}$、最後に$R_{s+1}$）でやると、$D'_\text{MPS} \sim D_\text{MPS}$のとき$O(D_\text{MPS}^3 d D_\text{MPO} + D_\text{MPS}^2 d^2 D_\text{MPO}^2)$程度がドミナントです。

**Step 2（QR）**: $(D'_\text{MPS} d) \times D'_\text{MPS}$行列のQR分解で$O(D_\text{MPS}^3 d)$。

**環境更新**: Step 1とおおむね同オーダー。

サイトあたりの合計は$O(D_\text{MPS}^3 d D_\text{MPO} + D_\text{MPS}^2 d^2 D_\text{MPO}^2)$、1掃引全体で$O(L D_\text{MPS}^3 d D_\text{MPO} + L D_\text{MPS}^2 d^2 D_\text{MPO}^2)$。
掃引を$n_\text{sweep}$回まわすので、総コストはこれの$n_\text{sweep}$倍です。

[zip-up](https://zenn.dev/ultimatile/articles/tn-mps-zipup)との比較が要点です。
1掃引あたりのオーダーはzip-upとほぼ同じ（どちらも$D_\text{MPS} D_\text{MPO}$の太いボンドを局所的にしか作らない）で、素朴法の$O(L D_\text{MPS}^3 D_\text{MPO}^3 d)$より$D_\text{MPO}$について軽いという利得もそのまま引き継ぎます。
違いは$n_\text{sweep}$という掛け算がつくこと、すなわち

$$
\frac{\text{variational fitting}}{\text{zip-up}} \approx O(n_\text{sweep})
$$

だけ重い、ということです。
精度を上げるためにこの定数倍を払う、というのがvariational fittingの立ち位置です。

メモリは、最大テンソルがStep 1の中間（$O(D_\text{MPS}^2 D_\text{MPO} d)$オーダー）で、これに加えて全サイト分の環境テンソル$\{L_s\}, \{R_s\}$（各$O(D_\text{MPS}^2 D_\text{MPO})$、合計$O(L D_\text{MPS}^2 D_\text{MPO})$）をキャッシュします。
環境を毎回作り直さずキャッシュするのが実装の肝で、これがないと掃引のたびに$O(L)$の再縮約が入って計算量が$O(L^2)$に悪化します。

## 精度と収束の性質

variational fittingの長所と短所を整理します。

### 長所：与えられたボンド次元で最適に近い

各サイトの局所問題を厳密に解いて掃引を収束させるので、得られる$\ket{\tilde{\varphi}}$は「ボンド次元$D'_\text{MPS}$のMPSのなかで$\| \ket{\tilde{\varphi}} - \hat{W}\ket{\psi} \|$を（局所的に）最小化する」解に収束します。
zip-upの「左から一回切るだけ」と違い、右側に残った構造の要求を**掃引の往復で何度も織り込む**ので、同じ$D'_\text{MPS}$ならzip-upより誤差が小さくなるのが普通です。

### 短所1：初期値依存と局所解

ALSは非凸問題に対する座標降下なので、**大域最適解が保証されません**。
特に初期値が悪いと局所解に捕まり、フィデリティが頭打ちになることがあります。
これが「zip-upや密度行列法の出力を初期値にする」のが定石である理由です。
良い初期値から始めれば数回の掃引で十分収束し、局所解の心配もほぼ消えます。

### 短所2：ボンド次元を増やせない（1サイト版）

上で説明した1サイト更新は、各$M^{[s]}$の形を保ったまま中身だけ最適化します。
したがって**ボンド次元を動的に増やせません**。
初期MPSのボンド次元が小さすぎると、そこが上限として張り付きます。
対策は2サイト版（次節）か、初期値のボンド次元を十分大きく取っておくことです。

### 短所3：収束が遅い場合がある

エンタングルメントが急に増える状況や、初期値が大域解から遠い場合、掃引回数が増えます。
zip-upの「一発」と違い掃引数ぶんのコストがかかるので、要求精度が緩い場面ではzip-up単体のほうが得なこともあります。

定量的には、Paeckelらのレビュー[^paeckel2019]に各手法の精度比較があり、十分収束させたvariational fittingがzip-upより一貫して高精度であること、ただしその代償として掃引コストがかかることが示されています。

## 1サイト版と2サイト版

DMRGと同じく、variational fittingにも1サイト(single-site)版と2サイト(two-site)版があります。

- **1サイト版**: 上で説明したもの。中心テンソル$M^{[s]}$を1つだけ更新。安いがボンド次元を増やせない。
- **2サイト版**: 隣り合う2サイト$M^{[s]}, M^{[s+1]}$をまとめた$\Theta^{[s]}$を一括で解き、SVDで2つに割り直す。SVDの切り捨てでボンド次元を**動的に調整**できる。

2サイト版のStep 1は、$L_{s-1}$、$A^{[s]}, A^{[s+1]}$、$W^{[s]}, W^{[s+1]}$、$R_{s+2}$を縮約して

$$
\Theta^{[s]}_{m_{s-1}, \sigma_s', \sigma_{s+1}', m_{s+1}}
$$

を作り、$(m_{s-1}, \sigma_s') | (\sigma_{s+1}', m_{s+1})$でSVDして特異値を$D'_\text{MPS}$個まで切り捨てます。
ボンド次元を増やせる代わり、中間テンソルに物理脚が2本ぶん乗るのでサイトあたりのコストが$d$倍ほど重くなります。
初期ボンド次元の見積もりが難しい場面では2サイト版から始め、ボンドが落ち着いたら1サイト版に切り替える、という運用がよく使われます。

## 実装上の注意点

実装で踏みがちな細部を挙げておきます。

### 良い初期値を用意する

これがいちばん大事です。
乱数初期値からのvariational fittingは収束が遅く局所解にも弱いので、**zip-upの出力を初期値にする**のが定石です。
「zip-upで荒く速く作る → variational fitで磨く」という二段構えにすると、少ない掃引回数で高精度に到達できます（[zip-upの記事](https://zenn.dev/ultimatile/articles/tn-mps-zipup)の精度の節でも触れた通り）。
密度行列法の出力を初期値にする選択肢もあります。

### 環境テンソルのキャッシュと更新

環境$\{L_s\}, \{R_s\}$を毎回ゼロから縮約し直すと$O(L)$の無駄が掃引ごとに入ります。
直交中心を1サイト動かすたびに、確定したサイトのぶんだけ環境を**差分更新**（$L_{s-1} \to L_s$、$R_{s+1} \to R_s$）するのが必須です。
これで掃引が真に$O(L)$オーダーで回ります。

### 標準形の追従を崩さない

「なぜ混合標準形か」の節で述べた通り、$M^{[s]} = b$という単純更新は直交中心が正しくサイト$s$にある前提です。
Step 2のQR（またはSVD）で中心を隣へ移すのを忘れると、$N \ne I$になって更新式が破綻します。
掃引の向きと直交中心の位置を常に同期させる、というのが地味だが重要な不変条件です。

### 収束判定の取り方

距離の絶対値ではなく**掃引間の変化量**を見るのが安全です。
$\braket{\psi|\hat{W}^\dagger\hat{W}|\psi}$（定数項）を陽に計算するのは$D_\text{MPO}^2$ぶん重いので、これを避けて$\braket{\tilde{\varphi}|\tilde{\varphi}} - 2\,\mathrm{Re}\braket{\tilde{\varphi}|\hat{W}|\psi}$の変化、またはフィデリティの変化を見る実装が一般的です。
変化が機械精度近くまで落ちたら「これ以上掃引しても無駄」のサインです。

### MPOのスパース性

zip-up同様、Step 1の縮約はMPOのスパース性（近接相互作用Hamiltonianなら$D_\text{MPO} \times D_\text{MPO}$のうち$O(D_\text{MPO})$しか非零でない）を活かすと実速度が大きく変わります。
$W^{[s]}$を「サイト演算子のリスト+接続規則」として持ち、演算子ごとのループで縮約する実装が効きます。

### 対称性付きMPSとの相性

対称性を組み込んだMPS（[Abelian対称性テンソルの記事](https://zenn.dev/ultimatile/articles/intro-abelian-symmetric-tensor)）でもそのまま使えます。
環境テンソルもブロックスパースになり、Step 1の縮約とStep 2のQR/SVDがチャージブロックごとに独立に走るので軽くなります。
ただし2サイト版でSVD切り捨てによりボンドを動かすと、ブロックごとの保持本数の配分が動的に変わる点を慎重に扱う必要があります。

## まとめ

整理しなおすと：

1. **問題**: $\hat{W}\ket{\psi}$をボンド次元$D'_\text{MPS}$のMPSで最良近似したい。zip-upと同じ問題だが、「最良近似」を最適化問題として直接解くのがvariational fitting。
2. **定式化**: 距離$\| \ket{\tilde{\varphi}} - \hat{W}\ket{\psi} \|^2$を$\ket{\tilde{\varphi}}$について最小化。第3項は定数なので$\braket{\tilde{\varphi}|\tilde{\varphi}} - 2\mathrm{Re}\braket{\tilde{\varphi}|\hat{W}|\psi}$を最小化すればよい。
3. **アイデア**: 1サイトずつ局所最適化して左右に掃引(ALS)。混合標準形にしておくとノルム行列$N=I$になり、局所解は「環境と$A^{[s]}, W^{[s]}$を縮約するだけ」で求まる。
4. **アルゴリズム**: 環境$L_{s-1}, R_{s+1}$をキャッシュし、$M^{[s]} \leftarrow L_{s-1} A^{[s]} W^{[s]} R_{s+1}$で更新→QRで中心を移動→環境を差分更新。収束まで往復。
5. **計算量**: 1掃引はzip-upとほぼ同オーダー、ただし$n_\text{sweep}$回の掃引ぶん重い。素朴法より$D_\text{MPO}$について軽いのは共通。
6. **精度**: 収束すれば与えられたボンド次元での（局所）最適解。zip-upより高精度だが、初期値依存・局所解・1サイト版のボンド固定に注意。
7. **定石**: zip-up（または密度行列法）の出力を初期値にして磨く二段構え。

variational fittingは「掃引コストを払って精度を取りに行く」手法で、[zip-up](https://zenn.dev/ultimatile/articles/tn-mps-zipup)の速さと相補的です。
精度がクリティカルな場面（虚時間冷却、長時間発展など）では、zip-upや[密度行列法](https://zenn.dev/ultimatile/articles/tn-mpo-density-matrix)で初期値を作りvariational fitで仕上げる、という組み合わせが実用上もっともよく使われます。
3手法の精度・計算量の比較は[入口記事](https://zenn.dev/ultimatile/articles/tn-mpo-mps-comparison)にまとめています。
