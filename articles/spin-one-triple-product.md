---
title: "スピン1演算子の三重積公式"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: []
published: false
---

::::message
この記事では，学部程度の線形代数と量子力学を前提とする．以下では$\hbar=1$とする．また，ギリシャ文字の添字$\alpha,\beta,\ldots$はCartesian成分$x,y,z$を表し，上付きと下付きは区別しない．同じ添字が繰り返し現れた場合は，その成分について和を取る．恒等演算子の定数倍は恒等演算子を省略して表記する（$cI\to c$）．
::::

スピン1/2の演算子2つの積について以下のような公式が知られている：

$$
S_\alpha S_\beta = \frac{1}{4} \delta_{\alpha\beta} + \frac{\mathrm{i}}{2} \epsilon_{\alpha\beta\gamma} S_\gamma．
$$

これは恒等式

$$
AB=\frac12[A,B]+\frac12\{A,B\}\tag{1}
$$

と交換関係

$$
[S_\alpha,S_\beta]=\mathrm{i}\epsilon_{\alpha\beta\gamma}S_\gamma
$$

と反交換関係

$$
\{S_\alpha,S_\beta\}=\frac12\delta_{\alpha\beta}
$$

から示せる． なお，Pauli行列$\sigma_\alpha$とスピン演算子は$S_\alpha=\sigma_\alpha/2$という関係にあり$1/2$倍異なるため，スピン演算子の公式はPauli行列での公式と定数倍異なることに注意する．

ここでスピン1の場合に同様の2つのスピン演算子の積の公式が成立するか考えてみる．上述の計算を踏襲すると，恒等式と交換関係は成り立つので

$$
S_\alpha S_\beta = \frac{\mathrm{i}}{2}\epsilon_{\alpha\beta\gamma}S_\gamma+\frac12\{S_\alpha,S_\beta\}\tag{2}
$$

までは言える．しかし，スピン1では反交換子$\{S_\alpha,S_\beta\}$をスピン演算子1つ以下では書けない[^anticommutator]．したがって，スピン1では2つのスピン演算子の積について冒頭と同様の公式は成立しない．

[^anticommutator]: $\alpha=\beta=z$の場合だけを考えれば十分である．$\lvert 1,m\rangle$は全スピンの量子数が$1$，$z$成分の量子数が$m$である状態を表し，$\boldsymbol{S}^2\lvert 1,m\rangle=2\lvert 1,m\rangle$および$S_z\lvert 1,m\rangle=m\lvert 1,m\rangle$を満たす．ここで$m=1,0,-1$である．もし$(S_z)^2$が恒等演算子とスピン演算子の線形結合で表せるなら，$S_z$との可換性から$(S_z)^2=a\mathbb{1}+bS_z$と書ける．両辺を$\lvert 1,m\rangle$に作用させると$m^2=a+bm$を得る．$m=0$を代入して$a=0$を得る．次に$m=1$を代入すると$b=1$となる．しかし，$m=-1$は$b=-1$を要求するため矛盾する．

しかし，3つのスピン演算子の積まで考えると，任意の三重積を二重積以下に書き下せる．本記事ではこのスピン1に固有の関係を導出する．

## 三重積公式

三重積について最も簡潔な関係は

$$
\boxed{
S_\alpha S_\beta S_\gamma
+S_\gamma S_\beta S_\alpha
=\delta_{\alpha\beta}S_\gamma
+\delta_{\beta\gamma}S_\alpha
}
\tag{3}
$$

である．左辺では演算子の順序を反転した2項を足している．したがって，この式は三重積の$\alpha\leftrightarrow\gamma$対称部分を与えている．特に$\alpha=\beta=\gamma$とすれば$(S_\alpha)^3=S_\alpha$を得る．

個々の順序付き積を表すには，四重極(quadrupolar)演算子

$$
Q_{\alpha\beta}
:=\{S_\alpha,S_\beta\}
-\frac43\delta_{\alpha\beta}
\tag{4}
$$

を導入するとよい．$Q_{\alpha\beta}$は添字について対称かつトレースレスである．このとき，三重積の完全な還元公式は

$$
\boxed{
S_\alpha S_\beta S_\gamma
=\frac12\left(
\delta_{\alpha\beta}S_\gamma
+\delta_{\beta\gamma}S_\alpha
\right)
+\frac{\mathrm{i}}3\epsilon_{\alpha\beta\gamma}
+\frac{\mathrm{i}}2
\epsilon_{\alpha\gamma\delta}Q_{\delta\beta}
}
\tag{5}
$$

となる．右辺は恒等演算子，スピン演算子，四重極演算子だけからなる．四重極演算子はスピン演算子の二次式なので，これで三重積は二重積以下へ還元された．式(5)で$\alpha$と$\gamma$を入れ替えた式を足せば，$\epsilon$を含む項が消えて式(3)を得る．

## 四重極演算子に関する関係式

定義(4)を使うと，二重積は

$$
S_\alpha S_\beta
=\frac{\mathrm{i}}2\epsilon_{\alpha\beta\gamma}S_\gamma
+\frac23\delta_{\alpha\beta}
+\frac12Q_{\alpha\beta}
\tag{6}
$$

と書ける．三重積を計算するために必要となる$Q_{\alpha\beta}$と$S_\gamma$の交換関係および反交換関係は

$$
[Q_{\alpha\beta},S_\gamma]
=\mathrm{i}\epsilon_{\alpha\gamma\delta}Q_{\delta\beta}
+\mathrm{i}\epsilon_{\beta\gamma\delta}Q_{\alpha\delta}
\tag{7}
$$

および

$$
\{Q_{\alpha\beta},S_\gamma\}
=\delta_{\alpha\gamma}S_\beta
+\delta_{\beta\gamma}S_\alpha
-\frac23\delta_{\alpha\beta}S_\gamma
\tag{8}
$$

である．式(7)は，恒等式

$$
[\{A,B\},C]
=\{A,[B,C]\}+\{B,[A,C]\}
$$

を定義(4)へ適用し，スピン演算子の交換関係を使えば得られる．一方，式(8)はスピン1に固有の関係である．次節では式(8)を成分表示によらず示す．

## 完全対称三重積

標準基底$\{\lvert 1,1\rangle,\lvert 1,0\rangle,\lvert 1,-1\rangle\}$におけるスピン1演算子の行列表現は

$$
S_x=\frac{1}{\sqrt{2}}
\begin{pmatrix}
0&1&0\\
1&0&1\\
0&1&0
\end{pmatrix},\qquad
S_y=\frac{1}{\sqrt{2}}
\begin{pmatrix}
0&-\mathrm{i}&0\\
\mathrm{i}&0&-\mathrm{i}\\
0&\mathrm{i}&0
\end{pmatrix},\qquad
S_z=
\begin{pmatrix}
1&0&0\\
0&0&0\\
0&0&-1
\end{pmatrix}
$$

である．任意の実ベクトル$\boldsymbol{n}=(n_x,n_y,n_z)$に対して，$\boldsymbol{n}\cdot\boldsymbol{S}$は

$$
\boldsymbol{n}\cdot\boldsymbol{S}
=\begin{pmatrix}
n_z&\dfrac{n_x-\mathrm{i}n_y}{\sqrt{2}}&0\\
\dfrac{n_x+\mathrm{i}n_y}{\sqrt{2}}&0&\dfrac{n_x-\mathrm{i}n_y}{\sqrt{2}}\\
0&\dfrac{n_x+\mathrm{i}n_y}{\sqrt{2}}&-n_z
\end{pmatrix}
$$

となる．この行列の特性多項式を計算すると

$$
\begin{aligned}
\det\!\left(\lambda\mathbb{1}-\boldsymbol{n}\cdot\boldsymbol{S}\right)
&=\lambda\left\{\lambda^2-\left(n_x^2+n_y^2+n_z^2\right)\right\}\\
&=\lambda\left(\lambda^2-\lvert\boldsymbol{n}\rvert^2\right)
\end{aligned}
$$

を得る．したがって，$\boldsymbol{n}\cdot\boldsymbol{S}$の固有値は$\lvert\boldsymbol{n}\rvert,0,-\lvert\boldsymbol{n}\rvert$である．Cayley--Hamiltonの定理より

$$
(\boldsymbol{n}\cdot\boldsymbol{S})^3
=\lvert\boldsymbol{n}\rvert^2(\boldsymbol{n}\cdot\boldsymbol{S})
\tag{9}
$$

が成り立つ．式(9)を添字表示すると

$$
n_\alpha n_\beta n_\gamma
S_\alpha S_\beta S_\gamma
=n_\alpha n_\beta n_\gamma
\delta_{\alpha\beta}S_\gamma
$$

となる．$n_\alpha n_\beta n_\gamma$は添字の置換について完全対称なので，$\alpha,\beta,\gamma$の置換全体$\mathfrak{S}_3$について和を取れば

$$
n_\alpha n_\beta n_\gamma T_{\alpha\beta\gamma}=0
$$

を得る．ただし

$$
\begin{aligned}
T_{\alpha\beta\gamma}
:={}&\sum_{\pi\in\mathfrak{S}_3}
S_{\pi(\alpha)}S_{\pi(\beta)}S_{\pi(\gamma)}\\
&-2\left(
\delta_{\alpha\beta}S_\gamma
+\delta_{\beta\gamma}S_\alpha
+\delta_{\gamma\alpha}S_\beta
\right)
\end{aligned}
$$

と定義した．$T_{\alpha\beta\gamma}$は完全対称なので，上の等式が任意の$\boldsymbol{n}$について成り立つことから$T_{\alpha\beta\gamma}=0$が従う[^symmetric-tensor]．したがって

$$
\sum_{\pi\in\mathfrak{S}_3}
S_{\pi(\alpha)}S_{\pi(\beta)}S_{\pi(\gamma)}
=2\left(
\delta_{\alpha\beta}S_\gamma
+\delta_{\beta\gamma}S_\alpha
+\delta_{\gamma\alpha}S_\beta
\right)
\tag{10}
$$

を得る．左辺の積を交換関係で並べ替え，定義(4)を使って整理すると式(8)となる．

[^symmetric-tensor]:
    $T_{\alpha\beta\gamma}$の完全対称性を使って縮約を成分ごとにまとめると，

    $$
    \begin{aligned}
    0={}&n_\alpha n_\beta n_\gamma T_{\alpha\beta\gamma}\\
    ={}&T_{xxx}n_x^3
    +3T_{xxy}n_x^2n_y
    +3T_{xxz}n_x^2n_z\\
    &+3T_{xyy}n_xn_y^2
    +6T_{xyz}n_xn_yn_z
    +3T_{xzz}n_xn_z^2\\
    &+T_{yyy}n_y^3
    +3T_{yyz}n_y^2n_z
    +3T_{yzz}n_yn_z^2
    +T_{zzz}n_z^3
    \end{aligned}
    $$

    となる．例えば$n_x^2n_y$の係数が$3T_{xxy}$なのは，$T_{xxy}=T_{xyx}=T_{yxx}$だからである．ここで各$T_{\alpha\beta\gamma}$は演算子だが，任意の状態$\lvert u\rangle,\lvert v\rangle$で行列要素を取れば，上式は$n_x,n_y,n_z$に関する通常の複素係数多項式になる．この多項式は任意の実数$n_x,n_y,n_z$に対して零なので，互いに異なる10個の単項式の係数はすべて零である．したがって$\langle u\rvert T_{xxx}\lvert v\rangle=\langle u\rvert T_{xxy}\lvert v\rangle=\cdots=\langle u\rvert T_{zzz}\lvert v\rangle=0$となる．これは任意の$\lvert u\rangle,\lvert v\rangle$について成り立つため，$T_{xxx}=T_{xxy}=\cdots=T_{zzz}=0$である．これらは完全対称テンソル$T_{\alpha\beta\gamma}$の独立な成分をすべて尽くすので，$T_{\alpha\beta\gamma}=0$を得る．

## 三重積の還元

式(6)の右から$S_\gamma$をかけ，式(1)を$Q_{\alpha\beta}S_\gamma$に適用すると

$$
\begin{aligned}
S_\alpha S_\beta S_\gamma
={}&\frac{\mathrm{i}}2
\epsilon_{\alpha\beta\delta}S_\delta S_\gamma
+\frac23\delta_{\alpha\beta}S_\gamma\\
&+\frac14[Q_{\alpha\beta},S_\gamma]
+\frac14\{Q_{\alpha\beta},S_\gamma\}
\end{aligned}
\tag{11}
$$

となる．ここに式(6)から式(8)を代入する．さらに，対称かつトレースレスな$Q_{\alpha\beta}$について成り立つ恒等式

$$
\begin{aligned}
&\epsilon_{\alpha\beta\delta}Q_{\delta\gamma}
+\epsilon_{\beta\gamma\delta}Q_{\delta\alpha}
+\epsilon_{\gamma\alpha\delta}Q_{\delta\beta}\\
&\qquad
=\epsilon_{\alpha\beta\gamma}Q_{\delta\delta}
=0
\end{aligned}
\tag{12}
$$

を使って整理すれば，式(5)を得る．これでスピン1演算子の任意の三重積を二重積以下に書き下せた．
