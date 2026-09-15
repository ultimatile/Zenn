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
=&\frac{\mathrm{i}}2\epsilon^{\alpha\beta\gamma}S^\gamma S^\delta
+\frac12\delta^{\alpha\beta}S^\delta
+\frac14\left(\delta^{\alpha\delta}S^\beta+\delta^{\beta\delta}S^\alpha\right)\\
&+\frac{\mathrm{i}}4\left(
\epsilon^{\alpha\delta\gamma}Q^{\gamma\beta}
+\epsilon^{\beta\delta\gamma}Q^{\alpha\gamma}
\right)
\end{aligned}
$$

を得る．自由添字$\delta$を$\gamma$に置き換えれば式(3)となる．右辺に現れるスピン演算子の積は高々2つなので，スピン1演算子の三重積を二重積以下に書き下せた．

---

$[\{A,B\},C]=\{A,[B,C]\}+\{B,[A,C]\}$より

$$
[Q^{\alpha\beta},S^\gamma]=[\{S^\alpha,S^\beta\},S^\gamma]=\{S^\alpha,[S^\beta,S^\gamma]\}+\{S^\beta,[S^\alpha,S^\gamma]\}
=\mathrm{i}\epsilon_{\beta\gamma\delta}\{S^\alpha,S^\delta\}+\mathrm{i}\epsilon_{\alpha\gamma\delta}\{S^\beta,S^\delta\}
$$

やや唐突だがBloch Hamiltonian $\bm{c}\cdot \bm{S}$を考える．ここで$\bm{c}\coloneqq(c_x,c_y,c_z)\in\mathbb{R}^3$は任意の実ベクトルである．
標準基底での$S^\alpha$の行列表示は

$$
S^x=\frac{1}{\sqrt{2}}\begin{pmatrix}
0&1&0\\
1&0&1\\
0&1&0
\end{pmatrix}
\quad
S^y=\frac{1}{\sqrt{2}}\begin{pmatrix}
0&-\mathrm{i}&0\\
\mathrm{i}&0&-\mathrm{i}\\
0&\mathrm{i}&0
\end{pmatrix}
\quad
S^z=\begin{pmatrix}
1&0&0\\
0&0&0\\
0&0&-1
\end{pmatrix}
$$

であるから$\bm{c}\cdot\bm{S}$の行列表示は

$$
\begin{pmatrix}
c^z&\frac{c_x-\mathrm{i}c_y}{\sqrt{2}}&0\\
\frac{c_x+\mathrm{i}c_y}{\sqrt{2}}&0&\frac{c_x-\mathrm{i}c_y}{\sqrt{2}}\\
0&\frac{c_x+\mathrm{i}c_y}{\sqrt{2}}&-c_z
\end{pmatrix}
\quad
$$

となる．続けてCayley-Hamiltonの定理を適用するため$\bm{c}\cdot\bm{S}$の特性方程式$\mathrm{det}(\bm{c}\cdot\bm{S}-\lambda)=0$を求めると$\lambda(\lambda^2-c^2)=0$となる．したがって

$$
(\bm{c}\cdot\bm{S})^3=c^2\bm{c}\cdot\bm{S}
$$

が成り立つ．これをテンソル表示で書き下すと

$$
c_\alpha c_\beta c_\gamma S^\alpha S^\beta S^\gamma = c_\alpha c_\beta c_\gamma \delta_{\beta\gamma}S^\alpha
$$

と書ける．ここで$c_\alpha c_\beta c_\gamma$は$c$数なので添え字の入れ替えについて対称である．例えば$\beta$と$\gamma$を入れ替えても$c_\alpha c_\beta c_\gamma=c_\alpha c_\gamma c_\beta$である．一方$S^\alpha S^\beta S^\gamma$はスピン演算子が一般に非可換なので$S^\alpha S^\beta S^\gamma\neq S^\alpha S^\gamma S^\beta$である．
そこで6種類ある$\alpha$, $\beta$, $\gamma$の置換$\pi\in \mathfrak{S}_3$に渡って上式の和を取り，$c_\alpha c_\beta c_\gamma$の対称性と$\delta_{\alpha\beta}=\delta_{\beta\alpha}$を使って整理すると

$$
c_\alpha c_\beta c_\gamma\sum_{\pi\in\mathfrak{S}_3}S^{\pi(\alpha)}S^{\pi(\beta)}S^{\pi(\gamma)}=2c_\alpha c_\beta c_\gamma(\delta_{\beta\gamma}S^\alpha+\delta_{\gamma\alpha}S^\beta+\delta_{\alpha\beta}S^\gamma)
$$

となる．ここで$T_{\alpha\beta\gamma}\coloneqq\sum_{\pi\in\mathfrak{S}_3}S^{\pi(\alpha)}S^{\pi(\beta)}S^{\pi(\gamma)}-2(\delta_{\beta\gamma}S^\alpha+\delta_{\gamma\alpha}S^\beta+\delta_{\alpha\beta}S^\gamma)$と置くと$T_{\alpha\beta\gamma}$は添え字の入れ替えに対して対称($T^{\alpha\beta\gamma}=T^{\pi(\alpha)\pi(\beta)\pi(\gamma)}(\pi\in\mathfrak{S_3})$)となり，上式は$c_\alpha c_\beta c_\gamma T^{\alpha \beta \gamma}=0$である．$T^{\alpha\beta\gamma}$が完全対称であることから$T^{\alpha\beta\gamma}=0$が従う．

$$
[S^\alpha,Q^{\beta\gamma}]=[S^\alpha,\{S^\beta,S^\gamma\}]=\mathrm{i}\epsilon_{\alpha\gamma\delta}\{S^\beta,S^\delta\}+\mathrm{i}\epsilon_{\alpha\beta\delta}\{S^\delta,S^\gamma\}
$$
