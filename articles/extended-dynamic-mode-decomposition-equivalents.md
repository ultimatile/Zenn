---
title: "拡張ダイナミックモード分解と等価な手法たち"
emoji: "🦀"
type: "idea" # tech: 技術記事 / idea: アイデア
topics: ["dmd","koopman"]
published: false
---

## はじめに

拡張動的モード分解(Extended Dynamic Mode Decomposition; EDMD)はデータ駆動非線形時系列解析の手法として人気がある方法です。

原論文は Williams, Kevrekidis, Rowley (2015)[^edmd]で、流体力学の文脈で提案されました。

しかし2015年は遅すぎます。
EDMDと**数学的に等価な手法**は、信号処理、分子動力学、統計物理など様々な分野ではるか以前から使われており、EDMDは再発見に過ぎません。
EDMD論文の意義は、これら異分野で独立に使われてきたKoopman的手法に対して、**Koopman作用素の有限次元近似**という統一的な見方を提供したことにあると考えています。

以下ではまずEDMDの定式化を紹介し、その後、EDMDと等価（あるいは特殊ケースの関係にある）手法を紹介します。

## 拡張動的モード分解(EDMD)の定式化

### Koopman作用素

離散時間の自律的力学系 $(\mathcal{M}, n, \bm{F})$ を考えます。ここで $\mathcal{M} \subseteq \mathbb{R}^N$ は状態空間、$\bm{F}: \mathcal{M} \to \mathcal{M}$ は時間発展演算子です。

Koopman作用素 $\mathcal{K}$ は、状態空間上の**関数（オブザーバブル）** $\phi: \mathcal{M} \to \mathbb{C}$ に作用する線形作用素で、

$$

\mathcal{K}\phi = \phi \circ \bm{F}

$$

と定義されます。$\bm{F}$ が非線形でも $\mathcal{K}$ は線形です。ただし一般には無限次元になります。

### EDMDのアルゴリズム

EDMDは以下の2つを入力とします。

1. **スナップショット対のデータ**: $\{(\bm{x}_m, \bm{y}_m)\}_{m=1}^M$ ただし $\bm{y}_m = \bm{F}(\bm{x}_m)$
2. **辞書（基底関数の集合）**: $\mathcal{D} = \{\psi_1, \psi_2, \ldots, \psi_K\}$

辞書関数をまとめてベクトル値関数として

$$

\bm{\Psi}(\bm{x}) = \begin{bmatrix} \psi_1(\bm{x}) & \psi_2(\bm{x}) & \cdots & \psi_K(\bm{x}) \end{bmatrix}

$$

と定義します。

Koopman作用素の有限次元近似行列 $\bm{K} \in \mathbb{C}^{K \times K}$ を、残差

$$

J = \frac{1}{2}\sum_{m=1}^M \left|(\bm{\Psi}(\bm{y}_m) - \bm{\Psi}(\bm{x}_m)\bm{K})\bm{a}\right|^2

$$

の最小化により求めると、

$$

\bm{K} = \bm{G}^{+}\bm{A}

$$

が得られます。ここで ${}^{+}$ は疑似逆行列を表し、

$$

\bm{G} = \frac{1}{M}\sum_{m=1}^M \bm{\Psi}(\bm{x}_m)^{*}\bm{\Psi}(\bm{x}_m), \quad
\bm{A} = \frac{1}{M}\sum_{m=1}^M \bm{\Psi}(\bm{x}_m)^{*}\bm{\Psi}(\bm{y}_m)

$$

です。

$\bm{G}$ が正則なら $\bm{K} = \bm{G}^{-1}\bm{A}$ と書けます。$\bm{G}$ と $\bm{A}$ はそれぞれ辞書関数の**共分散行列**と**時間遅れ共分散行列**のサンプル推定量にほかなりません。

$\bm{K}$ の固有値 $\mu_j$ と固有ベクトル $\bm{\xi}_j$ から、Koopman固有関数の近似が

$$

\varphi_j = \bm{\Psi}\bm{\xi}_j

$$

として得られます。

### 一般化固有値問題としての表現

$\bm{K}$ の固有値問題 $\bm{K}\bm{\xi} = \mu\bm{\xi}$、すなわち $\bm{G}^{-1}\bm{A}\bm{\xi} = \mu\bm{\xi}$ は、**一般化固有値問題**

$$

\bm{A}\bm{\xi} = \mu\,\bm{G}\bm{\xi}

$$

と等価です。共分散行列の記法で書けば

$$

\hat{\bm{C}}(\tau)\bm{b} = \mu\,\hat{\bm{C}}(0)\bm{b}

$$

となります。この形が以降の等価性を見通す上で重要です。

## Prony法

**Prony法**（1795年）[^prony]は、信号処理における最古の手法のひとつで、信号を複素指数関数の和としてフィッティングするものです。

スカラー時系列 $y(0), y(1), \ldots$ が

$$

y(n) = \sum_{k=1}^{K} c_k z_k^n

$$

と表せると仮定します。ここで $z_k = e^{\lambda_k \Delta t}$ は離散時間の固有値（極）、$c_k$ は振幅です。

線形予測の関係式

$$

y(n) + a_1 y(n-1) + \cdots + a_K y(n-K) = 0

$$

から係数 $a_1, \ldots, a_K$ を求め、特性多項式

$$

z^K + a_1 z^{K-1} + \cdots + a_K = 0

$$

の根として $z_k$ を得ます。

### EDMDとの関係

Prony法は本質的に**DMD（Dynamic Mode Decomposition）の1次元版**です。DMDはEDMDにおいて辞書を恒等写像 $\bm{\Psi}(\bm{x}) = \bm{x}$ とした場合に対応します。

さらに、遅延座標 $(y(n), y(n+1), \ldots, y(n+K-1))$ をEDMDの辞書として用いると、EDMDの一般化固有値問題はProny法の極を求める問題と本質的に等価になります。

## 行列束法

**行列束法**（Matrix Pencil Method; MPM）[^mpm]は、Prony法を一般化し数値的に安定化した手法です。

行列の対 $(Y_1, Y_0)$ から構成される1パラメータ族 $Y_1 - z Y_0$ を行列束（matrix pencil）と呼びます。手法名は操作ではなくこの数学的対象の名前をそのまま冠したもので、何をする手法なのかは名前からは分かりません。

### アルゴリズム

時系列データから2つの行列を構成します:

$$

Y_0 = \begin{bmatrix}
y(0) & y(1) & \cdots & y(L-1) \\
y(1) & y(2) & \cdots & y(L) \\
\vdots & & & \vdots \\
y(N-L-1) & y(N-L) & \cdots & y(N-2)
\end{bmatrix}

$$

$$

Y_1 = \begin{bmatrix}
y(1) & y(2) & \cdots & y(L) \\
y(2) & y(3) & \cdots & y(L+1) \\
\vdots & & & \vdots \\
y(N-L) & y(N-L+1) & \cdots & y(N-1)
\end{bmatrix}

$$

ここで $L$ はペンシルパラメータです。極 $z_k$ は一般化固有値問題

$$

Y_1 \bm{v} = z\, Y_0 \bm{v}

$$

の固有値として得られます。

### EDMDとの関係

行列束法は、**遅延座標を辞書関数としたEDMD**と同じ構造をもちます。

遅延座標 $\bm{\Psi}(\bm{x}_n) = (y(n), y(n+1), \ldots, y(n+L-1))$ を辞書として使えば、EDMDの行列 $\bm{G}$ と $\bm{A}$ はそれぞれ $Y_0^\top Y_0$ と $Y_0^\top Y_1$ に比例し、$\bm{K} = (Y_0^\top Y_0)^{-1}Y_0^\top Y_1$ は行列束法の解と一致します。

Prony法が特性多項式の求根問題を経由するのに対し、行列束法は一般化固有値問題を直接解くため、ノイズに対してはるかにロバストです。EDMDはこの行列束法の構造を、辞書関数を任意に選べる形に一般化したものと見ることができます。

## ESPRIT

**ESPRIT**（Estimation of Signal Parameters via Rotational Invariance Techniques）[^esprit]は、信号部分空間の**回転不変性（shift-invariance）** を利用してスペクトルパラメータを推定する手法です。

### Hankel DMDとの形式的等価性

ESPRITとHankel DMDはどちらも同じHankel行列から出発します。ノイズがない場合、両者は**全く同じ固有値（指数関数の極）を復元する**ことが証明されています[^esprit_dmd]。

- **Hankel DMD**: Hankel行列の時間シフト対 $(H_0, H_1)$ に対し、最小二乗的にKoopman作用素の有限次元近似を構成する
- **ESPRIT**: 信号部分空間 $U_r$ の時間シフトに対する回転不変性 $U_1 = U_0 \Phi$ を利用し、回転行列 $\Phi$ の固有値として極を求める

ノイズなしの極限では両者は等価ですが、アルゴリズムの構造が異なるためノイズに対するロバスト性が違います。ESPRITは回転不変性を陽に課すことで、Hankel DMDよりノイズに強く、少ない指数関数の数でより安定した推定が得られることが報告されています[^esprit_dmd]。

### EDMDとの関係

ESPRITはスカラー時系列を遅延埋め込みしたHankel行列を入力とするため、Prony法や行列束法と同じカテゴリに属します。ノイズなしでの固有値がHankel DMDと一致することから、Koopman固有値の近似という意味でEDMD（遅延座標辞書）と等価です。ただし、固有値の抽出方法が最小二乗（DMD）ではなく部分空間の回転不変性（ESPRIT）である点が本質的に異なります。

## VAC/VAMP

### VAC（Variational Approach for Conformation Dynamics）

**VAC**（変分アプローチ）は、分子動力学シミュレーションの解析のために Noé & Nüske (2013)[^vac_original] が提案した手法です。Wu & Noé (2017)[^vac]ではVACとEDMDの関係が明示的に示されました。

VACは以下の**変分原理**に基づきます: 基底関数 $\boldsymbol{\chi} = (\chi_1, \ldots, \chi_m)$ の線形結合

$$

f_i(\bm{x}) = \bm{b}_i^\top \boldsymbol{\chi}(\bm{x})

$$

によって固有関数を近似するとき、Rayleighトレース

$$

R_m = \sum_{i=1}^{m} \mathbb{E}_\mu[f_i(\bm{x}_t)f_i(\bm{x}_{t+\tau})]

$$

を直交性の制約のもとで最大化すると、**一般化固有値問題**

$$

\bm{C}(\tau)\bm{B} = \bm{C}(0)\bm{B}\hat{\bm{\Lambda}}

$$

が得られます。ここで

$$

\bm{C}(0) = \mathbb{E}_\mu[\boldsymbol{\chi}(\bm{x}_t)\boldsymbol{\chi}(\bm{x}_t)^\top], \quad
\bm{C}(\tau) = \mathbb{E}_\mu[\boldsymbol{\chi}(\bm{x}_t)\boldsymbol{\chi}(\bm{x}_{t+\tau})^\top]

$$

は平衡分布のもとでの共分散行列・時間遅れ共分散行列です。

これは $\bm{K} = \bm{C}(0)^{-1}\bm{C}(\tau)$ の固有値問題と等価であり、**EDMDの Koopman行列と完全に同一**です[^vac]。実際、Wu & Noé (2017) は次のように明記しています:

> The algorithm of the linear VA is identical to more recently proposed extended dynamic mode decomposition (EDMD).

基底関数の選び方によって既知の手法が得られます:
- $\boldsymbol{\chi}(\bm{x}) = \bm{x} - \boldsymbol{\mu}$（平均を引いた座標）→ **TICA**（Time-lagged Independent Component Analysis）
- $\chi_i(\bm{x}) = \mathbb{1}_{A_i}(\bm{x})$（集合の指示関数）→ **マルコフ状態モデル（MSM）**

### VAMP（Variational Approach for Markov Processes）

**VAMP**はWu & Noé (2020)[^vamp]が提案した、VACの**非可逆過程への一般化**です。

VACは可逆（detailed balance を満たす）過程でのKoopman作用素の**固有値分解**に基づきますが、VAMPはKoopman作用素の**特異値分解（SVD）** に基づきます。

Koopman作用素 $\mathcal{K}_\tau$ の特異値分解において、左右の特徴関数 $\bm{f}$, $\bm{g}$ の線形結合で特異関数を近似すると、**VAMP-$r$ スコア**

$$

\mathcal{R}_r[\bm{f}, \bm{g}] = \sum_{i=1}^k \langle f_i, \mathcal{K}_\tau g_i \rangle_{\rho_0}^r

$$

の最大化がアルゴリズムの基礎となります。これは時間遅れ正準相関分析（CCA）と等価です。

可逆過程（$\bm{f} = \bm{g}$、$\bm{C}(\tau)$ が対称）の場合、VAMPはVAC（= EDMD）に帰着します。

## Takano-Miyashita法

**Takano-Miyashita法**は、高野宏と宮下精二が1995年にランダムスピン系の緩和モード解析のために提案した手法です[^tm]。EDMDに**20年先行**しています。

### 定式化

$N$ 個のIsingスピンの系において、緩和モードを**スピンの線形結合**で近似する試行関数

$$

\hat{\phi}(S) = \sum_{i=1}^N f_i S_i(S)

$$

を考えます。平衡状態でのRayleigh商

$$

\Lambda[\hat{\phi}] = \frac{\sum_{i,j} f_i C_{ij}(t) f_j}{\sum_{i,j} f_i C_{ij}(0) f_j}

$$

を最大化すると、**一般化固有値問題**

$$

\sum_{j=1}^N C_{ij}(t) f_j = e^{-\hat{\lambda} t} \sum_{j=1}^N C_{ij}(0) f_j

$$

が得られます。ここで $C_{ij}(t) = \langle S_i(t) S_j(0) \rangle$ はスピン相関行列です。

さらに、速い緩和モードの寄与を抑制する改良法として、試行関数を

$$

\hat{\phi}_\alpha(S) = \sum_{i=1}^N f_{\alpha,i} S_i(t_0/2; S)

$$

に置き換えると、

$$

\sum_{j=1}^N C_{ij}(t_0 + t) f_j = e^{-\hat{\lambda} t} \sum_{j=1}^N C_{ij}(t_0) f_j

$$

という時間シフトした一般化固有値問題が得られます。

### EDMDとの等価性

EDMDの枠組みと対応づけると:

| Takano-Miyashita法 | EDMD |
|---|---|
| スピン $S_i$ | 辞書関数 $\psi_i$ |
| スピン相関行列 $C_{ij}(0)$ | 共分散行列 $\bm{G}$ |
| 時間遅れ相関行列 $C_{ij}(t)$ | 時間遅れ共分散行列 $\bm{A}$ |
| 緩和因子 $e^{-\hat{\lambda}t}$ | Koopman固有値 $\mu$ |
| 一般化固有値問題 $C(t)f = \sigma C(0)f$ | $\bm{A}\bm{\xi} = \mu\,\bm{G}\bm{\xi}$ |

スピンを辞書関数とみなせば、Takano-Miyashita法はEDMDそのものです。

### VAMPとの等価性

平衡可逆ダイナミクスのもとでは[^equiv]:

- detailed balanceにより $C_{00} = C_{11} = C(0)$、$C_{01} = C(t)$ が対称となる
- VAMPのSVDはKoopman作用素の固有値分解に帰着する
- 結果として得られる $C(t)f = \sigma C(0)f$ はTakano-Miyashita法の固有値問題と完全に一致（$\sigma = e^{-\hat{\lambda}t}$）

つまりTakano-Miyashita法は、**可逆極限でのVAMP/TCCA（= VAC/TICA = EDMD）をスピン基底に適用したもの**と完全に等価です。

## まとめ

EDMDの核心は、辞書関数の共分散行列と時間遅れ共分散行列を用いた一般化固有値問題

$$

\bm{C}(\tau)\bm{b} = \mu\,\bm{C}(0)\bm{b}

$$

にあります。この同一の数学的構造が、異なる分野で独立に発見されてきました。

| 手法 | 分野 | 年代 | 辞書（基底）の選択 |
|---|---|---|---|
| Prony法 | 信号処理 | 1795 | 遅延座標（単項式） |
| ESPRIT | 信号処理 | 1986 | 遅延座標（部分空間回転不変性） |
| 行列束法 | 電気工学 | 1990頃 | 遅延座標 |
| Takano-Miyashita法 | 統計物理 | 1995 | スピン変数 |
| VAC/TICA | 分子動力学 | 2013 | 分子座標・特徴量 |
| EDMD | 流体力学 | 2015 | 任意の辞書関数 |
| VAMP | 分子動力学 | 2017 | 任意（非可逆への一般化） |

EDMDは新しい数学を生み出したわけではありません。しかし「Koopman作用素の有限次元近似」という統一的な解釈を与え、辞書関数の選択という設計自由度を明示したことで、異分野の手法を横断的に理解する枠組みを提供しました。

[^edmd]: M.O. Williams, I.G. Kevrekidis, C.W. Rowley, "A Data-Driven Approximation of the Koopman Operator: Extending Dynamic Mode Decomposition," J. Nonlinear Sci. 25, 1307-1346 (2015). [arXiv:1408.4408](https://arxiv.org/abs/1408.4408)
[^prony]: G.R. de Prony, "Essai expérimental et analytique," J. de l'École Polytechnique 1, 24-76 (1795).
[^esprit]: R. Roy and T. Kailath, "ESPRIT — Estimation of Signal Parameters via Rotational Invariance Techniques," IEEE Trans. Acoust. Speech Signal Process. 37, 984-995 (1989).
[^esprit_dmd]: J. Huber et al., "Compact representation and long-time extrapolation of real-time data for quantum systems using the ESPRIT algorithm," (2025). [arXiv:2506.13760](https://arxiv.org/abs/2506.13760)
[^mpm]: Y. Hua and T.K. Sarkar, "Matrix Pencil Method for Estimating Parameters of Exponentially Damped/Undamped Sinusoids in Noise," IEEE Trans. Acoust. Speech Signal Process. 38, 814-824 (1990).
[^vac_original]: F. Noé and F. Nüske, "A variational approach to modeling slow processes in stochastic dynamical systems," Multiscale Model. Simul. 11, 635-655 (2013).
[^vac]: H. Wu and F. Noé, "Variational Koopman models: slow collective variables and molecular kinetics from short off-equilibrium simulations," J. Chem. Phys. 146, 154104 (2017). [arXiv:1610.06773](https://arxiv.org/abs/1610.06773)
[^vamp]: H. Wu and F. Noé, "Variational approach for learning Markov processes from time series data," J. Nonlinear Sci. 30, 23-66 (2020). [arXiv:1707.04659](https://arxiv.org/abs/1707.04659)
[^tm]: H. Takano and S. Miyashita, "Relaxation Modes in Random Spin Systems," J. Phys. Soc. Jpn. 64, 3688-3698 (1995).
[^equiv]: 等価性の詳細な導出はこの記事のスコープ外ですが、可逆・定常ダイナミクスでの線形特徴量に制限した場合の Takano-Miyashita法とVAMPの数学的等価性を確認しています。
