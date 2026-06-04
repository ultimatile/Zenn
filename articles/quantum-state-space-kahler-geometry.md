---
title: "量子状態空間としての複素射影空間とKähler幾何"
emoji: "🧭"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["量子力学", "微分幾何", "複素幾何"]
published: false
---

## はじめに

量子力学で状態ベクトルを扱うとき、最初に出てくる空間は複素Hilbert空間です。
有限次元だけを考えるなら、これはほとんど$\mathbb{C}^N$です。

しかし物理的な純粋状態はベクトルそのものではありません。
ゼロでない複素数倍だけ違う状態ベクトルは同じ物理状態を表します。
特に規格化済みの状態では、全体位相

$$
|\psi\rangle \sim e^{i\theta}|\psi\rangle
$$

を同一視します。
したがって、量子状態の本当の空間は複素射影空間

$$
\mathbb{C}P^{N-1}
$$

です。

この記事では、有限次元の複素内積空間から出発して、$\mathbb{C}^N$と$\mathbb{C}P^{N-1}$に現れる幾何を見ます。
特にFubini-Study計量、Quantum Geometric Tensor、変分アンサッツ多様体、等質空間、シンプレクティック形式、複素構造、Kähler構造の関係を整理します。

抽象的なKähler多様体一般の理論には入りません。
主役はあくまで

$$
\mathbb{C}^N,\qquad \mathbb{C}P^{N-1}
$$

です。

:::message
この記事では有限次元のHilbert空間だけを扱います。
無限次元Hilbert空間や場の理論で現れる函数解析的な問題は扱いません。
:::

## 幾何の最小限の言葉

先に、この記事で使う幾何学の言葉を最小限だけ整理します。
厳密な定義をすべて展開すると微分幾何の入門になってしまうので、ここでは$\mathbb{C}^N$と$\mathbb{C}P^{N-1}$を読むために必要な範囲に限ります。

### 多様体と接空間

まず多様体とは、局所的には$\mathbb{R}^m$のように見える空間です。
各点の近くに座標を入れて、微分や接ベクトルを考えられる空間だと思えばよいです。
多様体$M$の点$p$における接空間を$T_pM$と書きます。

### Riemann計量

Riemann計量とは、各接空間$T_pM$に内積を入れたものです。
接ベクトル$u,v\in T_pM$に対して

$$
g_p(u,v)
$$

という実対称な正定値双線形形式を与えます。
これにより、接ベクトルの長さ、曲線の長さ、距離、勾配が定義できます。

### シンプレクティック形式

シンプレクティック形式とは、各接空間に入った反対称な2-form

$$
\omega_p(u,v)
$$

で、非退化かつ閉じているものです。
非退化とは、$\omega_p(u,v)$をすべての$v$に対して見ると$u$が復元できる、という条件です。
閉じているとは

$$
d\omega=0
$$

という条件です。
物理では、シンプレクティック形式はHamilton力学の幾何を与えます。

### 概複素構造と複素多様体

概複素構造とは、各接空間に「$i$倍」のような作用素$J$を入れたものです。
つまり

$$
J_p:T_pM\to T_pM
$$

があり、

$$
J_p^2=-1
$$

を満たします。
これは実接空間を複素線形空間のように扱うための構造です。

ただし、概複素構造があるだけでは、座標変換が正則になるとは限りません。
概複素構造が実際に複素座標から来ているとき、その概複素構造は積分可能であると言います。
積分可能な概複素構造を持つ多様体が複素多様体です。
ざっくり言えば、複素多様体とは局所的に$\mathbb{C}^n$のように見え、座標変換が正則な多様体です。

### Hermite計量とKähler形式

Hermite計量とは、複素構造$J$と両立するRiemann計量です。
両立とは

$$
g(Ju,Jv)=g(u,v)
$$

が成り立つことです。
Hermite計量$g$と複素構造$J$から、2-form

$$
\omega(u,v)=g(Ju,v)
$$

を作れます。
これをKähler形式、あるいは基本2-formと呼びます。

### Kähler多様体

Kähler多様体とは、複素多様体にHermite計量が入り、そのKähler形式が閉じているものです。
つまり

$$
d\omega=0
$$

が成り立つHermite多様体です。
この条件により、Riemann幾何、シンプレクティック幾何、複素幾何が互いに矛盾せず同居します。

この記事で何度も使う関係は

$$
\omega(u,v)=g(Ju,v)
$$

です。
これは「計量$g$」「複素構造$J$」「シンプレクティック形式$\omega$」の三つが一体になっていることを表します。

### Kählerポテンシャル

最後にKählerポテンシャルです。
複素座標$z_1,\ldots,z_n$を持つ局所座標で、ある実函数$K(z,\bar z)$から計量が

$$
g_{i\bar j}
=
\frac{\partial^2 K}{\partial z_i\partial \bar z_j}
$$

と書けるとき、$K$をKählerポテンシャルと呼びます。

ここで$\partial$と$\bar\partial$は、外微分$d$を複素座標の向きに分けたものです。
局所的には

$$
d=\partial+\bar\partial
$$

であり、函数$f(z,\bar z)$に対して

$$
\partial f
=
\sum_i
\frac{\partial f}{\partial z_i}dz_i,
\qquad
\bar\partial f
=
\sum_i
\frac{\partial f}{\partial \bar z_i}d\bar z_i
$$

と定義されます。
したがって

$$
\partial\bar\partial K
=
\sum_{i,j}
\frac{\partial^2 K}{\partial z_i\partial \bar z_j}
dz_i\wedge d\bar z_j
$$

です。
この記法を使うと、Kähler形式は

$$
\omega
=
i\partial\bar\partial K
$$

と書けます。

この形で書けるなら、Kähler形式は自動的に閉じています。
実際、$\partial^2=\bar\partial^2=0$と$\partial\bar\partial=-\bar\partial\partial$から

$$
d(i\partial\bar\partial K)
=
i(\partial+\bar\partial)\partial\bar\partial K
=0
$$

です。
したがって、複素多様体上で$g_{i\bar j}=\partial_i\partial_{\bar j}K$が正定値なHermite計量を与えているなら、その計量はKählerです。

逆に、Kähler計量は局所的にはKählerポテンシャルから書けます。
ただし、一般には多様体全体で一つの大域的なKählerポテンシャルが存在するとは限りません。
この記事で使う$\mathbb{C}^N$では大域的なポテンシャルを書けますが、$\mathbb{C}P^{N-1}$のFubini-Studyポテンシャルは通常、各座標チャート上の局所表示として使います。

Kählerポテンシャルは一意ではありません。
正則函数$F(z)$を使って

$$
K(z,\bar z)
\mapsto
K(z,\bar z)+F(z)+\overline{F(z)}
$$

と変えても、$g_{i\bar j}$は変わりません。
したがって、Kählerポテンシャルは計量を作るための局所的な表示だと思うのがよいです。

## 複素内積空間としての$\mathbb{C}^N$

有限次元Hilbert空間を

$$
\mathcal{H} \simeq \mathbb{C}^N
$$

とします。
内積をブラケット記法で

$$
\langle \phi|\psi\rangle
$$

と書きます。
物理の記法では、これは第一引数について反線形、第二引数について線形です。

この内積はHermite形式です。
Hermite形式は実部と虚部に分解できます。
接ベクトル$u,v \in T_\psi\mathcal{H} \simeq \mathcal{H}$に対して

$$
g_{\mathcal{H}}(u,v)=\mathrm{Re}\langle u|v\rangle
$$

と置くと、これは実Riemann計量です。
また

$$
\omega_{\mathcal{H}}(u,v)=\mathrm{Im}\langle u|v\rangle
$$

と置くと、これはシンプレクティック形式になります。

さらに、複素構造$J_{\mathcal{H}}$を

$$
J_{\mathcal{H}}u = iu
$$

で定義します。
すると

$$
J_{\mathcal{H}}^2=-1
$$

であり、

$$
\omega_{\mathcal{H}}(u,v)=g_{\mathcal{H}}(J_{\mathcal{H}}u,v)
$$

が成り立ちます。

つまり$\mathbb{C}^N$には、最初から

- 実Riemann計量$g_{\mathcal{H}}$
- シンプレクティック形式$\omega_{\mathcal{H}}$
- 複素構造$J_{\mathcal{H}}$

が入っています。
しかもこれらは互いに両立しています。
この意味で、$\mathbb{C}^N$は最も基本的なKähler多様体です。

もっと座標で書くと、$z_j=x_j+iy_j$に対して

$$
ds^2 = \sum_j (dx_j^2+dy_j^2)
$$

であり、

$$
\omega_{\mathcal{H}} = \sum_j dx_j\wedge dy_j
$$

です。
これは平坦なEuclid空間$\mathbb{R}^{2N}$に、複素構造を入れたものだと思えばよいです。

## 物理状態はベクトルではなくrayである

量子力学では、$|\psi\rangle$と$c|\psi\rangle$は同じ物理状態を表します。
ここで$c\in\mathbb{C}^\times$です。
したがって、ゼロでないベクトル全体

$$
\mathcal{H}\setminus\{0\}
$$

を複素スカラー倍で割った空間

$$
(\mathcal{H}\setminus\{0\})/\mathbb{C}^\times
$$

を考えます。
これが複素射影空間$\mathbb{C}P^{N-1}$です。

同じことを、規格化済み状態から見ることもできます。
規格化条件

$$
\langle \psi|\psi\rangle=1
$$

を課すと、状態ベクトルは単位球面

$$
S^{2N-1}=\{|\psi\rangle\in\mathcal{H}\mid \langle\psi|\psi\rangle=1\}
$$

上にあります。
この上でまだ全体位相

$$
|\psi\rangle \mapsto e^{i\theta}|\psi\rangle
$$

が残っています。
したがって

$$
\mathbb{C}P^{N-1}=S^{2N-1}/U(1)
$$

です。

この表示は量子力学では非常に自然です。
規格化条件でノルム方向を落とし、$U(1)$で全体位相方向を落とすと、物理的な純粋状態空間が残ります。

## 接空間とゲージ方向

規格化済み状態$|\psi\rangle$を少し変化させます。
変化を$|\delta\psi\rangle$と書くと、規格化条件の一次変化から

$$
\mathrm{Re}\langle \psi|\delta\psi\rangle=0
$$

が従います。
したがって、単位球面$S^{2N-1}$の接ベクトルはこの条件を満たします。

一方で、全体位相の変化

$$
|\psi\rangle \mapsto e^{i\theta}|\psi\rangle
$$

の無限小変化は

$$
|\delta\psi\rangle=i|\psi\rangle
$$

です。
これは物理状態を変えない方向です。
この方向を垂直方向、あるいはゲージ方向と呼ぶことにします。

射影空間の接ベクトルとして意味があるのは、このゲージ方向を除いた変化です。
そこで

$$
|\delta\psi_\perp\rangle
= (1-|\psi\rangle\langle\psi|)|\delta\psi\rangle
$$

を考えます。
これは$|\psi\rangle$に直交する成分です。
すなわち

$$
\langle\psi|\delta\psi_\perp\rangle=0
$$

です。

この直交成分が、$\mathbb{C}P^{N-1}$上の実際の変化を表します。
全体位相方向$i|\psi\rangle$は射影空間では消えます。

## Fubini-Study計量

Hilbert空間には内積があります。
しかし、そのままでは物理状態空間の計量にはなりません。
なぜなら、$|\psi\rangle$と$e^{i\theta}|\psi\rangle$を同一視しなければならないからです。

そこで、変化$|\delta\psi\rangle$のうち、物理的に意味のある直交成分だけを測ります。
規格化済み状態では

$$
ds_{\mathrm{FS}}^2
= \langle \delta\psi_\perp|\delta\psi_\perp\rangle
$$

と定義します。
展開すると

$$
ds_{\mathrm{FS}}^2
= \langle \delta\psi|\delta\psi\rangle
- |\langle\psi|\delta\psi\rangle|^2
$$

です。
これがFubini-Study計量です。

より正確には、上の式はHermite形式を与えます。
その実部がRiemann計量で、虚部がシンプレクティック形式になります。
二つの変化$|\delta_1\psi\rangle,|\delta_2\psi\rangle$に対して

$$
h_{\mathrm{FS}}(\delta_1\psi,\delta_2\psi)
=
\langle \delta_1\psi|
(1-|\psi\rangle\langle\psi|)
|\delta_2\psi\rangle
$$

と書けます。
このとき

$$
g_{\mathrm{FS}}=\mathrm{Re}\,h_{\mathrm{FS}},
\qquad
\omega_{\mathrm{FS}}=\mathrm{Im}\,h_{\mathrm{FS}}
$$

です。

:::message
Fubini-Study計量は、Hilbert空間の内積をそのまま使ったものではなく、全体位相方向を除いた成分に内積を入れたものです。
そのため$\mathbb{C}P^{N-1}$上の計量として well-defined になります。
:::

規格化していないベクトル$|\psi\rangle\neq0$を使うなら、同じ式は

$$
h_{\mathrm{FS}}(\delta_1\psi,\delta_2\psi)
=
\frac{\langle \delta_1\psi|\delta_2\psi\rangle}{\langle\psi|\psi\rangle}
-
\frac{\langle \delta_1\psi|\psi\rangle
\langle\psi|\delta_2\psi\rangle}
{\langle\psi|\psi\rangle^2}
$$

と書けます。
これは$|\psi\rangle$のスケールを変えても同じ射影空間上の量を表します。

## QGTはFS計量の引き戻しである

物理では、状態がパラメータ$\lambda=(\lambda^1,\ldots,\lambda^m)$に依存することがよくあります。

$$
|\psi\rangle = |\psi(\lambda)\rangle
$$

とします。
規格化されているとして、パラメータ変化に対する接ベクトルは

$$
|\partial_\mu\psi\rangle
=\frac{\partial}{\partial\lambda^\mu}|\psi(\lambda)\rangle
$$

です。
このときFubini-StudyのHermite形式をパラメータ空間へ引き戻すと

$$
\chi_{\mu\nu}
=
\langle \partial_\mu\psi|
(1-|\psi\rangle\langle\psi|)
|\partial_\nu\psi\rangle
$$

が得られます。
これがQuantum Geometric Tensorです。
展開すると

$$
\chi_{\mu\nu}
=
\langle \partial_\mu\psi|\partial_\nu\psi\rangle
-
\langle \partial_\mu\psi|\psi\rangle
\langle\psi|\partial_\nu\psi\rangle
$$

です。
第二項は、全体位相方向に対応する成分を引いています。
そのため、この形は「連結部分」と呼ばれることがあります。

実部は量子計量です。

$$
g_{\mu\nu}=\mathrm{Re}\,\chi_{\mu\nu}
$$

虚部はBerry曲率と対応します。

$$
\Omega_{\mu\nu}=\mathrm{Im}\,\chi_{\mu\nu}
$$

と書けます。
文献によってはBerry曲率に$2$や符号を含めるので、ここは規約に注意が必要です。

重要なのは、QGTが突然出てきた量ではないということです。
QGTは

$$
\lambda \mapsto [\psi(\lambda)] \in \mathbb{C}P^{N-1}
$$

という写像によって、Fubini-StudyのHermite形式をパラメータ空間へ引き戻したものです。

したがって、量子計量やBerry曲率は、状態空間$\mathbb{C}P^{N-1}$の幾何をパラメータ空間から見たものです。

## 変分多様体としてのアンサッツ

変分法では、$\mathbb{C}P^{N-1}$全体を動くわけではありません。
何らかのアンサッツを決めて、その中だけを動きます。

パラメータ空間を$\Theta$とし、アンサッツを

$$
\Psi:\Theta\to\mathcal{H}\setminus\{0\}
$$

と書きます。
物理状態として意味があるのはrayなので、本当に見るべき写像は

$$
\iota:\Theta\to\mathbb{C}P^{N-1},
\qquad
\iota(\theta)=[\Psi(\theta)]
$$

です。

この像

$$
\mathcal{M}_{\mathrm{ans}}=\iota(\Theta)
\subset
\mathbb{C}P^{N-1}
$$

が変分多様体です。
変分法とは、全状態空間$\mathbb{C}P^{N-1}$上のエネルギー函数を、部分集合$\mathcal{M}_{\mathrm{ans}}$に制限して最小化する問題です。

この見方をすると、QGTの意味がかなりはっきりします。
QGTは、Fubini-StudyのHermite形式をアンサッツ写像で引き戻したものです。

$$
\chi=\iota^*h_{\mathrm{FS}}
$$

です。
その実部

$$
G=\mathrm{Re}\,\chi=\iota^*g_{\mathrm{FS}}
$$

が変分多様体上の計量であり、虚部

$$
\Omega=\mathrm{Im}\,\chi=\iota^*\omega_{\mathrm{FS}}
$$

がBerry曲率の引き戻しです。

つまり、QGTは「パラメータ空間に人工的に入れた行列」ではありません。
アンサッツが$\mathbb{C}P^{N-1}$へ作る写像を通して、状態空間のKähler幾何をパラメータ空間へ持ち帰ったものです。

:::message
自然勾配法で出てくる計量行列は、変分多様体に引き戻されたFubini-Study計量です。
したがって自然勾配は、パラメータ空間のEuclid幾何ではなく、状態空間での距離に基づく勾配法です。
:::

## アンサッツ多様体への射影

自然勾配法や虚時間発展を変分アンサッツで行うとき、面倒になるのはここです。
全状態空間$\mathbb{C}P^{N-1}$上では、エネルギー

$$
E([\psi])=\frac{\langle\psi|H|\psi\rangle}{\langle\psi|\psi\rangle}
$$

の勾配方向を考えればよいです。
しかし変分法では、動ける方向が

$$
T_{[\psi]}\mathcal{M}_{\mathrm{ans}}
\subset
T_{[\psi]}\mathbb{C}P^{N-1}
$$

に制限されます。
したがって、本当に必要なのは全空間の勾配そのものではなく、それをアンサッツ多様体の接空間へ射影したものです。

パラメータの微小変化$\delta\theta$は、状態空間上の接ベクトル

$$
d\iota(\delta\theta)
\in
T_{[\psi]}\mathbb{C}P^{N-1}
$$

を作ります。
自然勾配方向$\delta\theta$は、任意の変分方向$\eta$に対して

$$
G(\delta\theta,\eta)
=
-dE(d\iota(\eta))
$$

を満たす方向です。
座標で書けば

$$
G_{\mu\nu}\delta\theta^\nu
=
-\partial_\mu E
$$

です。
これが自然勾配法の線形方程式です。

幾何的には、これは

$$
-\mathrm{grad}_{\mathrm{FS}}E
$$

を$\mathcal{M}_{\mathrm{ans}}$の接空間へFubini-Study計量で直交射影していることに対応します。
つまり自然勾配は、周囲の射影Hilbert空間で見た最急降下方向を、アンサッツで実現可能な方向に落としたものです。

虚時間発展の変分版、あるいはimaginary-time TDVPで出てくる射影条件も同じ構造です。
全Hilbert空間での時間発展ベクトルを、アンサッツ多様体の接空間へ最小二乗的に射影します。
その最小二乗の計量がFubini-Study計量であり、座標表示したものがQGTです。

このため、自然勾配の記事を書こうとすると、単に

$$
G^{-1}\nabla E
$$

と書くだけでは済みません。
本質的には「全状態空間上の勾配を、アンサッツ多様体へ射影する」という話をしなければいけません。
ここが少し重い部分です。

## 正則アンサッツと部分多様体

パラメータ空間$\Theta$が実多様体である場合、$\mathcal{M}_{\mathrm{ans}}$は一般には$\mathbb{C}P^{N-1}$の実部分多様体です。
この場合でも、引き戻し計量

$$
G=\iota^*g_{\mathrm{FS}}
$$

は定義できます。
したがって自然勾配法は使えます。

しかし、$\Theta$が複素多様体で、アンサッツ写像

$$
\iota:\Theta\to\mathbb{C}P^{N-1}
$$

が正則である場合は、さらに強いことが言えます。
微分$d\iota$が各点で単射なら、$\iota$は正則はめ込みです。
さらに$\iota$が像への同相写像になっていれば、正則埋め込みです。
このとき像$\mathcal{M}_{\mathrm{ans}}$は$\mathbb{C}P^{N-1}$の複素部分多様体になります。

この場合、$\mathbb{C}P^{N-1}$のKähler構造はそのまま引き戻せます。
すなわち

$$
g_{\Theta}=\iota^*g_{\mathrm{FS}},
\qquad
\omega_{\Theta}=\iota^*\omega_{\mathrm{FS}}
$$

が得られます。
複素構造$J_\Theta$は

$$
d\iota\circ J_\Theta
=
J_{\mathrm{FS}}\circ d\iota
$$

を満たすものとして、$\mathbb{C}P^{N-1}$の複素構造と両立します。
特に

$$
d\omega_{\Theta}
=
d\iota^*\omega_{\mathrm{FS}}
=
\iota^*d\omega_{\mathrm{FS}}
=0
$$

なので、$\Theta$は引き戻し計量によってKähler多様体になります。

この意味で、正則アンサッツは特別です。
単にパラメータを複素数にしただけではなく、アンサッツ多様体が状態空間の複素幾何と整合します。
逆に、パラメータ依存性が$z$と$\bar z$の両方を含むような非正則アンサッツでは、実Riemann計量としてのQGTは残りますが、複素部分多様体としてのKähler構造は一般には残りません。

:::message
実パラメータの量子回路アンサッツは、普通は$\mathbb{C}P^{N-1}$の実部分多様体を作ります。
正則パラメータを持つアンサッツが作る複素部分多様体とは、幾何的な性質が異なります。
:::

## 埋め込みとはめ込みの非一意性

アンサッツを多様体として見るとき、もう一つ注意があります。
パラメータ表示は一意ではありません。

まず、同じ物理状態を表すHilbert空間への持ち上げは無数にあります。
たとえば

$$
\Psi(\theta)
\quad\text{と}\quad
e^{i\alpha(\theta)}\Psi(\theta)
$$

は、同じ射影空間上の写像

$$
\iota(\theta)=[\Psi(\theta)]
$$

を定めます。
したがって、Hilbert空間上で見た微分はゲージに依存します。
一方、Fubini-Study計量やQGTの連結部分は、このゲージ方向を消した量です。

次に、パラメータ空間の取り方も非一意です。
別のパラメータ$\theta'=\theta'(\theta)$を使えば、同じ変分多様体を別の座標で表せます。
この場合、計量行列$G_{\mu\nu}$の成分は変わりますが、幾何そのものは変わりません。

さらに、アンサッツ写像が単射でないこともあります。
異なるパラメータが同じ物理状態を表す場合、

$$
\iota(\theta_1)=\iota(\theta_2)
\qquad
(\theta_1\neq\theta_2)
$$

が起こります。
このとき、$\Theta$は変分多様体そのものというより、その上の被覆や冗長な座標系になっています。

微分$d\iota$が単射でない点では、引き戻し計量$G=\iota^*g_{\mathrm{FS}}$が退化します。
これは自然勾配法でQGTが特異行列になる状況に対応します。
物理的には、あるパラメータ方向に動いても状態が一次では変化しないということです。

したがって、変分多様体を厳密に扱うには、少なくとも次を区別する必要があります。

- パラメータ空間$\Theta$
- Hilbert空間への持ち上げ$\Psi:\Theta\to\mathcal{H}\setminus\{0\}$
- 射影空間への写像$\iota:\Theta\to\mathbb{C}P^{N-1}$
- 像としての変分多様体$\mathcal{M}_{\mathrm{ans}}$

自然勾配やTDVPで本当に重要なのは、最後の$\mathcal{M}_{\mathrm{ans}}$と、その接空間への射影です。
しかし計算では$\Theta$上の座標を使うので、ゲージ冗長性やパラメータ冗長性がQGTの特異性として現れます。

## 複素射影空間の座標

$\mathbb{C}P^{N-1}$の点は、ゼロでないベクトル

$$
Z=(Z_0,\ldots,Z_{N-1})\in\mathbb{C}^N\setminus\{0\}
$$

の同値類

$$
[Z_0:\cdots:Z_{N-1}]
$$

です。
同値関係は

$$
(Z_0,\ldots,Z_{N-1})
\sim
c(Z_0,\ldots,Z_{N-1})
\qquad (c\in\mathbb{C}^\times)
$$

です。

$Z_0\neq0$のチャートでは

$$
w_j=\frac{Z_j}{Z_0}\qquad (j=1,\ldots,N-1)
$$

を座標にできます。
このチャートでは点を

$$
[1:w_1:\cdots:w_{N-1}]
$$

と書けます。

このように、$\mathbb{C}P^{N-1}$は局所的には$\mathbb{C}^{N-1}$に見えます。
しかもチャート間の座標変換は正則です。
したがって$\mathbb{C}P^{N-1}$は複素多様体です。

この座標でFubini-Study計量はKählerポテンシャル

$$
K(w,\bar w)=\log(1+\sum_j |w_j|^2)
$$

から得られます。
すなわち

$$
g_{i\bar j}
=
\frac{\partial^2 K}{\partial w_i\partial \bar w_j}
$$

です。
計算すると

$$
g_{i\bar j}
=
\frac{(1+|w|^2)\delta_{ij}-\bar w_i w_j}
{(1+|w|^2)^2}
$$

になります。
ここで

$$
|w|^2=\sum_j |w_j|^2
$$

です。

この式は少し複雑に見えますが、意味は単純です。
射影空間では、ベクトルの絶対的な大きさではなく、方向だけを測ります。
そのため、通常のEuclid計量からスケール方向と位相方向を取り除いた形になります。

## 等質空間としての$\mathbb{C}P^{N-1}$

$\mathbb{C}P^{N-1}$には$U(N)$が自然に作用します。
ユニタリ変換$U\in U(N)$は状態ベクトルを

$$
|\psi\rangle \mapsto U|\psi\rangle
$$

と変換します。
これは内積を保つので、Fubini-Study計量も保ちます。

この作用は推移的です。
つまり、任意の規格化済み状態は、適当なユニタリ変換で基準状態

$$
|e_0\rangle=(1,0,\ldots,0)^T
$$

へ移せます。

基準点$[e_0]$を固定するユニタリ変換は

$$
U(1)\times U(N-1)
$$

です。
したがって

$$
\mathbb{C}P^{N-1}
\simeq
\frac{U(N)}{U(1)\times U(N-1)}
$$

と書けます。

これは$\mathbb{C}P^{N-1}$が等質空間であることを意味します。
どの点も幾何的には同じです。
Fubini-Study計量は、この$U(N)$対称性と非常に相性がよい計量です。

この等質空間表示は、量子力学では「任意の純粋状態はユニタリ変換で互いに移り合う」という事実を幾何学的に書いたものです。

## Berry接続とシンプレクティック形式

単位球面$S^{2N-1}$から射影空間への写像

$$
S^{2N-1}\to \mathbb{C}P^{N-1}
$$

は$U(1)$主束です。
この主束には自然な接続があります。
Berry接続です。

規格化済み状態に対して

$$
A = -\mathrm{Im}\langle\psi|d\psi\rangle
$$

と置きます。
これは全体位相方向を測る1-formです。

その曲率

$$
F=dA
$$

は射影空間上の2-formに降ります。
この2-formがFubini-Studyのシンプレクティック形式です。
規約の違いを除けば

$$
F \sim \omega_{\mathrm{FS}}
$$

です。

ここで重要なのは、$\omega_{\mathrm{FS}}$が閉じていて非退化であることです。

閉じているとは

$$
d\omega_{\mathrm{FS}}=0
$$

ということです。
これは局所的にKählerポテンシャル

$$
K=\log(1+|w|^2)
$$

から

$$
\omega_{\mathrm{FS}}
= i\partial\bar\partial K
$$

と書けることから従います。

非退化性は、全体位相方向を割ったあとには、物理的な接方向に対して$\omega_{\mathrm{FS}}$がちゃんとペアリングを与えることを意味します。

したがって、$\mathbb{C}P^{N-1}$はシンプレクティック多様体です。
Berry曲率がシンプレクティック形式になっている、と言ってもよいです。

## 概複素構造と複素構造

Hilbert空間$\mathcal{H}\simeq\mathbb{C}^N$には、$i$倍による複素構造がありました。

$$
J_{\mathcal{H}}u=iu
$$

この構造は射影空間にも降ります。
なぜなら、$|\psi\rangle$に直交する変化$|\delta\psi_\perp\rangle$に$i$を掛けても、やはり$|\psi\rangle$に直交するからです。

$$
\langle\psi|\delta\psi_\perp\rangle=0
\quad\Rightarrow\quad
\langle\psi|i\delta\psi_\perp\rangle=0
$$

したがって、射影空間の接空間上で

$$
J_{\mathrm{FS}}[\delta\psi_\perp]=[i\delta\psi_\perp]
$$

と定義できます。
これは

$$
J_{\mathrm{FS}}^2=-1
$$

を満たします。
したがって$\mathbb{C}P^{N-1}$は概複素構造を持ちます。

さらに、先ほど見たように$\mathbb{C}P^{N-1}$には正則座標

$$
w_j=\frac{Z_j}{Z_0}
$$

があります。
チャート間の変換も正則です。
したがって、この概複素構造は積分可能であり、$\mathbb{C}P^{N-1}$は複素多様体です。

## Kähler多様体としての$\mathbb{C}P^{N-1}$

ここまでで、$\mathbb{C}P^{N-1}$には三つの構造が出てきました。

- Fubini-Study計量$g_{\mathrm{FS}}$
- シンプレクティック形式$\omega_{\mathrm{FS}}$
- 複素構造$J_{\mathrm{FS}}$

これらは独立に存在しているわけではありません。
互いに両立しています。

具体的には

$$
\omega_{\mathrm{FS}}(u,v)
=
g_{\mathrm{FS}}(J_{\mathrm{FS}}u,v)
$$

が成り立ちます。
さらに

$$
d\omega_{\mathrm{FS}}=0
$$

です。
したがって、$\mathbb{C}P^{N-1}$はKähler多様体です。

つまり、量子状態空間は単なるRiemann多様体ではありません。
同時に

- 距離を測るRiemann幾何
- Berry曲率を持つシンプレクティック幾何
- 正則座標を持つ複素幾何

を備えています。
これらが一つにまとまったものがKähler幾何です。

## 正則多様体とKähler多様体の関係

ここで注意があります。
複素多様体であることと、Kähler多様体であることは同じではありません。

冒頭で述べたように、複素多様体は正則座標を持つ多様体です。
そこにHermite計量が入り、対応するKähler形式が閉じているとき、Kähler多様体になります。

つまり流れとしては

$$
\text{複素多様体}
\quad+\quad
\text{よいHermite計量}
\quad\Rightarrow\quad
\text{Kähler多様体}
$$

です。

一般の複素多様体が必ずKählerになるわけではありません。
しかし$\mathbb{C}^N$と$\mathbb{C}P^{N-1}$は非常に特別です。

$\mathbb{C}^N$では

$$
K(z,\bar z)=\sum_j |z_j|^2
$$

がKählerポテンシャルになり、平坦なKähler構造が得られます。

$\mathbb{C}P^{N-1}$では局所的に

$$
K(w,\bar w)=\log(1+|w|^2)
$$

がKählerポテンシャルになり、Fubini-Study計量が得られます。

この二つは量子力学にとって特別に重要です。
状態ベクトルの空間は$\mathbb{C}^N$であり、物理的な純粋状態の空間は$\mathbb{C}P^{N-1}$です。
どちらも自然なKähler構造を持ちます。

## 量子力学で何が嬉しいのか

この幾何を使うと、量子力学のいくつかの構造が一つの図式に入ります。

まず、状態間の距離はFubini-Study計量で測れます。
規格化済み状態$|\psi\rangle,|\phi\rangle$に対して、射影空間上の距離は重なり

$$
|\langle\psi|\phi\rangle|
$$

で決まります。
全体位相に依存しない量だけが残ります。

次に、Berry位相は$U(1)$束の接続として理解できます。
その曲率はFubini-Studyのシンプレクティック形式と対応します。

さらに、パラメータ依存状態$|\psi(\lambda)\rangle$を考えると、QGTはFubini-Study構造の引き戻しになります。
実部は量子計量、虚部はBerry曲率です。

最後に、変分法や自然勾配では、アンサッツ多様体上に引き戻された計量が重要になります。
これは「どの方向にパラメータを動かすと、実際に量子状態がどれだけ変わるか」を測る量です。
したがって、自然勾配は単なる最適化テクニックではなく、射影Hilbert空間の勾配をアンサッツ多様体へ射影したものとして理解できます。
QGTが特異になる場合も、幾何的にはパラメータ表示の冗長性や、アンサッツ写像の階数落ちとして解釈できます。

## まとめ

この記事では、有限次元の量子状態空間に現れるKähler幾何を見ました。

- $\mathbb{C}^N$は平坦なKähler多様体である
- 物理的な純粋状態はrayなので、状態空間は$\mathbb{C}P^{N-1}$である
- $\mathbb{C}P^{N-1}$は$S^{2N-1}/U(1)$として得られる
- Hilbert空間の内積から、全体位相方向を除くことでFubini-Study計量が得られる
- QGTはFubini-StudyのHermite形式をパラメータ空間へ引き戻したものである
- 変分アンサッツは$\mathbb{C}P^{N-1}$内の変分多様体を定める
- 自然勾配は全状態空間の勾配を変分多様体の接空間へ射影したものである
- 正則アンサッツが正則埋め込みを与えると、変分多様体はKähler構造を継承する
- QGTの特異性は、ゲージ冗長性やパラメータ冗長性として現れる
- $\mathbb{C}P^{N-1}$は$U(N)/(U(1)\times U(N-1))$という等質空間である
- Berry曲率はFubini-Studyのシンプレクティック形式と対応する
- $\mathbb{C}P^{N-1}$は複素構造、計量、シンプレクティック形式が両立したKähler多様体である

抽象的な言葉で言えば、量子状態空間は複素多様体であり、さらに自然なKähler構造を持ちます。
しかしこの記事で重要なのは、抽象論そのものではありません。

量子力学で日常的に使っている

$$
\langle\phi|\psi\rangle,\qquad
|\psi\rangle\sim e^{i\theta}|\psi\rangle,\qquad
\chi_{\mu\nu},\qquad
\text{Berry曲率},\qquad
\text{自然勾配}
$$

は、すべて$\mathbb{C}P^{N-1}$のKähler幾何として自然に整理できます。
