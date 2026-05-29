---
title: "KAK分解入門"
emoji: "🦀"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["量子コンピュータ", "量子ゲート", "テンソルネットワーク", "cpp"]
published: false
---

## はじめに

任意の$n$量子ビットユニタリ演算は1量子ビットゲートと2量子ビットゲートの列に分解できるが、実験的制約からゲート数の最小化が重要である。特に2量子ビットゲートのCNOT分解は中心的課題であり、任意の2量子ビットゲート$U \in SU(4)$は**最大3 CNOTと15個の1量子ビットゲート**で最適に実現できることが知られている[^vw04]。

本記事ではこの結果の基礎となる**KAK分解**（Cartan分解の特殊ケース）を解説し、最後にPythonによる小さな実装（PoC）でアルゴリズムの主要部分を確認する。

[^vw04]: F. Vatan and C. Williams, "Optimal quantum circuits for general two-qubit gates", Phys. Rev. A **69**, 032315 (2004). arXiv: [quant-ph/0308006](https://arxiv.org/abs/quant-ph/0308006).

## KAK（Weyl）分解

### 定義

任意の2量子ビットユニタリゲート$U \in SU(4)$は以下のように分解できる:

$$
U = \mathrm{e}^{\mathrm{i}\phi}\,K_1 K_2\,\exp\!\left(\mathrm{i}\,\sum_{\alpha=x,y,z}c_\alpha\,\sigma_{1\alpha}\sigma_{2\alpha}\right)K'_1 K'_2.
$$

図で書くと以下のようになる。

![KAK decomposition tensor network](/images/intro-kak-decomposition/kak-tn.png)

ここで

- $K_1, K_2, K'_1, K'_2 \in SU(2)$: 1量子ビットゲート（**局所**演算）。下付き添字$1, 2$はサイト（量子ビット）を、プライムの有無は局所層の出順（$K_i$が左側＝先に書く層、$K'_i$が右側の層）を表す
- $c_x, c_y, c_z \in \mathbb{R}$: 正準（Weyl）パラメータ（**非局所**演算を特徴づける）
- $\phi \in \mathbb{R}$: グローバル位相
- $\sigma_{i\alpha}$（$i = 1, 2$, $\alpha = x, y, z$）は量子ビット$i$に作用するパウリ演算子（他方には恒等演算）。すなわち$\sigma_{1\alpha} = \sigma_\alpha \otimes I$, $\sigma_{2\alpha} = I \otimes \sigma_\alpha$であり、$\sigma_{1\alpha}\sigma_{2\alpha} = \sigma_\alpha \otimes \sigma_\alpha$は2量子ビットのパウリテンソル積。以降この量子多体系記法を採り、異なるサイトに作用する演算子の積は暗黙のテンソル積とみなす（例: $K_1 K_2 = K_1 \otimes K_2$）。冗長な$\otimes I$表示も避ける

$SU(4)$は15次元リー群で、KAK分解は12パラメータの局所演算と3パラメータの非局所演算に分離する。**3パラメータ$(c_x, c_y, c_z)$が2量子ビットゲートの非局所的性質を完全に特徴づける**ことが本記事のひとつの主題である。

### リー代数の視点

「KAK」の名称はCartan分解の構造に由来する。$\mathfrak{su}(4)$のリー代数は

$$
\mathfrak{su}(4) = \underbrace{\mathfrak{k}}_{\text{局所}} \oplus \underbrace{\mathfrak{p}}_{\text{非局所}}
$$

と分解される。ここで

- $\mathfrak{k} = \mathrm{span}\{\sigma_{1\mu}, \sigma_{2\mu}\}_{\mu \in \{x, y, z\}}$: 局所演算の生成子（6次元）
- $\mathfrak{p} = \mathrm{span}\{\sigma_{1\mu}\sigma_{2\nu}\}_{\mu, \nu \in \{x, y, z\}}$: 非局所演算の生成子（9次元）

$\mathfrak{p}$の中で互いに可換な最大部分代数（Cartan部分代数）は

$$
\mathfrak{a} = \mathrm{span}\{\sigma_{1x}\sigma_{2x},\, \sigma_{1y}\sigma_{2y},\, \sigma_{1z}\sigma_{2z}\}
$$

である。$[\sigma_{1x}\sigma_{2x}, \sigma_{1y}\sigma_{2y}] = 0$等は容易に確認できる。これが3次元であることが、非局所パラメータが3つであることに対応する。残りの6つの非局所生成子（$\sigma_{1x}\sigma_{2y}$, $\sigma_{1x}\sigma_{2z}$等）の自由度は左右の局所演算$K, K'$に吸収される。

## Weyl chamberと正準クラスベクトル

$U, V \in SU(4)$が**局所演算を除いて同値**であるとは、$U(2)$の元$R_1, R_0, S_1, S_0$が存在して

$$
U = (R_1 \otimes R_0)\, V\, (S_1 \otimes S_0)
$$

と書けることである。この同値関係$\sim$は$SU(4)$を**同値類**に分割し、各同値類は正準パラメータ$(c_x, c_y, c_z)$で特徴づけられる。これを**クラスベクトル**と呼ぶ。

正準パラメータには冗長性があり、3種類の**クラス保存変換**が存在する:

1. **シフト**: 任意の成分に$\pm \pi/2$を加算。例えば$c_x \to c_x + \pi/2$は

$$
\mathrm{e}^{\mathrm{i}[(c_x + \pi/2)\sigma_{1x}\sigma_{2x} + c_y\sigma_{1y}\sigma_{2y} + c_z\sigma_{1z}\sigma_{2z}]} = \underbrace{\mathrm{i}\,\sigma_{1x}\sigma_{2x}}_{\text{局所的}} \cdot \mathrm{e}^{\mathrm{i}(c_x\sigma_{1x}\sigma_{2x} + c_y\sigma_{1y}\sigma_{2y} + c_z\sigma_{1z}\sigma_{2z})}
$$

のように同値類を保つ。

1. **反転**: 2成分の符号を同時に反転。例えば$(c_x, c_y, c_z) \to (-c_x, -c_y, c_z)$は

$$
\sigma_{1z}\, \mathrm{e}^{\mathrm{i}\,\vec{c}\cdot\vec{\Sigma}}\, \sigma_{1z} = \mathrm{e}^{\mathrm{i}(-c_x, -c_y, c_z)\cdot\vec{\Sigma}}
$$

で実現される。$\vec{\Sigma} = (\sigma_{1x}\sigma_{2x}, \sigma_{1y}\sigma_{2y}, \sigma_{1z}\sigma_{2z})$とした。

1. **交換**: 2成分を入れ替え（Hadamard系のCliffordによる軸交換）。

これらにより、任意のクラスベクトルは以下の**正準領域**（Weyl chamber）に帰着できる:

$$
\frac{\pi}{2} > c_x \ge c_y \ge c_z \ge 0,\qquad c_x + c_y \le \frac{\pi}{2}
$$

これは3次元空間中の**四面体** $OA_1A_2A_3$として視覚化できる。頂点と代表的な点は:

- $O = (0, 0, 0)$: 恒等演算$I$
- $A_1 = (\pi/2, 0, 0)$: 局所演算と同値（$\sigma_{1x}\sigma_{2x}$の半周期）
- $A_2 = (\pi/4, \pi/4, 0)$: iSWAP
- $A_3 = (\pi/4, \pi/4, \pi/4)$: SWAP
- $B = (\pi/4, 0, 0)$: CNOT（辺$OA_1$の中点）
- $(\pi/8, 0, 0)$: $\sqrt{\mathrm{CNOT}}$

![Weyl chamber tetrahedron](/images/intro-kak-decomposition/weyl-chamber.png)
*正準パラメータ空間中のWeyl chamber（四面体 $OA_1A_2A_3$）。底面 $c_z = 0$ は $SO(4)$クラス（2 CNOT）、線分 $OB$ は1 CNOTで実現できる軌跡、内部は一般の3 CNOT領域に対応する。代表点 $O(=I)$, $\sqrt{\mathrm{CNOT}}$, $B(=\mathrm{CNOT})$, $A_2(=\mathrm{iSWAP})$, $A_3(=\mathrm{SWAP})$ の座標はPoC実装（`kak.py`）で実際に分解して得た値。*

線分$OB$上の任意の点は1 CNOTで実現可能であり、CNOTを「半分」にした$\sqrt{\mathrm{CNOT}}$などが自然に位置づけられる。

なお、ここで描いた領域は$c_x$を$\pi/2$まで許す**フルなWeyl chamber**であり、後述の実装が折り畳む**縮約Weyl chamber**（$\pi/4 \ge c_x \ge c_y \ge |c_z|$）はこの四面体をさらにクラス保存変換で還元したものである。

:::message
**非局所とエンタングリングの区別**: $A \otimes B$で書けないゲートは**非局所**（non-local）と呼ばれるが、すべてがエンタングリングゲートとは限らない。SWAPは非局所だが積状態を積状態に写すためエンタングリングパワー$\mathrm{EP}(\mathrm{SWAP}) = 0$である（後述）。
:::

## Magic基底

Bell状態に近いエンタングル基底を取ると、$SU(4)$の構造が劇的に簡単になる。**Magic基底**[^magic-conv]と呼ばれるユニタリ行列$\mathcal{B}$を以下で定義する:

$$
\mathcal{B} = \frac{1}{\sqrt{2}} \begin{pmatrix}
1 & \mathrm{i} & 0 & 0 \\
0 & 0 & \mathrm{i} & 1 \\
0 & 0 & \mathrm{i} & -1 \\
1 & -\mathrm{i} & 0 & 0
\end{pmatrix}
$$

この行列の各列はBell状態の変種（最大エンタングル状態）であり、

$$
|\Phi_0\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}},\quad |\Phi_1\rangle = \mathrm{i}\,\frac{|00\rangle - |11\rangle}{\sqrt{2}}
$$

$$
|\Phi_2\rangle = \mathrm{i}\,\frac{|01\rangle + |10\rangle}{\sqrt{2}},\quad |\Phi_3\rangle = \frac{|01\rangle - |10\rangle}{\sqrt{2}}
$$

[^magic-conv]: 文献によって列の順序や$\mathcal{B} U \mathcal{B}^\dagger$ vs $\mathcal{B}^\dagger U \mathcal{B}$の両方が異なる。本記事ではQiskitの規約$M = \mathcal{B}^\dagger U \mathcal{B}$を採用する。

### 同型$SU(2) \otimes SU(2) \cong SO(4)$

KAK分解の数学的基礎をなすのは次の同型である:

$$
A, C \in SU(2) \;\Longrightarrow\; \mathcal{B}^\dagger (A \otimes C)\, \mathcal{B} \in SO(4)
$$

すなわちmagic基底で見ると、**局所ゲートのテンソル積は実直交変換になる**。逆に、$O \in SO(4)$ならば$\mathcal{B}\, O\, \mathcal{B}^\dagger \in SU(2) \otimes SU(2)$である。両者は2対1準同型$\Phi: SU(2) \times SU(2) \to SO(4)$で結ばれており、$(A, C)$と$(-A, -C)$が同じ$SO(4)$の元に写る。

### KAK分解のmagic基底表現

KAK分解をmagic基底に変換すると、

$$
M = \mathcal{B}^\dagger U \mathcal{B} = K_m \cdot D \cdot K'_m
$$

ここで$K_m, K'_m \in SO(4)$、$D = \mathrm{diag}(\mathrm{e}^{\mathrm{i}d_0}, \mathrm{e}^{\mathrm{i}d_1}, \mathrm{e}^{\mathrm{i}d_2}, \mathrm{e}^{\mathrm{i}d_3})$。

つまり**局所演算は実直交行列** $SO(4)$として、**非局所部分は対角位相行列** $D$として現れる。これがKAK分解アルゴリズムの主舞台になる。

## アルゴリズム: $N = M^T M$とTakagi分解

### $N$の構造

$M = \mathcal{B}^\dagger U \mathcal{B}$に対し$N = M^T M$とおく（**転置**であり、共役転置ではない）。

KAK分解を代入し、$K_m, K'_m \in SO(4)$より$K_m^T K_m = I$かつ$D^T = D$なので

$$
N = M^T M = {K'_m}^T \cdot D^2 \cdot K'_m
$$

これは$N$の**Takagi分解**にほかならない。Takagi分解とは、対称行列$N = N^T$に対して$V^T N V = \Lambda$（対角）を満たすユニタリ$V$を求める分解で、通常の固有値分解$P^{-1} N P = \Lambda$と異なり左側が転置になる。

$V = K'_m$が求まれば、$D^2$の固有値から位相$d_k$が、$M = K_m D V^T$から$K_m = M V D^{-1}$が得られる。

### Hermitianトリック

$N$は対称かつユニタリだがHermitianではないため、直接`eigh`（Hermitian行列の固有値分解）で対角化できない。標準的なTakagi分解ルーチンも一般には利用できないため、**$N$を実Hermitian行列に変換**する。

$N$が対称ユニタリのとき、

$$
H_1 = \mathrm{Re}(N) + \mathrm{Im}(N) = \frac{(1-\mathrm{i})N + (1+\mathrm{i})N^\dagger}{2}
$$

は**実対称行列**になる。固有値は$\sqrt{2}\sin(2\phi_k + \pi/4)$（$\phi_k$は$D^2$の位相の半分）。

なぜ$\mathrm{Re}(N) + \mathrm{Im}(N)$かというと、CNOTのような特定のゲートでは$\mathrm{Re}(N) = 0$になるため$\mathrm{Re}(N)$単独では全固有値が0で完全縮退してしまうからである。$\mathrm{Im}(N)$を加えることで縮退が解ける場合が多い。

### 2段階固有分解

$H_1$の`eigh`で得た固有ベクトル行列$V_\mathrm{tmp}$には、$H_1$の縮退固有空間内で**自由度が残る**。これを解消するため、もう1つの実対称行列

$$
H_2 = \mathrm{Re}(N) - \mathrm{Im}(N)
$$

を導入する。$H_2$の固有値は$\sqrt{2}\cos(2\phi_k + \pi/4)$で、$H_1$と異なるパターンを持つ。

ただし**ここで注意が必要**で、$V_\mathrm{tmp}^\dagger H_2 V_\mathrm{tmp}$全体に2段目の`eigh`をかけると、$H_1$ブロック間の混合が許容されてしまい、特定のドレッシングされた入力（例: $(\pi/8, \pi/8, c)$近傍で$H_1$が3重縮退する点）で同時対角化が破綻する[^cluster-bug]。

これを避けるため、$V_\mathrm{tmp}$の列を$H_1$の固有値クラスタにグループ化し、**各クラスタ内に制限した** $V_g^\dagger H_2 V_g$ごとに`eigh`を適用する（cluster-restricted simultaneous diagonalization）。クラスタ内の回転$R_g$をスキャッターして得た4×4回転$R$から、最終的な固有ベクトル行列は

$$
V = V_\mathrm{tmp} R
$$

となる。

[^cluster-bug]: 当初の素朴な実装（global eigh）はこの3重縮退点で$O(1)$のFrobenius round-trip誤差を生じていた。クラスタ化しきい値は相対$10^{-4}$、絶対床$10^{-12}$で、`eigh`の固有ベクトル精度劣化（誤差$\sim$ ulp $\cdot \|N\| / \mathrm{gap}$）を吸収するように選んでいる。

最後に各列の最大絶対値要素を実正にして位相を固定し、$\det(V) = +1$を強制（必要なら第0列を反転）して$V \in SO(4)$を保証する。

### 正準パラメータの抽出

magic基底で$\exp(\mathrm{i}(c_x\sigma_{1x}\sigma_{2x} + c_y\sigma_{1y}\sigma_{2y} + c_z\sigma_{1z}\sigma_{2z}))$が対角化されることから、slot encodingは

$$
\begin{aligned}
d_0 &= c_x - c_y + c_z, & d_1 &= -c_x + c_y + c_z, \\
d_2 &= c_x + c_y - c_z, & d_3 &= -c_x - c_y - c_z
\end{aligned}
$$

となる[^slot-fix]。逆変換はソート不要でペア和から直接:

$$
c_x = \frac{d_0 + d_2}{2},\quad c_y = \frac{d_1 + d_2}{2},\quad c_z = \frac{d_0 + d_1}{2}
$$

[^slot-fix]: 複数の文献規約が混在する領域なので、$\mathcal{B}^\dagger \sigma_{1x}\sigma_{2x} \mathcal{B}$等を自分で対角化して整合性を確認するのが安全。

## 計算基底への復元

magic基底の結果を計算基底に戻す:

$$
K' = \mathcal{B}\, V^T\, \mathcal{B}^\dagger,\qquad K = \mathcal{B}\, (M V D^{-1})\, \mathcal{B}^\dagger
$$

同型$SO(4) \cong SU(2) \otimes SU(2)$より$K, K' \in SU(2) \otimes SU(2)$なので、各層を$A \otimes B$の形にテンソル積分解できる。実装では16要素から最大絶対値要素をピボットに取って$A, B$を抽出する。

## Weyl chamber縮約

ここまでで得た$(c_x, c_y, c_z)$は一般に標準のWeyl chamberに属さない。Cirqの`kak_canonicalize_vector`をC++に移植したアルゴリズム[^cirq]で、3種のクラス保存変換を**生成子**として実装し、変換のたびに対応する単一量子ビットCliffordを2×2因子に**吸収**させて、縮約Weyl chamber

$$
\frac{\pi}{4} \ge c_x \ge c_y \ge |c_z| \ge 0,\qquad c_z \ge 0 \text{ if } c_x = \frac{\pi}{4}
$$

に折り畳む。

[^cirq]: `cirq-core/cirq/linalg/decompositions.py`, [Cirq](https://github.com/quantumlib/Cirq), Apache-2.0.

決定論的なシーケンスで:

1. 各$c_k$を$(-\pi/4, \pi/4]$に収める（`canonical_shift`）
2. $|c_0| \ge |c_1| \ge |c_2|$になるようバブルソート
3. $c_0 < 0$なら`negate(0, 2)`（負を$c_2$に逃がす）
4. $c_1 < 0$なら`negate(1, 2)`
5. $c_2$を再フォールド
6. 半端境界tiebreak（$c_x = \pi/4$面で$c_z \ge 0$を強制）

各操作で対応するCliffordを左右の2×2因子に左乗・右乗することで$U = K \cdot \exp(\mathrm{i}\,\vec{c}\cdot\vec{\Sigma}) \cdot K'$がグローバル位相を除いて不変に保たれる。

## 具体例

### CNOT

$$
\mathrm{CNOT} = |0\rangle\langle 0| \otimes I + |1\rangle\langle 1| \otimes \sigma_x
$$

直接計算で$\mathrm{CNOT} \sim \mathrm{e}^{\mathrm{i}(\pi/4)\sigma_{1x}\sigma_{2x}}$が示せる（局所ユニタリで$\sigma_{1x}\sigma_{2z} \to \sigma_{1x}\sigma_{2x}$に変換）。よって正準クラスベクトルは

$$
(c_x, c_y, c_z) = \left(\frac{\pi}{4}, 0, 0\right)
$$

Weyl chamberでは辺$OA_1$の中点$B$に位置する。

### SWAP

$\sigma_{1x}\sigma_{2x}, \sigma_{1y}\sigma_{2y}, \sigma_{1z}\sigma_{2z}$の積関係を用いると

$$
\mathrm{SWAP} = \mathrm{e}^{-\mathrm{i}\pi/4}\,\exp\!\left(\mathrm{i}\,\frac{\pi}{4}(\sigma_{1x}\sigma_{2x} + \sigma_{1y}\sigma_{2y} + \sigma_{1z}\sigma_{2z})\right)
$$

正準クラスベクトルは$(\pi/4, \pi/4, \pi/4)$、Weyl chamberの頂点$A_3$。$\det(\mathrm{SWAP}) = -1$なのでSWAP自身は$SU(4)$には属さないが、$\mathrm{e}^{\mathrm{i}\pi/4}\mathrm{SWAP} \in SU(4)$である。

数値計算的には$N = M^T M = -\mathrm{i}\,I$となり全固有値が縮退する特殊ケース。実装では「$M$がmagic基底で対角」となる入力を統一的に検出する**diagonal-M bypass**を用いる[^diag-bypass]。

[^diag-bypass]: $|M[r, c]|_\mathrm{max\ off\text{-}diag} < 10^{-10}$なら$V = I$とおき、$d_k = \arg(M[k, k])$を直接読む。SWAP頂点（$N \propto I$）だけでなくWeyl chamberの境界（$c_x = c_y$等で2段eighの縮退部分空間が曖昧）まで統一的に処理できる。

### $\sqrt{\mathrm{CNOT}}$

CNOTの議論から自然に$\sqrt{\mathrm{CNOT}} \sim \mathrm{e}^{\mathrm{i}(\pi/8)\sigma_{1x}\sigma_{2x}}$。正準クラスベクトルは$(\pi/8, 0, 0)$、線分$OB$の中点。

## 最適回路構成

### $SO(4)$ゲート: 2 CNOT

$U \in SO(4)$ならば$\mathcal{B} U \mathcal{B}^\dagger = A \otimes C$。Magic基底変換$\mathcal{B}$は1個のCNOTで実現できる[^vw04]ので、$SO(4)$ゲートは

$$
U = \underbrace{\mathcal{B}^\dagger}_\text{1 CNOT}\,(A \otimes C)\,\underbrace{\mathcal{B}}_\text{1 CNOT}
$$

合計**2 CNOT + 12個の1量子ビットゲート**で実現される。

### $SU(4)$ゲート: 3 CNOT

一般の$U \in SU(4)$ではKAK分解と中央の正準ユニタリ$U_d(c_x, c_y, c_z) = \exp(\mathrm{i}(c_x\sigma_{1x}\sigma_{2x} + c_y\sigma_{1y}\sigma_{2y} + c_z\sigma_{1z}\sigma_{2z}))$の構成を組み合わせる。HadamardとCZの恒等式と隣接CNOTの打ち消しを用いて整理すると、$U_d(c_x, c_y, c_z)$は2 CNOTで、左右の局所ゲートと合わせて合計**3 CNOT + 15個の1量子ビットゲート**で任意の$U \in SU(4)$が実現される。

### CNOT数の最適性

> **定理**（Vatan--Williams[^vw04]）: SWAPゲートの実現には少なくとも3個のCNOTが必要である。

証明には**エンタングリングパワー** $\mathrm{EP}(U)$を用いる:

$$
\mathrm{EP}(U) = \mathop{\mathrm{average}}_{|\psi_1\rangle \otimes |\psi_2\rangle} \left[E(U|\psi_1\rangle \otimes |\psi_2\rangle)\right]
$$

ここで$E$は線形エントロピーによるエンタングルメント測度。基本性質:

- $0 \le \mathrm{EP}(U) \le 2/9$
- **局所不変**: $\mathrm{EP}((A \otimes B)U) = \mathrm{EP}(U(A \otimes B)) = \mathrm{EP}(U)$
- $\mathrm{EP}(A \otimes B) = 0$
- $\mathrm{EP}(\mathrm{CNOT}) = 2/9$, $\mathrm{EP}(\mathrm{SWAP}) = 0$

**証明**（背理法）: SWAPが2 CNOT以下で実現できると仮定する。

**1 CNOTの場合**: $\mathrm{SWAP} = (A_1 \otimes A_2)\,\mathrm{CNOT}\,(A_3 \otimes A_4)$とすると、局所不変性より$\mathrm{EP}(\mathrm{SWAP}) = \mathrm{EP}(\mathrm{CNOT}) = 2/9$。しかし$\mathrm{EP}(\mathrm{SWAP}) = 0$なので矛盾。

**2 CNOTの場合**: 各CNOTをCZに置換し、$R_z$とCZの可換関係で整理すると、中央の非局所部分は$U = \mathrm{CZ} \cdot (R_y(a) \otimes R_y(b)) \cdot \mathrm{CZ}$の形になる。エンタングリングパワーは

$$
\mathrm{EP}(U) = \frac{1}{18}(3 - \cos 2a - \cos 2b - \cos 2a \cos 2b)
$$

$\mathrm{EP}(\mathrm{SWAP}) = 0$から$a, b \in \{0, \pi\}$、すべての場合で$U$が局所演算に退化し$\mathrm{SWAP} = V_1 \otimes V_2$となるが、SWAPはテンソル積で表せないため矛盾。$\square$

したがって3 CNOTは一般の2量子ビットゲートに対して**最適**である。

### Chamber位置別分岐

実装では[^impl]、縮約Weyl chamber内の$(c_x, c_y, c_z)$の位置に応じて0/1/2/3 CNOTを使い分ける（Cirqの閉形式から移植）:

|位置|対応クラス| CNOT数|
| --- | --- | --- |
| $c_x = c_y = c_z = 0$ |恒等| 0 |
| $c_x = \pi/4$, $c_y = c_z = 0$ | CNOT類| 1 |
| $c_z = 0$面（上記以外）| $SO(4)$類| 2 |
| chamber内点|一般$SU(4)$ | 3 |

[^impl]: 1 CNOT分岐の述語は他より厳しく$5 \times 10^{-10}$（zero軸testの$10^{-9}$より約2倍狭い）に設定している。1 CNOTは$(\pi/4, 0, 0)$以外のクラスを実現できないため、内点を1 CNOT分岐に誤ルーティングすると間違ったユニタリを出力するためである。一方2 CNOT分岐への誤ルーティングではユニタリ誤差が$|c_z|$自身で抑えられるため、緩いtoleranceを使う。

## PythonによるPoC

ここまでのアルゴリズムをnumpy/scipyで実装する。中核は以下の5ステップ:

```python
import numpy as np
from scipy.linalg import eigh

B = (1 / np.sqrt(2)) * np.array([
    [1,  1j, 0,  0 ],
    [0,  0,  1j, 1 ],
    [0,  0,  1j, -1],
    [1, -1j, 0,  0 ],
])

def kak_decompose(U):
    # 1. SU(4)正規化
    U = U / np.linalg.det(U) ** 0.25
    # 2. magic基底へ
    M = B.conj().T @ U @ B
    # 3. N = M^T M（転置）
    N = M.T @ M
    # 4. Hermitianトリック+ cluster-restricted 2段eighでVを求める
    V = simultaneous_eigenbasis(N)
    # 5. slot encodingから(cx, cy, cz)
    d = np.angle(np.diag(V.conj().T @ N @ V)) / 2
    cx = (d[0] + d[2]) / 2
    cy = (d[1] + d[2]) / 2
    cz = (d[0] + d[1]) / 2
    # ... K1, K2復元+テンソル積分解+ Weyl chamber縮約...
    return cx, cy, cz, K1L, K1R, K2L, K2R
```

実装全体は[こちら](https://github.com/ultimatile/Zenn/tree/main/programs/intro-kak-decomposition)に置いた。代表的な入力での出力:

```
Identity:           (cx, cy, cz) = (0,        0,        0       )    err = 0
CNOT:               (cx, cy, cz) = (π/4,      0,        0       )    err = 2.3e-16
sqrt(CNOT):         (cx, cy, cz) = (π/8,      0,        0       )    err = 8.8e-16
SWAP·e^(iπ/4):      (cx, cy, cz) = (π/4,      π/4,      π/4     )    err = 3.6e-16
random SU(4):       (cx, cy, cz) = ...任意のchamber内点...      err < 2e-14
```

100個のHaarランダム$SU(4)$と、$H_1$が3重縮退する$(\pi/8, \pi/8, c)$resonance ridge上のdressed入力20個でround-trip誤差$< 10^{-9}$を確認できる。

## おわりに

KAK分解は2量子ビットゲートを「3パラメータの非局所部分」と「12パラメータの局所部分」に分離し、CNOT数の上限・下限を体系的に議論する基盤を与える。Cartan分解という抽象的な数学的構造が、量子回路コンパイルという具体的な工学問題に直結している好例といえる。

実装は数値的には自明でなく、特に縮退点での`eigh`固有空間の自由度の取り扱い（cluster-restricted 2段eigh、diagonal-M bypass）が要点となる。

## 参考文献

- F. Vatan, C. Williams, "Optimal quantum circuits for general two-qubit gates", Phys. Rev. A **69**, 032315 (2004). arXiv: [quant-ph/0308006](https://arxiv.org/abs/quant-ph/0308006).
- S.S. Bullock, I.L. Markov, "An arbitrary two-qubit computation in 23 elementary gates or less", Phys. Rev. A **68**, 012318 (2003). arXiv: [quant-ph/0211002](https://arxiv.org/abs/quant-ph/0211002).
- R.R. Tucci, "An Introduction to Cartan's KAK Decomposition for QC Programmers", arXiv: [quant-ph/0507171](https://arxiv.org/abs/quant-ph/0507171).
- N. Khaneja, R. Brockett, S.J. Glaser, Phys. Rev. A **63**, 032308 (2001).
- Qiskit `TwoQubitWeylDecomposition`実装.
- Cirq `kak_canonicalize_vector`実装. `cirq-core/cirq/linalg/decompositions.py`, [Cirq](https://github.com/quantumlib/Cirq) (Apache-2.0).
