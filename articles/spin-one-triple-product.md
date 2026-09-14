---
title: "スピン1演算子の三重積公式"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: []
published: false
---

スピン1/2の演算子2つの積について以下のような公式が知られている：

$$
S^\alpha S^\beta = \frac{1}{4} \delta^{\alpha\beta} + \frac{\mathrm{i}}{2} \epsilon^{\alpha\beta\gamma} S^\gamma．
$$

これは恒等式

$$
AB=\frac12[A,B]+\frac12\{A,B\}\tag{1}
$$

と交換関係

$$
[S^\alpha,S^\beta]=\mathrm{i}\epsilon^{\alpha\beta\gamma}S^\gamma
$$

と反交換関係

$$
\{S^\alpha,S^\beta\}=\frac12\delta^{\alpha\beta}
$$

から示せる． なお，Pauli行列$\sigma^\alpha$とスピン演算子は$S^\alpha=\sigma^\alpha/2$という関係にあり$1/2$倍異なるため，スピン演算子の公式はPauli行列での公式と定数倍異なることに注意する．

ここでスピン1の場合に同様の2つのスピン演算子の積の公式が成立するか考えてみる．上述の計算を踏襲すると，恒等式と交換関係は成り立つので

$$
S^\alpha S^\beta = \frac{\mathrm{i}}{2}\epsilon^{\alpha\beta\gamma}S^\gamma+\frac12\{S^\alpha,S^\beta\}\tag{2}
$$

までは言える．しかし，スピン1では反交換子$\{S^\alpha,S^\beta\}$をスピン演算子1つ以下では書けない[^anticommutator]．したがって，スピン1では2つのスピン演算子の積について冒頭と同様の公式は成立しない．

[^anticommutator]: $\alpha=\beta=z$の場合だけを考えれば十分である．$\lvert 1,m\rangle$は全スピンの量子数が$1$，$z$成分の量子数が$m$である状態を表し，$\boldsymbol{S}^2\lvert 1,m\rangle=2\lvert 1,m\rangle$および$S^z\lvert 1,m\rangle=m\lvert 1,m\rangle$を満たす．ここでは$\hbar=1$とし，$m=1,0,-1$である．もし$(S^z)^2$が恒等演算子とスピン演算子の線形結合で表せるなら，$S^z$との可換性から$(S^z)^2=a\mathbb{1}+bS^z$と書ける．両辺を$\lvert 1,m\rangle$に作用させると$m^2=a+bm$を得る．$m=0$を代入して$a=0$を得る．次に$m=1$を代入すると$b=1$となる．しかし，$m=-1$は$b=-1$を要求するため矛盾する．

しかし，3つのスピン演算子の積$S^\alpha S^\beta S^\gamma$を考えて，これを2つ以下のスピン演算子の積で書き下せないか，という意味の公式を考えるとこれは成立する．これが本記事で導出する公式になる．

先に本記事で導出する公式を示す．

$$
\boxed{
\begin{aligned}
S^\alpha S^\beta S^\gamma
={}&\frac{\mathrm{i}}2\epsilon^{\alpha\beta\delta}S^\delta S^\gamma
+\frac12\delta^{\alpha\beta}S^\gamma
+\frac14\left(\delta^{\alpha\gamma}S^\beta+\delta^{\beta\gamma}S^\alpha\right)\\
&+\frac{\mathrm{i}}4\left(
\epsilon^{\alpha\gamma\delta}Q^{\delta\beta}
+\epsilon^{\beta\gamma\delta}Q^{\alpha\delta}
\right)．
\end{aligned}
}\tag{3}
$$

ここで$Q^{\alpha\beta}$は四重極(quadrupolar)演算子と呼ばれ，定義は

$$
Q^{\alpha\beta}
:=\{S^\alpha,S^\beta\}-\frac43\delta^{\alpha\beta}
\tag{4}
$$

である．

ここで，後で使う四重極演算子に関わる交換関係の公式を先に示しておく．実質非自明な計算はここで尽きている．

$$
[Q^{\alpha\beta},S^\gamma]
=\mathrm{i}\epsilon^{\alpha\gamma\delta}Q^{\delta\beta}
+\mathrm{i}\epsilon^{\beta\gamma\delta}Q^{\alpha\delta}
\tag{5}
$$

および

$$
\{Q^{\alpha\beta},S^\gamma\}
=\delta^{\alpha\gamma}S^\beta
+\delta^{\beta\gamma}S^\alpha
-\frac23\delta^{\alpha\beta}S^\gamma
\tag{6}
$$

である．式(5)は式(4)とスピン演算子の交換関係から得られる．式(6)はスピン1に固有の関係であり，成分表示を使わずに次のように示せる．任意の実ベクトル$\boldsymbol{n}$に対して，$\boldsymbol{n}\cdot\boldsymbol{S}$の固有値は$\lvert\boldsymbol{n}\rvert,0,-\lvert\boldsymbol{n}\rvert$なので

$$
(\boldsymbol{n}\cdot\boldsymbol{S})^3
=\lvert\boldsymbol{n}\rvert^2(\boldsymbol{n}\cdot\boldsymbol{S})
$$

が成り立つ．この恒等式を$\boldsymbol{n}$について偏極すると

$$
\sum_{\pi\in\mathfrak{S}_3}
S^{\pi(\alpha)}S^{\pi(\beta)}S^{\pi(\gamma)}
=2\left(
\delta^{\alpha\beta}S^\gamma
+\delta^{\beta\gamma}S^\alpha
+\delta^{\gamma\alpha}S^\beta
\right)
\tag{7}
$$

を得る．左辺の積を交換関係で並べ替え，式(4)を使って整理すれば式(6)となる．ここで，$\mathfrak{S}_3$は3つの添字の置換全体を表す．

まず四重極演算子を使うと式(2)は

$$
S^\alpha S^\beta = \frac{\mathrm{i}}{2}\epsilon^{\alpha\beta\gamma}S^\gamma+\frac23\delta^{\alpha\beta}\mathbb{1}+\frac12Q^{\alpha\beta}
$$

と書ける．ここで右から$S^\delta$をかけ，$A=Q^{\alpha\beta}$，$B=S^\delta$とした式(1)を代入すると

$$
\begin{aligned}
S^\alpha S^\beta S^\delta
={}&\frac{\mathrm{i}}2\epsilon^{\alpha\beta\gamma}S^\gamma S^\delta
+\frac23\delta^{\alpha\beta}S^\delta\\
&+\frac14[Q^{\alpha\beta},S^\delta]
+\frac14\{Q^{\alpha\beta},S^\delta\}
\end{aligned}
$$

となる．式(5)，(6)を代入して整理すると

$$
\begin{aligned}
S^\alpha S^\beta S^\delta
={}&\frac{\mathrm{i}}2\epsilon^{\alpha\beta\gamma}S^\gamma S^\delta
+\frac12\delta^{\alpha\beta}S^\delta
+\frac14\left(\delta^{\alpha\delta}S^\beta+\delta^{\beta\delta}S^\alpha\right)\\
&+\frac{\mathrm{i}}4\left(
\epsilon^{\alpha\delta\gamma}Q^{\gamma\beta}
+\epsilon^{\beta\delta\gamma}Q^{\alpha\gamma}
\right)
\end{aligned}
$$

を得る．自由添字$\delta$を$\gamma$に置き換えれば式(3)となる．右辺に現れるスピン演算子の積は高々2つなので，スピン1演算子の三重積を二重積以下に書き下せた．

$[\{A,B\},C]=\{A,[B,C]\}+\{B,[A,C]\}$より

$$
[Q^{\alpha\beta},S^\gamma]=[\{S^\alpha,S^\beta\},S^\gamma]=
$$
