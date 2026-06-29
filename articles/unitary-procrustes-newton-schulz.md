---
title: "Newton-Schulz法によるユニタリProcrustes問題の反復解法"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["線形代数", "深層学習"]
published: false
register: joutai
---

## はじめに

前回の記事では、ユニタリProcrustes問題の（特殊形の）解が特異値分解で得られることを示した。これは直接法に分類される^[厳密には特異値分解に反復解法を使用すると反復法となる。]。今回は、同じ解を行列積だけからなる反復で近似するNewton-Schulz法を紹介する。後で見るように計算量のオーダー自体は特異値分解と変わらないが、計算が行列積に集約されるためGPUなどの並列計算機で高速に回せ、低精度で十分な場面では少数回の反復で済む。この性質から、Newton-Schulz法は深層学習のオプティマイザ [Muon](https://kellerjordan.github.io/posts/muon/) の中核となる演算として使われている。

## ユニタリProcrustes問題の定式化

前回の記事で示したように、与えられた $B \in \mathbb{C}^{n\times n}$ に対してFrobeniusノルムで最も近いユニタリ行列は

$$
A_\mathrm{opt} = \argmin_{\{A \mid A^\dagger A = AA^\dagger = I_n\}} \|A - B\|_\mathrm{F}^2 = UV^\dagger
$$

で与えられる。ただし $B = U\Sigma V^\dagger$ は $B$ の特異値分解とする。

この $UV^\dagger$ は $B$ の[極分解](https://en.wikipedia.org/wiki/Polar_decomposition)におけるユニタリ因子である。実際 $B = U\Sigma V^\dagger = (UV^\dagger)(V\Sigma V^\dagger)$ と分けると、$Q := UV^\dagger$ はユニタリ、$H := V\Sigma V^\dagger$ はエルミート半正定値となり、$B = QH$ はまさに極分解である。したがってユニタリProcrustes問題を解くことは、$B$ のユニタリ極因子 $Q$ を求めることと等価である。

ここで $Q = UV^\dagger$ の見方を一つ与えておく。$UV^\dagger = U I_n V^\dagger$ は、$B = U\Sigma V^\dagger$ の特異値（$\Sigma$ の対角成分）をすべて $1$ に置き換え、特異ベクトル $U, V$ はそのまま残した行列である。この特徴づけは後の収束性解析で使う。次節では、特異値分解を陽に計算せず $Q$ へ至る反復を、直交性からのずれの最小化として導く。

## Newton-Schulz法

$Q$ は $Q^\dagger Q = I_n$ を満たすユニタリ行列であった。そこで、$B$ から出発して直交性 $X^\dagger X = I_n$ からのずれを縮める方向に $X$ を動かすことを考える。ずれを測る目的函数

$$
f(X) = \frac{1}{4}\left\|X^\dagger X - I_n\right\|_\mathrm{F}^2
$$

を最小化する勾配降下から、Newton-Schulz反復が導かれる。

::: details 勾配の導出

$X^\dagger X - I_n$ はエルミートなので $f(X) = \frac{1}{4}\operatorname{tr}\!\big((X^\dagger X - I_n)^2\big)$ である。$M := X^\dagger X - I_n$ とおくと $dM = (dX)^\dagger X + X^\dagger dX$ なので、

$$
df = \frac{1}{2}\operatorname{tr}(M\,dM) = \operatorname{Re}\operatorname{tr}\!\big((XM)^\dagger dX\big)
$$

となる。よって（正の実数倍を除いて）勾配は $\nabla f = X(X^\dagger X - I_n)$ である。

:::

勾配降下のステップは、ステップ幅 $\eta$ を用いて

$$
X_{k+1} = X_k - \eta\,X_k(X_k^\dagger X_k - I_n) = X_k + \eta\,X_k(I_n - X_k^\dagger X_k)
$$

と書ける。ここで $\eta = \dfrac{1}{2}$ ととると

$$
X_{k+1} = \frac{1}{2}X_k\left(3 I_n - X_k^\dagger X_k\right), \qquad X_0 = \frac{B}{\alpha}
$$

が得られる。これがNewton-Schulz反復である。$\alpha$ は後述の収束条件を満たすように選ぶスケーリング定数で、$X_0$ を $B$ に比例させて初期値の特異ベクトルを $B$ と揃える。この反復は逆行列も特異値分解も含まず、行列積のみで計算できる[^higham]。$\eta = \frac{1}{2}$ という値は単なる一例でなく、収束性の節で見るように2次収束を与える特別な選択である。

なお目的函数を $\|XX^\dagger - I_n\|_\mathrm{F}^2$ の側にとると左乗法形 $\frac{1}{2}(3 I_n - X_kX_k^\dagger)X_k$ が出るが、$X(3 I_n - X^\dagger X) = (3 I_n - XX^\dagger)X$ なので正方行列では一致する。

1反復の計算量は、$X_k^\dagger X_k$ と $X_k(3 I_n - X_k^\dagger X_k)$ の2回の行列積からなり $O(n^3)$、$T$ 反復で $O(T n^3)$ である。特異値分解も $O(n^3)$ なのでオーダーは下がらない。Newton-Schulz法の利点はオーダーの低減ではなく、計算が行列積へ集約され並列計算機で高速に回せる点である。

この反復が特異ベクトルを保存することを確認する。

::: details 特異ベクトルが保存されることの確認

$X_k$ の特異値分解を $X_k = U\Sigma_k V^\dagger$ とおく。$X_k^\dagger X_k = V\Sigma_k^2 V^\dagger$ なので、

$$
X_{k+1} = \frac{1}{2}U\Sigma_k V^\dagger \cdot V\left(3 I_n - \Sigma_k^2\right)V^\dagger = U\left[\frac{1}{2}\Sigma_k\left(3 I_n - \Sigma_k^2\right)\right]V^\dagger
$$

となる。$U, V$ は $k$ に依らず一定で、各特異値 $\sigma$ だけが

$$
g(\sigma) = \frac{1}{2}\sigma\left(3 - \sigma^2\right)
$$

に従って更新される。反復が $X_k$ の奇数次のべき（$X_k$ と $X_k X_k^\dagger X_k$）のみで書ける、すなわち $g$ が奇函数であることがこの特異ベクトル保存の理由である。

:::

したがって反復全体は、各特異値に対するスカラー写像 $\sigma_{k+1} = g(\sigma_k)$ に帰着する。$\sigma = 1$ はこの写像の不動点であり（$g(1) = \frac{1}{2}\cdot 1\cdot(3-1) = 1$）、すべての特異値が $1$ に収束すれば

$$
X_k \to U I_n V^\dagger = UV^\dagger = A_\mathrm{opt}
$$

となる。

## 収束性とスケーリング

不動点 $\sigma = 1$ の近傍での収束の速さは $g'(\sigma) = \frac{3}{2}(1 - \sigma^2)$ からわかる。$g'(1) = 0$ なので $\sigma = 1$ は2次収束の不動点である。実際 $\epsilon_k := \sigma_k - 1$ とおいて展開すると、

$$
\sigma_{k+1} - 1 = -\frac{1}{2}\epsilon_k^2(\sigma_k + 2)
$$

が成り立ち^[$g(1+\epsilon) = \frac{3}{2}(1+\epsilon) - \frac{1}{2}(1+\epsilon)^3 = 1 - \frac{3}{2}\epsilon^2 - \frac{1}{2}\epsilon^3 = 1 - \frac{1}{2}\epsilon^2(3+\epsilon)$ であり、$3+\epsilon = \sigma_k + 2$ である。]、誤差が各ステップで2乗されていくため収束は速い。

この2次収束は、前節でステップ幅を $\eta = \frac{1}{2}$ にとったことの帰結である。一般の $\eta$ では各特異値の写像は $g_\eta(\sigma) = \sigma + \eta\,\sigma(1 - \sigma^2)$ となり、不動点 $\sigma = 1$ での微分は $g_\eta'(1) = 1 - 2\eta$ である。これが $0$ になって2次収束するのは $\eta = \frac{1}{2}$ のときに限り、$\eta < \frac{1}{2}$ なら $g_\eta'(1) \in (0, 1)$ で1次収束にとどまる。直交化欠損の勾配降下という見方とNewton法由来の2次収束は、この $\eta = \frac{1}{2}$ で結びつく。本文の $g$ はまさに $g_{1/2}$ である。

一方で、初期の特異値が $1$ から離れすぎていると収束しない。収束する初期値の範囲は次の通りである。

::: details 収束域が $(0, \sqrt{3})$ であることの確認

$g(\sigma) = \frac{1}{2}\sigma(3 - \sigma^2)$ は $\sigma \in (0, \sqrt{3})$ で正、$\sigma = \sqrt{3}$ で $0$、$\sigma > \sqrt{3}$ で負である。$(0, \sqrt{3})$ 上での最大値は $\sigma = 1$ における $g(1) = 1$ なので、$g$ は $(0, \sqrt{3})$ を $(0, 1]$ に写す。さらに $(0, 1]$ 上では

$$
g(\sigma) - \sigma = \frac{1}{2}\sigma(1 - \sigma^2) \geq 0
$$

であり、$g$ は単調増加で上限 $1$ に向かうため、$\sigma = 1$ に収束する。逆に初期値が $\sqrt{3}$ を超えると $g(\sigma) < 0$ となって特異値の符号が反転し、発散する。

:::

よって反復が収束するのは、$X_0 = B/\alpha$ のすべての特異値が $(0, \sqrt{3})$ に入る場合である。最大特異値について $\sigma_{\max}(B)/\alpha < \sqrt{3}$、すなわち $\alpha > \sigma_{\max}(B)/\sqrt{3}$ であればよい。最大特異値そのもの（$=\|B\|_2$）を求めると結局特異値分解が要るので、実用上は安価に計算できる $\alpha = \|B\|_\mathrm{F}$ を使う。$\|B\|_\mathrm{F} = \sqrt{\sum_i \sigma_i^2} \geq \sigma_{\max}(B)$ より $X_0$ の最大特異値は $1$ 以下となり、収束域 $(0, \sqrt{3})$ へ確実に収まる。

なお最小特異値が $0$（$B$ が特異）の場合、その特異値は $g(0) = 0$ のまま動かず $1$ に到達しない。これは極分解のユニタリ因子が一意に定まらない状況を表す。以下では $B$ は正則とする。

## 正確に計算するなら

正確な解が必要なら、素のNewton-Schulzより、極分解を頑健に計算する反復を使うほうがよい。NVIDIAの [cuSOLVER](https://docs.nvidia.com/cuda/cusolver/) には極分解を経由するSVDルーチン `cusolverDnXgesvdp` があり、極分解 $B = QH$ を求めてから $H$ をエルミート固有値分解してSVDを組み立てる。ドキュメントによれば、QR分解ベースの `gesvd` より大幅に速いとされる。

ここで使われる反復は本記事の素のNewton-Schulzではなく、QDWH（QRベースの動的重み付きHalley反復）である[^qdwh]。QDWHは3次収束で高々約6反復、悪条件やランク落ちにも頑健で、$\sigma \approx 0$ 付近でも摂動を入れて対処する。素のNewton-Schulzは $\sigma \approx 0$ で収束が鈍く、スケーリングを誤ると発散する（収束域 $(0, \sqrt{3})$）ため、正確なSVD計算にはこうした頑健な反復が用いられる。

## Muonにおける近似直交化

素のNewton-Schulzが活きるのは、正確さより速さが優先される低精度の直交化である。深層学習のオプティマイザ [Muon](https://kellerjordan.github.io/posts/muon/)（MomentUm Orthogonalized by Newton-Schulz）は、行列パラメータの勾配モメンタム $M$ を直交化してから更新する。ここでの直交化は $M$ に最も近い直交行列を求める操作で、本記事のユニタリProcrustes問題（実行列なら直交Procrustes問題）そのものである。Muonはこの直交化を、特異値分解ではなくNewton-Schulz反復で近似する。

ただしMuonが使うのは本記事の3次反復ではなく、係数を調整した5次の変種である（$M$ は実行列なので随伴 $\dagger$ は転置 $\top$ になる）。

$$
X_{k+1} = a X_k + b\,(X_k X_k^\top)X_k + c\,(X_k X_k^\top)^2 X_k, \qquad (a, b, c) = (3.4445,\ -4.7750,\ 2.0315)
$$

特異値へのスカラー写像は $\phi(x) = ax + bx^3 + cx^5$ である[^muon]。これも $X_k$ の奇数次多項式なので、本記事と同じく特異ベクトルを保存し、特異値だけに $\phi$ が作用する。違いは係数の振り方にある。

- 本記事の3次 $\phi(x) = \frac{3}{2}x - \frac{1}{2}x^3$ は $\phi(1) = 1$、$\phi'(1) = 0$ で、特異値を $1$ へ2次収束させる正確志向の選択である。
- Muonの5次は初項の傾きを $a = 3.4445$ と大きくとり、小さい特異値を一気に $1$ 付近へ持ち上げる。代わりに $\phi(1) = 0.701$ で $1$ すら不動点でなく、約5反復で特異値を $[0.7, 1.3]$ 程度の帯へ押し込めば十分という割り切りになっている。

この係数の決め方も、Jordanのブログでは極限 $\lim_{N\to\infty}\phi^N(x)$ が $[0.7, 1.3]$ に入るという制約のもとで $a$ を最大化する、として与えている。$\varepsilon \approx 0.3$ までの不正確さは損失曲線を悪化させない、という観察が根拠である。$a$ が大きいほど小さい特異値が速く持ち上がるので、少数反復で済む。

正確さを捨てて少数ステップを取れるのは、勾配の前処理という用途では極因子を正確に求める必要がないからである。低精度で回せて、行列積だけなので学習ループ内で微分可能なまま高速に実行できることのほうが優先される。

## まとめ

ユニタリProcrustes問題の解 $A_\mathrm{opt} = UV^\dagger$ は $B$ のユニタリ極因子であり、特異値分解を陽に計算せずとも、行列積のみからなるNewton-Schulz反復

$$
X_{k+1} = \frac{1}{2}X_k\left(3 I_n - X_k^\dagger X_k\right), \qquad X_0 = \frac{B}{\|B\|_\mathrm{F}}
$$

で求められる。この反復は $B$ の特異値を $1$ へ2次収束で近づけ、$X_k \to A_\mathrm{opt}$ となる。計算量のオーダーは特異値分解と同じ $O(n^3)$ で、利点はオーダーの低減ではなく計算が行列積へ集約される点にある。正確な極分解やSVDが必要なら、頑健なQDWHを使う cuSOLVER `gesvdp` のような実装が適し、素のNewton-Schulzが活きるのは、低精度で十分かつ微分可能性や少数反復が効く、Muonのような直交化である。

## 余談: 直交化の精度と学習

最後に与太話を一つ。X上で、Muonの直交化をNewton-SchulzよりさらにSVDに近い精度の方法（[Polar Express](https://arxiv.org/abs/2505.16932) など）で行うと、かえって検証損失が悪化したという観察が報告されている。直交化に乗るノイズがむしろ学習に効いているのではないか、という見立てである。

個人の観察で裏付けのある結果ではない。ただ、$\varepsilon \approx 0.3$ までの不正確さは損失を悪化させないというJordanのブログの観察とは整合的で、それを「不正確さは無害」から「不正確さはむしろ有益」へ一歩進めた格好になっている。なぜ荒い直交化で足りるどころか有利になりうるのか、と考えると興味深い。

@[tweet](https://x.com/Creative_Math_/status/2067406111485854079)

[^qdwh]: QDWHとそれによるSVD・固有値分解の構成は Y. Nakatsukasa, Z. Bai, F. Gygi, "Optimizing Halley's Iteration for Computing the Matrix Polar Decomposition," SIAM J. Matrix Anal. Appl. 31(5):2700–2720 (2010) および Y. Nakatsukasa and N. J. Higham, "Stable and Efficient Spectral Divide and Conquer Algorithms for the Symmetric Eigenvalue Decomposition and the SVD," SIAM J. Sci. Comput. 35(3):A1325–A1349 (2013) を参照。

[^muon]: 係数と「$1$ へ厳密に収束させず帯に収める」設計の根拠は [Keller Jordan のブログ記事](https://kellerjordan.github.io/posts/muon/)を参照。

[^higham]: ユニタリ極因子を反復で求める手法とその収束性については N. J. Higham, _Functions of Matrices: Theory and Computation_, SIAM (2008) の8章を参照。
