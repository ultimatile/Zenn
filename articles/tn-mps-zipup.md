---
title: "MPO-MPS積を計算するzip-upアルゴリズム"
emoji: "🤐"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["tensornetwork", "matrixproductstate","tensortrain"]
published: false
---

## はじめに

本記事では、行列積状態(MPS) $\ket{\text{MPS}}$に行列積演算子(MPO) $\hat{W}_\text{MPO}$を作用させる操作MPO-MPS積(MMP)

$$
\hat{W}_\text{MPO}\ket{\text{MPS}}
$$

を計算する主要アルゴリズムの一つである**zip-upアルゴリズム**を解説します。

問題は、この演算を素直にやるとボンド次元が掛け算で増えてしまうことです。
MPSのボンド次元を$D_\text{MPS}$、MPOのボンド次元を$D_\text{MPO}$とすると、$\hat{W}_{\text{MPO}}\ket{\text{MPS}}$のボンド次元は一般に$D_\text{MPS} D_\text{MPO}$になります。
このままMMPを繰り返すと、$D_\text{MPS} D_\text{MPO}, D_\text{MPS} D_\text{MPO}^2, \ldots$と指数的にボンド次元が増加し、計算が破綻します。
したがって、掛けた直後にどこかで「増加したMPSのボンド次元を$D_\text{MPS}$程度に圧縮する」操作が必要です。

このとき、**素朴に「全部繋いでから圧縮」とやらない方法**のひとつが**zip-upアルゴリズム** [^stoudenmire2010]です。
名前の通り「ジッパーを左から右に閉じていく」ように、サイトごとに縮約とSVD切り捨てを交互に進めることで、中間段階でも$D_\text{MPS} D_\text{MPO}$という大きなボンドを丸ごと持たずに済む、という方法です。

[^stoudenmire2010]: E. M. Stoudenmire and S. R. White, *Minimally Entangled Typed Thermal State Algorithms*, *New J. Phys.* **12**, 055026 (2010), [arXiv:1002.1305](https://arxiv.org/abs/1002.1305). zip-upアルゴリズムは第3節で導入されています。

本記事はzip-upアルゴリズム単体の解説に絞ります。
同じ問題に対する別解（密度行列法、variational fitting）との比較は、別記事で扱う予定です。

参考文献としては、原典の[arXiv:1002.1305](https://arxiv.org/abs/1002.1305)、tensornetwork.orgの解説ページ[^tnorg]、および各種手法を比較したレビュー[^paeckel2019]を念頭に置いています。

[^tnorg]: <https://tensornetwork.org/mps/algorithms/zip_up_mpo/>。図解が丁寧で実装の手がかりになります。

[^paeckel2019]: S. Paeckel, T. Köhler, A. Swoboda, S. R. Manmana, U. Schollwöck, C. Hubig, *Time-evolution methods for matrix-product states*, *Ann. Phys.* **411**, 167998 (2019), [arXiv:1901.05824](https://arxiv.org/abs/1901.05824). zip-upを含む複数手法の精度と計算量の比較があります。

## 準備：MPSとMPO

記号を固定しておきます。
長さ$L$の一次元格子上で、サイト$s$の物理次元を$d$（典型的には$d = 2$がスピン$1/2$やスピンレスフェルミオン、$d = 4$がスピン$1/2$フェルミオン($\ket{0}, \ket{\uparrow}, \ket{\downarrow}, \ket{\uparrow\downarrow}$)など）とします。

### MPS

$\ket{\psi}$をMPSで

$$
\ket{\psi} = \sum_{\{\sigma\}} A^{[1]}_{\sigma_1} A^{[2]}_{\sigma_2} \cdots A^{[L]}_{\sigma_L} \ket{\sigma_1 \sigma_2 \cdots \sigma_L}
$$

と書きます。
$A^{[s]}_{\sigma_s}$は脚を3本持つテンソルで、インデックスを明示すれば$A^{[s]}_{l, \sigma_s, r}$、$l, r$がボンドインデックス、$\sigma_s$が物理インデックスです。
両端$l$ ($s=1$)と$r$ ($s=L$)は次元1の自明な脚としておきます。
ボンド次元の最大値を$D_\text{MPS}$とします。

### MPO

演算子$\hat{W}$をMPOで

$$
\hat{W} = \sum_{\{\sigma, \sigma'\}} W^{[1]}_{\sigma_1' \sigma_1} W^{[2]}_{\sigma_2' \sigma_2} \cdots W^{[L]}_{\sigma_L' \sigma_L} \ket{\sigma'_1 \cdots \sigma'_L}\bra{\sigma_1 \cdots \sigma_L}
$$

と書きます。
$W^{[s]}_{\sigma_s' \sigma_s}$は脚を4本持ち、インデックスを明示すれば$W^{[s]}_{b, \sigma_s', \sigma_s, b'}$、$b, b'$がMPOボンド、$\sigma_s$が入射物理脚（ket側）、$\sigma_s'$が出射物理脚（bra側）です。
両端$b$ ($s=1$)と$b'$ ($s=L$)は次元1。
MPOボンド次元の最大値を$D_\text{MPO}$とします。

### MPS標準形(canonical form)

MPSの右標準形(right-canonical form)とは、各テンソル$A^{[s]}$が

$$
\sum_{\sigma_s, r} A^{[s]}_{l, \sigma_s, r} (A^{[s]}_{l', \sigma_s, r})^{*} = \delta_{l l'}
$$

を満たす形のことです。
テンソル図で言えば「自身と複素共役を物理脚と右ボンドで縮約したら左ボンドの恒等行列になる」状態で、$A^{[s]}$を行列$l \to (\sigma_s, r)$と見たときに行が正規直交していることを意味します。

zip-upを始める前提として、入力MPSは右標準形にしておきます。
任意のMPSはQR分解の右から左への掃引で右標準形に変換できるので、これは$O(L D_\text{MPS}^3)$の前処理です。

## 問題設定：素朴な方法とその難点

まず、何もしないと何が起きるかを確認します。

$\hat{W}\ket{\psi}$のサイトごとのテンソルを単純に書き下すと、

$$
B^{[s]}_{(l, b), \sigma_s', (r, b')} = \sum_{\sigma_s} W^{[s]}_{b, \sigma_s', \sigma_s, b'} A^{[s]}_{l, \sigma_s, r}
$$

となり、$\ket{\varphi} = \hat{W}\ket{\psi}$は$B^{[s]}$を繋げたMPSで表せます。
ただしボンドが$(l, b)$と$(r, b')$という複合インデックスになっており、ボンド次元は$D_\text{MPS} \times D_\text{MPO}$。
これが冒頭で述べた「ボンドが掛け算で膨らむ」現象です。

これを再び$D_\text{MPS}$に圧縮するには、$B^{[s]}$を繋いだMPSを一度作ってから、左から右へのSVD掃引で順次切り捨てれば原理的にはできます。
しかしこの方法には実用上の難点があります：

1. **中間メモリが大きい**: 各サイトテンソル$B^{[s]}$はdim約$D_\text{MPS} D_\text{MPO} \cdot d \cdot D_\text{MPS} D_\text{MPO} = D_\text{MPS}^2 D_\text{MPO}^2 d$の要素を持つ。$D_\text{MPS} = 1000$, $D_\text{MPO} = 50$, $d = 2$で$5 \times 10^9$要素($\sim$ 40 GB / double倍精度)。
2. **SVDのコストが高い**: 圧縮掃引のSVDは$(D_\text{MPS} D_\text{MPO} \cdot d) \times (D_\text{MPS} D_\text{MPO})$行列が対象で、$O(D_\text{MPS}^3 D_\text{MPO}^3 d)$程度。$D_\text{MPO}$が大きいと致命的。
3. **無駄が大きい**: 最終的に$D_\text{MPS}$に切り詰めるのに、いったん$D_\text{MPS} D_\text{MPO}$まで膨らませる必要は本来ない。

zip-upは、これら3つを同時に回避する方法です。

## アイデア：縮約と圧縮を交互に進める

zip-upの発想は単純です：「左から順に、サイトテンソル1つぶんだけ縮約して、即座にSVDで切り捨てる」。

掃引中、計算済みの左側は新MPSのテンソル$M^{[1]}, \ldots, M^{[s]}$（ボンド次元$\le D'_\text{MPS}$）で表され、未処理の右側は元の$A^{[s+1]}, \ldots, A^{[L]}$と$W^{[s+1]}, \ldots, W^{[L]}$がそのまま残っています。
両者を繋ぐ「持ち越しテンソル」$R_s$を用意し、これがジッパーの引き手の役を果たします。

模式図で書けば、サイト$s$まで進んだ状態は

![zip-up algorithm mid-sweep state at site s](/images/tn-mps-zipup/zipup-state.png)

の形をしており、$R_s$は左に新MPSの細いボンド、右に$A$の太いボンドと$W$の太いボンドの2本を持つテンソル（脚3本、形$D'_\text{MPS} \times D_\text{MPS} \times D_\text{MPO}$）です。
これを使って次の一手は

1. $R_s$を$A^{[s+1]}$と$W^{[s+1]}$に縮約→大きいテンソル$C_{s+1}$を作る。
2. $C_{s+1}$を「左から見たブロック」と「右から見たブロック」にSVDで分解。
3. $U$側を新サイトテンソル$M^{[s+1]}$とし、$S V^\dagger$を新たな持ち越し$R_{s+1}$とする。
4. SVDの段階で特異値を$D'_\text{MPS}$個まで（あるいは閾値$\epsilon$で）切り捨てる。

これを図で書くと

![zip-up iteration: contract → SVD → identify](/images/tn-mps-zipup/zipup-iter.png)

となります。

これを$s = 0$（自明な初期$R_0$）から$s = L-1$まで繰り返すと、左標準形の新MPS $M^{[1]}, \ldots, M^{[L]}$ができあがります。

ポイントは、ボンド$D_\text{MPS} D_\text{MPO}$が登場するのは**$C_{s+1}$という局所テンソルの中だけ**で、サイトを進めば消えてしまうことです。
全長にわたって$D_\text{MPS} D_\text{MPO}$のボンドを保持する必要がない、というのがzip-upの本質的な節約です。

## アルゴリズム詳細

具体的に書き下します。

### 初期化

$R_0$は自明な「scalar 1」とします（次元$1 \times 1 \times 1$のテンソル、左ボンド・右ボンド・MPO右ボンドすべて自明）。

### サイト$s = 1, \ldots, L-1$のループ

**Step 1（縮約）**: $R_{s-1}$、$A^{[s]}$、$W^{[s]}$を縮約して

$$
C^{[s]}_{m_{s-1}, \sigma_s', r, b'}
=
\sum_{l, b, \sigma_s}
(R_{s-1})_{m_{s-1}, l, b}
\, A^{[s]}_{l, \sigma_s, r}
\, W^{[s]}_{b, \sigma_s', \sigma_s, b'}
$$

を作ります。
$C^{[s]}$の脚は4本: 左ボンド$m_{s-1}$（次元$\le D'_\text{MPS}$、ただし$m_0 = 1$）、新物理脚$\sigma_s'$（次元$d$）、右ボンド$r$（次元$\le D_\text{MPS}$）、MPO右ボンド$b'$（次元$\le D_\text{MPO}$）。

このテンソルが、zip-upの中で唯一$O(D_\text{MPS} D_\text{MPO})$オーダーのサイズを取る場所です。
要素数は$D'_\text{MPS} \cdot d \cdot D_\text{MPS} \cdot D_\text{MPO}$で、典型的に$D'_\text{MPS} \sim D_\text{MPS}$なら$D_\text{MPS}^2 D_\text{MPO} d$オーダー。
素朴法の$D_\text{MPS}^2 D_\text{MPO}^2 d$より$D_\text{MPO}$ぶん軽い、というのがここでの利得です。

**Step 2（SVDと切り捨て）**: $C^{[s]}$を行列としてリシェイプしてSVDします。

「左ブロック」を$(m_{s-1}, \sigma_s')$、「右ブロック」を$(r, b')$とまとめると、$C^{[s]}$は$(D'_\text{MPS} d) \times (D_\text{MPS} D_\text{MPO})$の行列。
これを

$$
C^{[s]}_{(m_{s-1}, \sigma_s'), (r, b')}
= \sum_{m_s} U^{[s]}_{(m_{s-1}, \sigma_s'), m_s} \, S^{[s]}_{m_s} \, V^{[s] \dagger}_{m_s, (r, b')}
$$

とSVDし、特異値を大きい順に$D'_\text{MPS}$個まで（または閾値$S_{m_s} \ge \epsilon$で）切り捨てます。
打ち切り後の新ボンド次元$m_s \le D'_\text{MPS}$。

**Step 3（割り当てと持ち越し）**:

- 新サイトテンソル: $M^{[s]}_{m_{s-1}, \sigma_s', m_s} = U^{[s]}_{(m_{s-1}, \sigma_s'), m_s}$
- 持ち越し: $(R_s)_{m_s, r, b'} = S^{[s]}_{m_s} V^{[s] \dagger}_{m_s, (r, b')}$

$U$の取り方から$M^{[s]}$は自動的に**左標準形**になります：

$$
\sum_{m_{s-1}, \sigma_s'} M^{[s]}_{m_{s-1}, \sigma_s', m_s} (M^{[s]}_{m_{s-1}, \sigma_s', m_s'})^* = \delta_{m_s m_s'}.
$$

これは新MPSが直接「左から左標準形で組み上がっていく」ことを意味します。
最後に左右どちらかのcanonical formに変換する後処理が不要、というのはzip-upの地味な利点です。

### 最終サイト$s = L$

最後だけ少し違います。
$s = L$では$R_{L-1}$、$A^{[L]}$、$W^{[L]}$を縮約しますが、$A^{[L]}$の右ボンドと$W^{[L]}$のMPO右ボンドはどちらも次元1の自明な脚なので、SVDで切り出す「右ブロック」がtrivialになります。
このため最後のサイトはSVDを行わずそのまま新サイトテンソル$M^{[L]}$として割り当てます：

$$
M^{[L]}_{m_{L-1}, \sigma_L', \cdot}
=
\sum_{l, b, \sigma_L}
(R_{L-1})_{m_{L-1}, l, b}
\, A^{[L]}_{l, \sigma_L, \cdot}
\, W^{[L]}_{b, \sigma_L', \sigma_L, \cdot}
$$

ここで「$\cdot$」は次元1の自明な脚。

掃引終了時点で得られる新MPS $M^{[1]} \cdots M^{[L]}$は左標準形で、ボンド次元は各$s$で$\le D'_\text{MPS}$になっています。

## なぜright-canonical前提が必要か

ここで使っているSVDの打ち切りは、その時点での「左右のカット」でのSchmidt分解の近似になっています。
入力MPS $\ket{\psi}$がright-canonicalであれば、各サイト$s$で

- 左側（既に処理済み）: $M^{[1]}, \ldots, M^{[s]}$は構成法から左標準形
- 右側（未処理）: $A^{[s+1]}, \ldots, A^{[L]}$は仮定から右標準形

になっており、$R_s$の特異値は$\ket{\varphi} = \hat{W}\ket{\psi}$のサイト$s$後のカットでのSchmidt係数を**MPOの右側を含めて見たときの値**として近似的に再現します。
このとき切り捨てによる誤差は、その特異値の二乗和で見積もれます：

$$
\| \ket{\varphi} - \ket{\varphi}^\text{truncated} \|^2 \approx \sum_{m_s > D'_\text{MPS}} (S_{m_s})^2.
$$

入力がright-canonicalでないと、ここでの特異値はSchmidt係数とは別物になり、$L^2$誤差の見積もりも保証されません。
実装では「掛け算前に右標準形に変換」を必ずやっておくのが安全です。

なお、「Schmidt係数を再現する」と言っても、それはMPOの右側部分も含めたcutの話で、最終的に欲しい$\ket{\varphi}$それ自体のSchmidt値そのものではありません。
この乖離がzip-upの精度限界の根本原因で、後述します。

## 計算量

各サイトでの最も重いステップはStep 1とStep 2です。

**Step 1（縮約）**: $R_{s-1}$ ($D'_\text{MPS} \times D_\text{MPS} \times D_\text{MPO}$)、$A^{[s]}$ ($D_\text{MPS} \times d \times D_\text{MPS}$)、$W^{[s]}$ ($D_\text{MPO} \times d \times d \times D_\text{MPO}$)を3つ縮約。
適切な順序（例: $R_{s-1}$と$A^{[s]}$を先、次に$W^{[s]}$）でやると$O((D'_\text{MPS})^2 d D_\text{MPO} D_\text{MPS} + D'_\text{MPS} d^2 D_\text{MPO}^2 D_\text{MPS})$程度。$D'_\text{MPS} \sim D_\text{MPS}$なら$O(D_\text{MPS}^2 d^2 D_\text{MPO}^2)$がドミナント。

**Step 2（SVD）**: $(D'_\text{MPS} d) \times (D_\text{MPS} D_\text{MPO})$行列のSVD。$D'_\text{MPS} \sim D_\text{MPS}$、$D_\text{MPO} \ge d$なら通常$D_\text{MPS} d \le D_\text{MPS} D_\text{MPO}$で、コストは$O((D'_\text{MPS})^2 d^2 \cdot D_\text{MPS} D_\text{MPO}) = O(D_\text{MPS}^3 d^2 D_\text{MPO})$程度。

サイトあたりの合計は$O(D_\text{MPS}^3 d^2 D_\text{MPO} + D_\text{MPS}^2 d^2 D_\text{MPO}^2)$、全体で$O(L D_\text{MPS}^3 d^2 D_\text{MPO} + L D_\text{MPS}^2 d^2 D_\text{MPO}^2)$。

比較として、素朴法（全部繋いでから圧縮）は、中間MPSのボンドが$D_\text{MPS} D_\text{MPO}$なので圧縮掃引のSVDコストが$O(D_\text{MPS}^3 D_\text{MPO}^3 d)$程度、全体$O(L D_\text{MPS}^3 D_\text{MPO}^3 d)$。

zip-upと素朴法の比は

$$
\frac{O(L D_\text{MPS}^3 d^2 D_\text{MPO})}{O(L D_\text{MPS}^3 D_\text{MPO}^3 d)} = O\!\left(\frac{d}{D_\text{MPO}^2}\right)
$$

で、$D_\text{MPO}$が大きいほどzip-upの優位が大きくなります。
たとえば近接相互作用Hubbard鎖の$D_\text{MPO} = 6$、$d = 4$なら比は$\sim 1/9$、より長距離・高Trotter次数の$D_\text{MPO} = 30$、$d = 2$なら$\sim 1/450$。

メモリも同様で、zip-upの最大テンソルは$C^{[s]}$の$O(D_\text{MPS}^2 D_\text{MPO} d)$要素、素朴法は中間$B^{[s]}$の$O(D_\text{MPS}^2 D_\text{MPO}^2 d)$要素なので、ピークメモリで$D_\text{MPO}$ぶん節約できます。

## 精度の限界とその直感

zip-upが「速いし簡単」なのは見た通りですが、結果の精度は変分的に最適ではありません。
具体的には、得られた$\ket{\varphi}^\text{truncated}$は、与えられたボンド次元$D'_\text{MPS}$で表されるMPSのなかで$\| \ket{\varphi} - \ket{\varphi}^\text{truncated} \|$を最小化するMPSとは一般に**異なります**。

直感的な理由は、SVD切り捨てが「現時点のカットでの局所的ベスト」を採るだけで、右側に残っている$A^{[s+1]} \cdots A^{[L]}$と$W^{[s+1]} \cdots W^{[L]}$の構造が、後段で新ボンドにどう要求してくるかを**先読みしない**ことです。
左から右への一回掃引で打ち切り判断を確定させてしまうので、右側の情報による調整は次のサイトに進んだあとはもう効きません。

数式で言うと、Step 2のSVDは

$$
\min_{\text{rank} \le D'_\text{MPS}} \| C^{[s]} - \tilde{C}^{[s]} \|_F^2
$$

という局所行列ノルムの最小化問題を解いているだけで、目的の全体誤差

$$
\| \ket{\varphi} - \ket{\varphi}^\text{truncated} \|^2
$$

を直接最小化しているわけではありません。
両者は、入力MPSがright-canonicalの仮定の下で「サイト$s$後のカットでのSchmidt cut」として一致するべきですが、それはMPOを含めて見たカットでの話で、MPOを取り除いた最終MPSのSchmidt cutと完全には一致しません。
このズレが「変分法より精度が劣る」原因です。

実用的には：

- **誤差は単調に蓄積する**: サイトを進むにつれて累積するので、$L$が大きく$D'_\text{MPS}$が小さい場面では顕著。
- **MPOの構造に依存する**: $\hat{W}$がサイト局所に近い（$D_\text{MPO}$小）ほどzip-upと最適解の差は小さく、長距離・複雑な$\hat{W}$ほど差が広がる傾向。
- **後処理で改善できる**: zip-upで得たMPSをそのまま使うのではなく、「同じMPSをターゲットにしたvariational fittingの初期値」として使うと、少ないsweep回数で変分最適解に近づける。実装ではこのパターンが多用されます。

定量的には、Paeckelらのレビュー[^paeckel2019]に各手法の精度比較が載っており、zip-upが時間発展では他手法より誤差が一桁程度大きくなる場合があることが示されています。
精度がクリティカルなとき（虚時間冷却で最低エネルギーを精密に追う、長時間の純粋状態発展など）はzip-up単体ではなく、後段にvariational fitを挿むのが安全です。

## 実装上の注意点

実装で踏みがちな細部を挙げておきます。

### 標準形の事前変換を忘れない

入力MPSの標準形が崩れていると、特異値の意味が変わり、切り捨て閾値$\epsilon$の校正がおかしくなります。
zip-upに渡す前に必ずright-canonicalに揃えるラッパを置くと、呼び出し側の規約に依存せず動作が安定します。
これは$O(L D_\text{MPS}^3)$のQR掃引で、zip-up本体の$O(L D_\text{MPS}^3 D_\text{MPO})$より軽いので、無条件で入れて損はありません。

### 切り捨て規約の統一

切り捨てには大きく分けて3通りあります：

1. **最大ボンド次元** $D'_\text{MPS}$で固定
2. **特異値閾値** $S_{m_s} \ge \epsilon \cdot S_1$（相対値）または$\ge \epsilon$（絶対値）
3. **累積打ち切り誤差** $\sum_{m_s > k} S_{m_s}^2 \le \delta$となる最小の$k$

実装では通常これらを組み合わせ、「最大$D'_\text{MPS}$かつ、相対誤差$\delta$を超えないように」のように複合条件を使うのが普通です。
切り捨てるかどうかの判断は数値的に微妙で、複数の条件のうちもっとも厳しいものを採る、というルールが安全です。

### 行列の特異値が縮退している場合

特異値がほぼ縮退している境界で打ち切ると、数値誤差で順序がランダムに入れ替わって結果が一回ごとに変わる、という問題が起きえます。
これはzip-upに限った話ではないMPS全般の問題ですが、特にzip-upで精度を測るときには、縮退境界をまたいで打ち切らないよう$D'_\text{MPS}$を少し余裕を持って取る、または明示的な縮退検出を入れる、などの対応が有効です。

### MPOのスパース性

MPOは一般に非常にスパースです（典型的な近接相互作用HamiltonianのMPOは$D_\text{MPO} \times D_\text{MPO}$のうち$O(D_\text{MPO})$の要素しか非零でない）。
Step 1の縮約はこのスパース性を活かしたコードにすると実速度が大きく変わります。
具体的には、$W^{[s]}_{b, \sigma_s', \sigma_s, b'}$を「サイト演算子のリスト+接続規則」として持ち、密GEMMではなく演算子ごとのループで縮約する実装が、ITensorなどで採用されています。

### 対称性付きMPSとの相性

対称性を組み込んだMPS（[[intro-abelian-symmetric-tensor]]）でもzip-upの構造はそのまま使えます。
ブロックスパーステンソルでのSVDは各チャージブロック独立に走るので、Step 2のSVDコストは$1/q^2$ ($q$はチャージ種数)でさらに軽くなります。
ただし「持ち越し$R_s$のチャージ構造が掃引中に動的に変化する」点を扱うために、ブロック構造を持つテンソルのreshapeを慎重に実装する必要があります。

## まとめ

整理しなおすと：

1. **問題**: $\hat{W}\ket{\psi}$をボンド次元$D'_\text{MPS}$のMPSとして求めたいが、素朴にやるとボンドが$D_\text{MPS} D_\text{MPO}$に膨らんでメモリ・計算量が悪化する。
2. **zip-upのアイデア**: 左から右へ「縮約→ SVD切り捨て→持ち越し」を繰り返し、$D_\text{MPS} D_\text{MPO}$ボンドは局所的にしか作らない。
3. **アルゴリズム**: $R_{s-1}$、$A^{[s]}$、$W^{[s]}$を縮約して$C^{[s]}$を作り、$(m_{s-1}, \sigma_s') | (r, b')$でSVDして$U$を新サイトテンソル$M^{[s]}$、$SV^\dagger$を$R_s$に。
4. **前提**: 入力MPSはright-canonicalに揃えておく。これでStep 2の打ち切りが（MPOを含めたカットでの）Schmidt cutに対応する。
5. **計算量**: 素朴法に対して$O(d/D_\text{MPO}^2)$オーダーの高速化、メモリも$O(1/D_\text{MPO})$。
6. **精度**: 変分最適ではない。誤差は累積する。精度が要るときはzip-upを初期値にしてvariational fitを後段に置く。
7. **出力**: 左標準形の新MPSが直接得られ、後処理不要。

zip-upは「他の手法より速いが厳密には最適ではない」という典型的なヒューリスティックで、要求精度と計算資源のトレードオフで使い分ける道具です。
**密度行列法**と**variational fitting**は同じ問題への別解で、それぞれ精度と計算量のtrade-offが異なります。
これらの手法との比較は別記事で扱う予定です。
