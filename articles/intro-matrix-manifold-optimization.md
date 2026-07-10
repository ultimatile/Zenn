---
title: "手を動かして学ぶ行列多様体上の最適化入門"
emoji: "⭕"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["数学", "最適化", "線形代数", "python"]
published: false
register: joutai
---

## はじめに

ユニタリ行列や直交行列に制約した最小化問題はあちこちに現れる．与えられた行列対を回転で重ね合わせる[Procrustes問題](https://zenn.dev/ultimatile/articles/unitary-procrustes)，対称行列の対角化（固有ベクトルの組は直交行列をなす），量子回路のゲートのあてはめ，[深層学習における重み行列の直交化](https://zenn.dev/ultimatile/articles/unitary-procrustes-newton-schulz)などで，いずれも

$$
\min_{U}f(U)\quad\text{s.t.}\quad U^\dagger U=I_n
$$

の形をしている．制約$U^\dagger U=I_n$は非線形な連立等式なので，勾配降下で素朴に$U\leftarrow U-\eta\nabla f$と動かすと1歩目から制約が壊れる．

この制約を満たす行列の集合は，行列の空間$\mathbb{C}^{n\times n}$の中の滑らかな曲面（[多様体](https://ja.wikipedia.org/wiki/%E5%A4%9A%E6%A7%98%E4%BD%93)）になっており，こうした集合は行列多様体と呼ばれる．行列多様体の上で勾配法やNewton法を回す理論はRiemann最適化として整備されていて，定番の教科書もある[^books]．ただし標準的な教科書は，正規直交な$p$本のベクトル組の全体であるStiefel多様体$\mathrm{St}(n,p)$を軸に接空間・レトラクション・ベクトル輸送といった一般論を展開することが多く，一般の$\mathrm{St}(n,p)$は絵に描けないため，初学では記号操作が先行しがちである．

本記事は逆側の入口を取る．舞台を最小の行列多様体，すなわち円周$S^1$（$1\times1$のユニタリ行列全体$U(1)$）と$2\times2$の直交群$O(2)$・ユニタリ群$U(2)$に限定する．この舞台を選んだのは図が描けるからだけではない．接空間・勾配・指数写像といった登場物の計算がすべて極座標（角度）の微分と$2\times2$の行列演算に落ちるので，本文の導出を紙と鉛筆で最後まで追える．タイトルの「手を動かして」はこの意味であり，ところどころに置いた確かめの計算を自分の手でやりながら読んでほしい．道具の中心にはStiefel多様体の一般論ではなくLie代数（反Hermite行列）による乗法的更新$U\leftarrow\mathrm{e}^{-\eta S}U$を据え，Stiefel多様体との関係は最後に整理する．

前提は線形代数（固有値分解・特異値分解・随伴$\dagger$）と勾配の基礎で，多様体やLie群の予備知識は仮定しない．手計算の答え合わせ用の[NumPy](https://numpy.org)スクリプトと図の生成コードは[リポジトリ](https://github.com/ultimatile/Zenn/tree/main/programs/intro-matrix-manifold-optimization)に置いた（本文にも検算用の断片を載せる）．

## 円周$S^1$の上の勾配降下

### 円を離れる一歩と円に沿う一歩

もっとも小さいユニタリ群から始める．$1\times1$のユニタリ行列とは$\bar zz=1$，すなわち$|z|=1$を満たす複素数$z$のことなので，$U(1)$は複素平面の単位円周$S^1$である．目的函数には

$$
f(z)=|z-b|^2
$$

を選ぶ．$b$は円上にあるとは限らない与えられた複素数で，$f$の最小化は「$b$にいちばん近い円上の点を探せ」という問題である（$b=0$では円上のどの点も等距離になり全点が最小解なので，以下$b\neq0$とする）．最初の手計算として，極形式$b=r\mathrm{e}^{\mathrm{i}\varphi}$，$z=\mathrm{e}^{\mathrm{i}\theta}$を代入して整理すると

$$
f(\mathrm{e}^{\mathrm{i}\theta})=1+r^2-2r\cos(\theta-\varphi)
$$

となる（余弦定理そのものである）．最小は$\theta=\varphi$，すなわち$z^*=b/|b|$（$b$を原点方向に円へ射影した点）と読み取れる．これは[以前の記事](https://zenn.dev/ultimatile/articles/unitary-procrustes)で扱った「与えられた行列に最も近いユニタリ行列を求める問題」（ユニタリProcrustes問題の特殊形）の$n=1$の場合にほかならず，$b=(b/|b|)\,|b|$は$1\times1$の[極分解](https://en.wikipedia.org/wiki/Polar_decomposition)である．答えがわかっている問題をあえて勾配法で解き，一歩一歩を図と手計算で確かめるのが本節の趣旨である．

勾配には，複素数・行列のままで扱える定義を使う．実数値函数$f$の微小変化を実内積で

$$
df=\langle\nabla f,dz\rangle_{\mathbb{R}},\qquad\langle u,v\rangle_{\mathbb{R}}\coloneqq\operatorname{Re}(\bar uv)
$$

と書いたときの$\nabla f$を勾配と定める．[Newton-Schulz法の記事](https://zenn.dev/ultimatile/articles/unitary-procrustes-newton-schulz)の「行列値函数の勾配」の節と同じ定義で，複素平面$\mathbb{C}$を実平面$\mathbb{R}^2$とみなしたときの通常の勾配に一致する．$f(z)=|z-b|^2$なら$df=\overline{dz}\,(z-b)+\overline{(z-b)}\,dz=2\operatorname{Re}\bigl(\overline{(z-b)}\,dz\bigr)$より

$$
\nabla f=2(z-b)
$$

である．これは平面ベクトルとして「$b$から遠ざかる向き」を指す．

素朴な勾配降下の一歩$w=z-\eta\nabla f$は，図1(a)のように円を離れて内側へ落ちる．制約$|z|=1$を保つ手立ては2通りある．

- 円の外で一歩動いてから円に引き戻す（$w/|w|$へ正規化する）．
- はじめから円に沿って動く．

前者は射影付き勾配法と呼ばれる流儀で，その「多様体の外に出た点を多様体へ戻す」役は，一般にはレトラクションと呼ばれる道具が引き受ける[^retraction]．Stiefel多様体の一般論ではこちらが主役だが，本記事の主役は後者である．以下でこれを組み立てる．

![two ways to take a constrained step on the circle](/images/intro-matrix-manifold-optimization/s1-two-steps.png)
*図1: 円上の勾配降下の2つの流儀．(a) 素朴な一歩$w=z-\eta\nabla f$は円を離れるので，正規化$w/|w|$で引き戻す．(b) 勾配を接方向へ射影し（$-\eta\operatorname{grad}f$，円から浮いた白抜き点が先端），同じ弧長だけ円に沿って進む（$\mathrm{e}^{-\eta S}z$）．点線は単位元$1$と$z$それぞれでの接線．*

### 接空間とLie代数$\mathfrak{u}(1)$

「円に沿って動く」を微分の言葉にする．円上を走る曲線$z(t)\in S^1$（$z(0)=z$）は$|z(t)|^2=1$を保つので，微分すると$\operatorname{Re}(\bar z\dot z)=0$．つまり$\bar z\dot z$は純虚数で，$|z|=1$より$\dot z\in\mathrm{i}\mathbb{R}z$となる．点$z$で円に接する方向の全体

$$
T_zS^1=\{\mathrm{i}\omega z\mid\omega\in\mathbb{R}\}=\mathrm{i}\mathbb{R}\,z
$$

を$z$での接空間と呼ぶ．図1(b)の点線が（$z$まで平行移動した）接空間である．とくに単位元$z=1$での接空間

$$
\mathfrak{u}(1)\coloneqq T_1S^1=\mathrm{i}\mathbb{R}
$$

すなわち純虚数の全体には名前がついていて，群$U(1)$の[Lie代数](https://ja.wikipedia.org/wiki/%E3%83%AA%E3%83%BC%E4%BB%A3%E6%95%B0)という[^bracket]．どの点の接空間も$T_zS^1=z\,\mathfrak{u}(1)$と「単位元での接空間に$z$を掛けたもの」で書ける点が肝心で，群の掛け算が接空間の記述を単位元での1個分に節約してくれる．

接方向へ有限の距離を進むには指数函数を使う．$\alpha\in\mathbb{R}$に対して$\mathrm{e}^{\mathrm{i}\alpha}z$は$z$を角度$\alpha$だけ回した円上の点であり，$t\mapsto\mathrm{e}^{\mathrm{i}t\alpha}z$は$z$から初速$\mathrm{i}\alpha z\in T_zS^1$で円周上を等速に歩く曲線，つまり測地線である．Lie代数の元$\mathrm{i}\alpha$を群の元$\mathrm{e}^{\mathrm{i}\alpha}$に移すこの対応を指数写像と呼ぶ．

あとは勾配の接方向成分を取り出せば，円に沿った最急降下が組み上がる．$\nabla f$の$T_zS^1$への直交射影は

$$
\operatorname{grad}f(z)=\langle\mathrm{i}z,\nabla f\rangle_{\mathbb{R}}\,\mathrm{i}z=Sz,\qquad S\coloneqq\operatorname{skew}(\nabla f\,\bar z),\quad\operatorname{skew}(w)\coloneqq\frac{w-\bar w}{2}
$$

と書ける．$\operatorname{skew}$は複素数の純虚部分$\mathrm{i}\operatorname{Im}w$を取り出す操作である．2つ目の等号はよい練習問題なので，まず手で確かめてから下のdetailsと突き合わせてほしい．この$\operatorname{grad}f$が**Riemann勾配**，つまり多様体上での勾配の姿である．降下の一歩は，接ベクトル$-\eta\operatorname{grad}f(z)=-\eta Sz$を初速とする測地線に沿って

$$
z_{k+1}=\mathrm{e}^{-\eta S_k}z_k,\qquad S_k=\operatorname{skew}\bigl(\nabla f(z_k)\,\bar z_k\bigr)
$$

と取る．$S_k$は純虚数なので$|\mathrm{e}^{-\eta S_k}|=1$であり，$|z_{k+1}|=|z_k|=1$が厳密に保たれる．射影も正規化も要らない．

:::details Riemann勾配の式の確認

$z$での単位接ベクトルは$\mathrm{i}z$なので，射影の係数は$\langle\mathrm{i}z,\nabla f\rangle_{\mathbb{R}}=\operatorname{Re}(\overline{\mathrm{i}z}\,\nabla f)=\operatorname{Re}(-\mathrm{i}\bar z\nabla f)=\operatorname{Im}(\bar z\nabla f)$である．よって射影は$\operatorname{Im}(\bar z\nabla f)\,\mathrm{i}z=\bigl(\mathrm{i}\operatorname{Im}(\nabla f\,\bar z)\bigr)z=\operatorname{skew}(\nabla f\,\bar z)\,z=Sz$となる（複素数の積は可換なので$\bar z\nabla f=\nabla f\,\bar z$）．

:::

なお$1\times1$では「純虚部分を取る」と書いたが，複素数$w$を$1\times1$行列とみれば$\bar w$は随伴$w^\dagger$であり，$\operatorname{skew}(w)=(w-w^\dagger)/2$は「反Hermite部分を取る」操作である．この形のまま$n\times n$へ持ち上がる．

### 角度で見れば1次元の勾配降下

$z=\mathrm{e}^{\mathrm{i}\theta}$とおくと$S=\mathrm{i}f'(\theta)$が成り立ち（下のdetails），更新則$z_{k+1}=\mathrm{e}^{-\eta S_k}z_k$は

$$
\theta_{k+1}=\theta_k-\eta f'(\theta_k)
$$

と読める．円上の乗法的な勾配降下の正体は，角度パラメータの通常の1次元勾配降下である（図2）．「パラメータ（角度）で見れば普通の勾配法，複素数・行列のままでは乗法的更新」という二重の見方は$n\times n$でも保たれる．ただし一般の$U(n)$には角度にあたる大域的パラメータの便利な取り方がないため，行列のまま扱う流儀が効いてくる（$U(1)$と後述の$SO(2)$が例外的に1次元で，本記事がこの2つを舞台に選んだ理由でもある）．

:::details 角度の微分との一致の確認

本文で求めた$f(\mathrm{e}^{\mathrm{i}\theta})=1+r^2-2r\cos(\theta-\varphi)$より$f'(\theta)=2r\sin(\theta-\varphi)$．一方$\nabla f\,\bar z=2(z-b)\bar z=2(1-b\bar z)$より$S=\mathrm{i}\operatorname{Im}\bigl(2(1-b\bar z)\bigr)=-2\mathrm{i}\operatorname{Im}(b\bar z)=2\mathrm{i}\operatorname{Im}(\bar bz)=2\mathrm{i}r\sin(\theta-\varphi)=\mathrm{i}f'(\theta)$となる．

:::

ここまでの手計算を数値で答え合わせしておく（本文のコード片はすべてこの検算用である）．行列になっても構造は変わらないので，変数名は後の節と同じにしてある．

```python
import numpy as np

b = 1.4 * np.exp(1j * np.deg2rad(-25))  # target point
z = np.exp(1j * np.deg2rad(120))        # start on the circle
eta = 0.15
for k in range(25):
    G = 2 * (z - b)                  # Euclidean gradient
    S = 1j * (G * np.conj(z)).imag   # skew(G z^dagger)
    z = np.exp(-eta * S) * z
print(abs(z - b / abs(b)))  # 1.62e-05: converged to b/|b|
print(abs(abs(z) - 1))      # 4.4e-16: never left the circle
```

![gradient descent iterates on the circle and on the angle landscape](/images/intro-matrix-manifold-optimization/s1-descent.png)
*図2: $f(z)=|z-b|^2$の勾配降下（$\eta=0.15$，25反復）．(a) 円上の反復列（色は反復の進みで，薄い色から濃い色へ）．(b) 同じ反復を角度$\theta$で見ると，1次元の勾配降下そのものである．*

円で見た対象と一般の呼び名の対応は次のとおり．

| 円での姿 | 一般名 |
| ---- | ---- |
| $\mathrm{i}\mathbb{R}$（単位元での接方向） | Lie代数$\mathfrak{u}(n)$ |
| $\mathrm{i}\mathbb{R}\,z$ | 接空間$T_U$ |
| $\operatorname{skew}(\nabla f\,\bar z)\,z$ | Riemann勾配$\operatorname{grad}f$ |
| $\mathrm{i}\alpha\mapsto\mathrm{e}^{\mathrm{i}\alpha}$ | 指数写像（測地線） |
| $w/\vert w\vert$への正規化 | レトラクション（極分解射影） |

## ユニタリ群$U(n)$とLie代数$\mathfrak{u}(n)$

### 接空間は反Hermite行列で書ける

$$
U(n)\coloneqq\{U\in\mathbb{C}^{n\times n}\mid U^\dagger U=I_n\}
$$

ユニタリ行列は積と逆行列（$U^{-1}=U^\dagger$）で閉じるので$U(n)$は群であり，かつ$\mathbb{C}^{n\times n}\cong\mathbb{R}^{2n^2}$の中の滑らかな曲面（多様体）でもある．群であり多様体でもある対象を[Lie群](https://ja.wikipedia.org/wiki/%E3%83%AA%E3%83%BC%E7%BE%A4)と呼ぶ．$S^1=U(1)$はその最小例だった．実行列版が直交群$O(n)=\{Q\in\mathbb{R}^{n\times n}\mid Q^\top Q=I_n\}$である．

接空間は円のときと同じ計算で出る．$U(n)$上の曲線$U(t)$（$U(0)=U$）は$U(t)U(t)^\dagger=I_n$を保つので，微分して

$$
\dot UU^\dagger+U\dot U^\dagger=0 .
$$

$\Omega\coloneqq\dot UU^\dagger$とおくと$\Omega+\Omega^\dagger=0$，つまり$\Omega$は反Hermite行列である．逆に任意の反Hermite行列$\Omega$に対して曲線$\mathrm{e}^{t\Omega}U$が$\dot U(0)=\Omega U$を実現するので

$$
T_UU(n)=\{\Omega U\mid\Omega\in\mathfrak{u}(n)\},\qquad\mathfrak{u}(n)\coloneqq\{\Omega\in\mathbb{C}^{n\times n}\mid\Omega^\dagger=-\Omega\}
$$

となる．反Hermite行列の全体$\mathfrak{u}(n)$が$U(n)$のLie代数であり，「$\Omega U$」が円の「$\mathrm{i}\omega z$」の一般化である．ここで$\mathrm{e}^{M}\coloneqq\sum_{k\geq0}M^k/k!$は行列指数函数で，$\Omega\in\mathfrak{u}(n)$なら

$$
(\mathrm{e}^{\Omega})^\dagger=\mathrm{e}^{\Omega^\dagger}=\mathrm{e}^{-\Omega}=(\mathrm{e}^{\Omega})^{-1}
$$

より$\mathrm{e}^{\Omega}$はユニタリになる．指数写像が「Lie代数の元からユニタリ行列を作る機械」として働く．

実ベクトル空間としての$\mathfrak{u}(n)$の次元は，対角成分（純虚数で$n$個）と狭義上三角成分（複素数で$n(n-1)/2$個）を数えて$n^2$である．これが多様体$U(n)$の次元，つまり最適化の実自由度になる（制約$U^\dagger U=I_n$はHermite行列1個分＝実$n^2$本の等式で，$2n^2-n^2=n^2$と勘定も合う）．$n=1$で$1$（角度1個），$n=2$で$4$．具体的には

$$
\mathfrak{u}(2)=\operatorname{span}_{\mathbb{R}}\{\mathrm{i}I_2,\ \mathrm{i}\sigma_x,\ \mathrm{i}\sigma_y,\ \mathrm{i}\sigma_z\},\qquad
\sigma_x=\begin{pmatrix}0&1\\1&0\end{pmatrix},\ \sigma_y=\begin{pmatrix}0&-\mathrm{i}\\\mathrm{i}&0\end{pmatrix},\ \sigma_z=\begin{pmatrix}1&0\\0&-1\end{pmatrix}
$$

とPauli行列による基底が取れる（量子計算で1量子ビットゲートの生成子と呼ばれるものである）．実版$\mathfrak{o}(n)$は実反対称行列の全体で次元$n(n-1)/2$．とくに$\mathfrak{o}(2)$は

$$
J=\begin{pmatrix}0&-1\\1&0\end{pmatrix}
$$

の実数倍しかない1次元空間で，$\mathrm{e}^{\theta J}$は角度$\theta$の回転行列である．回転群$SO(2)=\{\mathrm{e}^{\theta J}\}$はまたも円周であり，$2\times2$直交行列の最適化が2次元の図に収まるのはこのためである．

### Riemann勾配と乗法的更新則

Euclid勾配は円のときと同様に

$$
df=\langle\nabla f,dU\rangle_{\mathbb{R}},\qquad\langle A,B\rangle_{\mathbb{R}}\coloneqq\operatorname{Re}\operatorname{tr}(A^\dagger B)
$$

で定める（Frobenius内積の実部．詳細は[Newton-Schulz法の記事](https://zenn.dev/ultimatile/articles/unitary-procrustes-newton-schulz)の「行列値函数の勾配」の節を参照）．曲線$U(t)=\mathrm{e}^{t\Omega}U$に沿った$f$の変化率は，トレースの巡回性を使って

$$
\left.\frac{d}{dt}f(U(t))\right|_{t=0}=\langle\nabla f,\Omega U\rangle_{\mathbb{R}}=\langle\nabla f\,U^\dagger,\Omega\rangle_{\mathbb{R}}
$$

と書ける．ここで$\nabla f\,U^\dagger$をHermite部分と反Hermite部分に分ける:

$$
\nabla f\,U^\dagger=\underbrace{\frac{\nabla f\,U^\dagger+U\nabla f^\dagger}{2}}_{\text{Hermite}}+\ S,\qquad S\coloneqq\operatorname{skew}(\nabla f\,U^\dagger)=\frac{\nabla f\,U^\dagger-U\nabla f^\dagger}{2}\in\mathfrak{u}(n) .
$$

Hermite行列$H$と反Hermite行列$\Omega$は実内積で直交する（$\operatorname{tr}(H^\dagger\Omega)=\operatorname{tr}(H\Omega)$は純虚数なので実部が消える）から，

$$
\left.\frac{d}{dt}f\right|_{t=0}=\langle S,\Omega\rangle_{\mathbb{R}}
$$

が残る．ノルムを固定した$\Omega\in\mathfrak{u}(n)$のうちこれを最小にするのは，Cauchy-Schwarzの不等式の等号条件から$\Omega\propto-S$である．よって最急降下の更新則は

$$
U_{k+1}=\mathrm{e}^{-\eta S_k}U_k,\qquad S_k=\operatorname{skew}\bigl(\nabla f(U_k)\,U_k^\dagger\bigr),\qquad\operatorname{skew}(M)\coloneqq\frac{M-M^\dagger}{2}
$$

となる．円の式で$\bar z$を$U^\dagger$に読み替えただけである．性質を並べる．

- 制約が厳密に保たれる: $\mathrm{e}^{-\eta S_k}$がユニタリなので$U_{k+1}^\dagger U_{k+1}=U_k^\dagger U_k=I_n$．丸め誤差以外で多様体から離れない．ステップ幅が大きすぎても制約が壊れるのではなく「回りすぎる」だけである．
- 降下方向である: $\frac{d}{dt}f(\mathrm{e}^{-tS}U)\big|_{t=0}=-\|S\|_\mathrm{F}^2\leq0$で，$S\neq0$なら必ず$f$が下がる向きに出発する．
- 停留条件は$S=0\iff\nabla f\,U^\dagger$がHermite．制約なしの停留条件$\nabla f=0$の役をこのHermite性が引き受ける．
- Riemann勾配は$\operatorname{grad}f(U)=SU$で，Euclid勾配$\nabla f$の接空間$T_UU(n)$への直交射影に一致する（円の$\operatorname{grad}f=Sz$と同じ形）．更新則は「負のRiemann勾配$-\operatorname{grad}f(U)=-SU$を初速に取った測地線を長さ$\eta\|S\|_\mathrm{F}$だけ進む」Riemann最急降下である[^geodesic]．

### $2\times2$の行列指数函数の閉形式

一般の行列指数函数は[`scipy.linalg.expm`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html)で計算できるが，$2\times2$なら手で書ける．$S\in\mathfrak{u}(2)$を$S=\mathrm{i}aI_2+T$（$\mathrm{i}a=\operatorname{tr}S/2$，$T$はトレースレスな反Hermite行列）と分ける．このとき$T^2=-\theta^2I_2$（$\theta\geq0$）が成り立つので，指数函数の級数が2項に畳めて

$$
\mathrm{e}^{S}=\mathrm{e}^{\mathrm{i}a}\Bigl(\cos\theta\,I_2+\frac{\sin\theta}{\theta}\,T\Bigr)
$$

となる（$\theta\to0$では$\sin\theta/\theta\to1$）．Euler公式$\mathrm{e}^{\mathrm{i}\theta}=\cos\theta+\mathrm{i}\sin\theta$の行列版である．

:::details 2×2指数函数の閉形式の導出

$T$は反Hermiteなので固有値は純虚数，トレースレスなので固有値の和は$0$．よって固有値は$\pm\mathrm{i}\theta$（$\theta\geq0$）と書ける．Cayley-Hamiltonの定理$T^2-(\operatorname{tr}T)T+(\det T)I_2=0$に$\operatorname{tr}T=0$，$\det T=(\mathrm{i}\theta)(-\mathrm{i}\theta)=\theta^2$を入れると$T^2=-\theta^2I_2$．これを級数$\mathrm{e}^{T}=\sum_kT^k/k!$の偶数次・奇数次に代入すると$\mathrm{e}^{T}=\cos\theta\,I_2+(\sin\theta/\theta)\,T$が出る．$\mathrm{i}aI_2$は$T$と可換なので指数が分離し，本文の式になる．Pauli行列で$T=\mathrm{i}(b_x\sigma_x+b_y\sigma_y+b_z\sigma_z)$と書けば$\theta=|b|$で，量子計算で頻出の$\mathrm{e}^{\mathrm{i}\,\boldsymbol{b}\cdot\boldsymbol{\sigma}}=\cos|b|\,I_2+\mathrm{i}\sin|b|\,(\hat{\boldsymbol{b}}\cdot\boldsymbol{\sigma})$と同じ式である．

:::

検算で使う道具をコードにまとめる．`np.sinc(x)`は$\sin(\pi x)/(\pi x)$なので，`np.sinc(theta / np.pi)`が$\sin\theta/\theta$を（$\theta=0$も込みで）計算する．

```python
def skew(M):
    return (M - M.conj().T) / 2

def expm_aherm2(S):
    a = (S[0, 0] + S[1, 1]).imag / 2   # S = i*a*I + T with T traceless
    T = S - 1j * a * np.eye(2)
    theta = np.sqrt(max(-(T @ T)[0, 0].real, 0.0))
    return np.exp(1j * a) * (np.cos(theta) * np.eye(2) + np.sinc(theta / np.pi) * T)

def gd_unitary(grad, U0, eta, iters):
    U = U0.astype(complex)
    for _ in range(iters):
        U = expm_aherm2(-eta * skew(grad(U) @ U.conj().T)) @ U
    return U
```

## 実践1: $O(2)$による対称行列の対角化

実対称行列$H\in\mathbb{R}^{2\times2}$の固有ベクトルを勾配法で探す．直交行列$Q=(q_1\ q_2)$による相似変換$Q^\top HQ$の非対角成分を目的函数にする:

$$
f(Q)=\frac{1}{4}\bigl\|E(Q)\bigr\|_\mathrm{F}^2,\qquad E(Q)\coloneqq Q^\top HQ-\operatorname{diag}(Q^\top HQ) .
$$

$f(Q)=0$となるのは$Q^\top HQ$が対角行列，すなわち$Q$の列が$H$の固有ベクトルのときである．Euclid勾配は

$$
\nabla f=HQE(Q)
$$

と求まる（下のdetails）．$\mathfrak{o}(2)=\mathbb{R}J$は1次元なので$S_k=\operatorname{skew}(\nabla f\,Q^\top)$は$J$のスカラー倍$S_k=s_kJ$となり，$\mathrm{e}^{-\eta S_k}$は角度$-\eta s_k$の回転行列である．つまり更新のすべては「フレーム（$Q$の2本の列ベクトル）を少し回す」ことに尽きる．

ここでも角度に落として手を動かす．$H=\begin{pmatrix}a&b\\b&c\end{pmatrix}$，$Q(\theta)=\mathrm{e}^{\theta J}$（角度$\theta$の回転行列）とおいて$Q^\top HQ$の非対角成分を加法定理で整理すると

$$
m_{12}(\theta)=b\cos2\theta-\frac{a-c}{2}\sin2\theta
$$

となる（確かめてほしい）．$2\theta$しか現れないので$m_{12}(\theta+\pi/2)=-m_{12}(\theta)$であり，コスト$f=\frac12m_{12}^2$の谷が$\pi/2$おきに並ぶことがこの時点でわかる（図3(b)．固有ベクトルの組が列の入れ替え・符号反転の分だけ等価に存在することの現れである）．$m_{12}(\theta^*)=0$を解けば

$$
\tan2\theta^*=\frac{2b}{a-c}
$$

で，これは[Jacobi法](https://en.wikipedia.org/wiki/Jacobi_eigenvalue_algorithm)の回転角の公式そのものである．対角成分にも同じ整理を当てれば固有値

$$
\lambda_\pm=\frac{a+c}{2}\pm\sqrt{b^2+\Bigl(\frac{a-c}{2}\Bigr)^2}
$$

が手に入る．

行列側の更新と角度側の勾配法の換算も1行で確かめられる．$Q(\theta+t)=\mathrm{e}^{tJ}Q(\theta)$なので

$$
f'(\theta)=\left.\frac{d}{dt}f\bigl(\mathrm{e}^{tJ}Q\bigr)\right|_{t=0}=\langle S,J\rangle_{\mathbb{R}}=s\operatorname{tr}(J^\top J)=2s .
$$

つまり行列側の一歩（角度$-\eta s$の回転）は，角度側では$\theta\leftarrow\theta-\frac{\eta}{2}f'(\theta)$に当たる．$U(1)$では$S=\mathrm{i}f'(\theta)$と係数のずれがなかったが，それは生成子$\mathrm{i}$のノルムが$\langle\mathrm{i},\mathrm{i}\rangle_{\mathbb{R}}=1$だったからで，こちらは$\|J\|_\mathrm{F}^2=2$のぶん換算率が変わる．同じ円周でも，$\mathbb{C}$の中の$U(1)$と$\mathbb{R}^{2\times2}$の中の$SO(2)$では埋め込みの物差しが違うのである．

```python
def rot(t):
    return np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])

H = np.array([[2.0, 0.8], [0.8, 1.0]])
eta = 0.4
Q = rot(np.deg2rad(-9.0))                # start: a slightly rotated frame
for _ in range(100):
    M = Q.T @ H @ Q
    E = M - np.diag(np.diag(M))
    G = H @ Q @ E                        # Euclidean gradient
    S = (G @ Q.T - Q @ G.T) / 2          # = s * J
    Q = rot(-eta * S[1, 0]) @ Q          # expm(-eta*S) is a rotation
print(np.round(Q.T @ H @ Q, 8))   # -> diag(2.44339811, 0.55660189)
print(np.linalg.eigvalsh(H))      # -> [0.55660189 2.44339811]
```

$Q^\top HQ$が対角化され，対角成分は`eigvalsh`の固有値と（並び順を除いて）一致した．手計算の公式とも突き合わせておく．$H=\begin{pmatrix}2&0.8\\0.8&1\end{pmatrix}$では$\tan2\theta^*=1.6$より$\theta^*\approx29.0^\circ$，$\lambda_\pm=1.5\pm\sqrt{0.89}\approx2.4434,\ 0.5566$で，どちらも出力と一致する．図3(a)は2次形式の等高線$x^\top Hx=1$（楕円）とフレームの動きで，列ベクトル対が楕円の主軸へ向きを合わせていく．図3(b)は回転角$\theta$を横軸に取ったコストの風景で，反復は最寄りの谷$\theta^*$に落ちる．

![O(2) frame aligning with the principal axes of the quadratic form](/images/intro-matrix-manifold-optimization/o2-diagonalize.png)
*図3: $O(2)$上の勾配降下による$2\times2$対称行列の対角化（$\eta=0.4$）．(a) フレーム$Q=(q_1\ q_2)$が等高線$x^\top Hx=1$の主軸に向きを合わせていく．矢印は$q_1$（青系）と$q_2$（緑系）を表し，色は反復が進むほど濃い．破線は$H$の固有ベクトルの張る軸．(b) 回転角$\theta$で見たコストと反復列．*

なお，$\tan2\theta^*$の角をそのまま使って非対角成分を1回で消し，これを$n\times n$の$2\times2$部分問題に繰り返し当てるのが固有値算法としてのJacobi法である．いまの勾配法は，同じ角へ勾配を頼りに少しずつ近づいていく方法だと言える．

:::message

$O(2)$は$\det Q=+1$（回転）と$\det Q=-1$（鏡映）の2つの連結成分に分かれる．$\mathrm{e}^{-\eta S}$を掛ける更新は$\det Q$を変えないので，反復は初期値と同じ成分の中に留まる．対角化では両方の成分に大域解（固有ベクトルの一方の符号を反転したもの）があるため支障はないが，「指数因子$\mathrm{e}^{-\eta S}$は単位元を含む成分$SO(2)$に属するので，これを掛ける更新は連結成分をまたげない」ことは覚えておく価値がある．複素の$U(n)$は連結なのでこの問題は起きない．

:::

:::details 対角化コストの勾配の導出

$M\coloneqq Q^\top HQ$とおく．$f=\frac14\operatorname{tr}(E^\top E)$より$df=\frac12\langle E,dE\rangle$（実行列では$\langle A,B\rangle_{\mathbb{R}}=\operatorname{tr}(A^\top B)$）．$E$の対角は$0$なので対角部分との内積が消え，$\langle E,dE\rangle=\langle E,dM\rangle$．$dM=dQ^\top HQ+Q^\top HdQ$を代入し，$E^\top=E$と$H^\top=H$を使って2項をまとめると

$$
df=\frac12\Bigl(\operatorname{tr}(E\,dQ^\top HQ)+\operatorname{tr}(EQ^\top HdQ)\Bigr)=\operatorname{tr}\bigl((HQE)^\top dQ\bigr)=\langle HQE,dQ\rangle
$$

となり，$\nabla f=HQE$を得る．

:::

## 実践2: $U(2)$のユニタリProcrustes問題

複素の$U(2)$では，厳密解がわかっている問題を勾配法で解いて突き合わせる．与えられた$A,B\in\mathbb{C}^{2\times2}$に対するユニタリProcrustes問題

$$
\min_{U\in U(2)}f(U),\qquad f(U)=\|UA-B\|_\mathrm{F}^2
$$

の解は，$BA^\dagger$の特異値分解$BA^\dagger=W\Sigma V^\dagger$を用いて$U^*=WV^\dagger$，すなわち$BA^\dagger$の極分解のユニタリ因子である[^procrustes]．Euclid勾配は

$$
\nabla f=2(UA-B)A^\dagger
$$

と求まる（下のdetails）．

コードの前に，特殊形（$A=I_2$，すなわち[以前の記事](https://zenn.dev/ultimatile/articles/unitary-procrustes)の「最も近いユニタリ行列」問題）を1つ手で回してみる．

$$
B=\begin{pmatrix}0&2\\-1&0\end{pmatrix}
$$

とすると$B^\top B=\operatorname{diag}(1,4)$なので，極分解$B=U^*P$の因子は$P=\operatorname{diag}(1,2)$，$U^*=BP^{-1}=\begin{pmatrix}0&1\\-1&0\end{pmatrix}=\mathrm{e}^{-\frac{\pi}{2}J}$と手で求まる（特異値分解を経由せずに済むのは，$B^\top B$が対角になるようにインスタンスを仕込んだからである）．勾配法を$U_0=I_2$から始めると，$\operatorname{skew}(I_2)=0$より

$$
S_0=\operatorname{skew}\bigl(2(U_0-B)U_0^\dagger\bigr)=-2\operatorname{skew}(B)=3J,\qquad U_1=\mathrm{e}^{-3\eta J}
$$

で，最初の一歩は厳密解$\mathrm{e}^{-\frac{\pi}{2}J}$へ向かう角度$-3\eta$の回転になる（$\eta=\pi/18$なら1歩で行程のちょうど$1/3$が進む）．実際$U=\mathrm{e}^{\theta J}$とおくと$f(\theta)=7+6\sin\theta$，$s=3\cos\theta=f'(\theta)/2$と前節の換算則どおりに円の問題へ帰着するので，2歩目以降も手で追える（確かめてほしい）．4次元の$U(2)$をフルに使う一般の複素インスタンスは乱数で作り，数値で検算する．更新則はこれまでとまったく同じ形で，コードは`gd_unitary`に勾配を渡すだけである．

```python
rng = np.random.default_rng(7)
A = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
B = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))

U = gd_unitary(lambda U: 2 * (U @ A - B) @ A.conj().T, np.eye(2), eta=0.15, iters=2000)

W, _, Vh = np.linalg.svd(B @ A.conj().T)           # exact answer
print(np.linalg.norm(U - W @ Vh))                  # 4.5e-10
print(np.linalg.norm(U.conj().T @ U - np.eye(2)))  # 1.4e-14
```

2000反復で厳密解と$10^{-10}$の桁まで一致し，ユニタリ性は機械精度で保たれている[^critical]．

図4は3種類の更新則の比較である．

- 乗法的更新（本記事の方法）: $U\leftarrow\mathrm{e}^{-\eta S}U$．
- 加法的更新＋極分解射影: $U-\eta\nabla f$と動かしてから，最も近いユニタリ行列（極因子）へ射影する．円の$w/|w|$と同じ射影付き勾配法の流儀で，射影は特異値分解または[Newton-Schulz反復](https://zenn.dev/ultimatile/articles/unitary-procrustes-newton-schulz)で計算できる．
- 素朴な加法的更新: 射影せず$U-\eta\nabla f$のまま進む．

図4(a)のとおり，素朴な加法更新のコストは厳密解の値$f(U_{\mathrm{SVD}})$を下回ってどこまでも下がる．制約を無視すれば$UA=B$を厳密に解く$U=BA^{-1}$（一般にユニタリでない）まで行けるからで，「コストは下がっているのに答えから遠ざかる」典型例である．図4(b)のとおり多様体からの距離は$O(1)$まで育つ．一方，乗法的更新と射影つきの加法的更新はどちらも$10^{-15}$前後に張り付き，収束の速さもこの例ではほとんど変わらない．

![cost and unitarity error for the three update rules](/images/intro-matrix-manifold-optimization/u2-procrustes.png)
*図4: ユニタリProcrustes問題での3更新則の比較（$\eta=0.15$）．(a) コスト$f(U_k)$．素朴な加法更新（赤）は制約を破り，厳密解の値$f(U_{\mathrm{SVD}})$（点線）を下回っていく．(b) 多様体からの距離$\|U_k^\dagger U_k-I\|_\mathrm{F}$．乗法的更新（青）と加法的更新＋極分解射影（緑）は機械精度に張り付く．*

:::details Procrustesコストの勾配の導出

$R\coloneqq UA-B$とおくと$f=\operatorname{tr}(R^\dagger R)$，$dR=dU\,A$．よって

$$
df=\operatorname{tr}(dR^\dagger R)+\operatorname{tr}(R^\dagger dR)=2\operatorname{Re}\operatorname{tr}(R^\dagger dU\,A)=2\operatorname{Re}\operatorname{tr}\bigl((RA^\dagger)^\dagger dU\bigr)=\langle2RA^\dagger,dU\rangle_{\mathbb{R}}
$$

となり（3つ目の等号はトレースの巡回性），$\nabla f=2RA^\dagger=2(UA-B)A^\dagger$を得る．

:::

## Stiefel多様体との関係

ここまでLie群$U(n)$・$O(n)$だけで話を進めた．最後に，教科書で主役を張るStiefel多様体との関係を整理する．$\mathbb{K}=\mathbb{R}$または$\mathbb{C}$に対して

$$
\mathrm{St}(n,p)\coloneqq\{X\in\mathbb{K}^{n\times p}\mid X^\dagger X=I_p\}
$$

を[Stiefel多様体](https://en.wikipedia.org/wiki/Stiefel_manifold)と呼ぶ．列が正規直交する縦長行列，言い換えると正規直交な$p$本組（フレーム）の全体である．端のケースは既出の空間になる．

- $p=n$: $U(n)$・$O(n)$そのもの（本記事の舞台）．
- $p=1$: 単位球面．実で$n=2$なら$\mathrm{St}_{\mathbb{R}}(2,1)=S^1$．

つまり本記事に登場した空間はすべてStiefel多様体の特別な場合である．円$S^1$にいたっては，$U(1)$（$1\times1$のユニタリ行列）と$\mathrm{St}_{\mathbb{R}}(2,1)$（$\mathbb{R}^2$の単位ベクトル）という2通りの読み方を持つ[^sphere-group]．

$p<n$で決定的に変わるのは群構造の有無である．縦長行列同士は掛け合わせられないので$\mathrm{St}(n,p)$は群でなく，単位元も固有のLie代数も持たない．接空間は制約の微分から

$$
T_X\mathrm{St}(n,p)=\{\Delta\in\mathbb{K}^{n\times p}\mid X^\dagger\Delta+\Delta^\dagger X=0\}
$$

と書け，その標準形は$\Delta=X\Omega+X_\perp K$である（$\Omega\in\mathfrak{u}(p)$，$K$は任意の$(n-p)\times p$行列，$X_\perp$は$X$の直交補空間の正規直交基底．[Boumal](https://www.nicolasboumal.net/book/)の7.3節を参照）．

ただし，群でないからといって乗法的更新が書けなくなるわけではない．任意の接ベクトル$\Delta=X\Omega+X_\perp K$に対して

$$
\widehat\Omega\coloneqq X\Omega X^\dagger+X_\perp KX^\dagger-XK^\dagger X_\perp^\dagger
$$

とおくと，$\widehat\Omega$は$n\times n$の反Hermite行列で$\widehat\Omega X=\Delta$を満たし（$X^\dagger X=I_p$と$X_\perp^\dagger X=0$を使うだけなので確かめてほしい），$\mathrm{e}^{t\widehat\Omega}X$は制約$X^\dagger X=I_p$を厳密に保つ．$p<n$で失われるのは「書けること」ではなく，次の2つである．

- 一意性: 群では接ベクトルと生成子が$\Omega=\dot UU^\dagger$で1対1に対応した．一方$\mathrm{St}(n,p)$では，同じ$\Delta$を実現する反Hermite行列$\widehat\Omega$が無数にあり（上の式はその1つの選び方にすぎない），生成子が多様体に固有のLie代数の元として決まらない．
- 経済性: $\mathrm{St}(n,p)$の自由度は$np$のオーダーしかないのに，$n\times n$の生成子を持ち回ると記憶量も指数函数の計算量も$n^2$のオーダーに膨れる．$p\ll n$ではこの無駄が効いてくる．

そこで実用では，$n\times p$行列のまま「接方向へ動いてから多様体へ戻す」レトラクションが主役になる．よく使われるのは次の3つである．

- QRレトラクション: $X+\Delta$をQR分解して直交因子$Q$を取る．
- 極分解レトラクション: $X+\Delta$に最も近い（半）ユニタリ行列，すなわち極因子を取る．円の$w/|w|$の一般化で，計算には特異値分解または[Newton-Schulz反復](https://zenn.dev/ultimatile/articles/unitary-procrustes-newton-schulz)が使える．
- Cayley変換: 上の$\widehat\Omega$を使い$X\mapsto\bigl(I-\frac{t}{2}\widehat\Omega\bigr)^{-1}\bigl(I+\frac{t}{2}\widehat\Omega\bigr)X$と更新する．指数写像$\mathrm{e}^{t\widehat\Omega}X$を有理式で近似したもので，これも制約を厳密に保つ．

あるいは$\mathrm{St}(n,p)=U(n)/U(n-p)$（実なら$O(n)/O(n-p)$）という商（[等質空間](https://en.wikipedia.org/wiki/Homogeneous_space)）の見方を使えば，$U(n)$の測地線から$\mathrm{St}(n,p)$の厳密な測地線も導ける[^eas]．ここで計量にひとつ注意がある．商構造から自然に定まる計量（canonical metric）は，本記事でずっと使ってきた「埋め込み空間のFrobenius内積を接空間に制限した計量」とは一般に別物で，$p=1$と$p=n$では両者が一致するが，$1<p<n$では測地線もRiemann勾配も異なる[^eas]．どの道具を選んでも，「接空間で方向を決め，多様体の上へ戻る」という骨格は図1と変わらない．

| | $U(n)$・$O(n)$（$p=n$） | $\mathrm{St}(n,p)$（$p<n$） |
| ---- | ---- | ---- |
| 群構造 | あり（Lie群） | なし（等質空間$U(n)/U(n-p)$） |
| 接空間 | $\{\Omega U\mid\Omega\in\mathfrak{u}(n)\}$ | $\{\Delta\mid X^\dagger\Delta+\Delta^\dagger X=0\}$ |
| 制約を保つ更新 | $\mathrm{e}^{-\eta S}U$（測地線が閉形式） | レトラクションか商構造の測地線（$\mathrm{e}^{t\widehat\Omega}X$も書けるが生成子は非一意・冗長） |
| 本記事での例 | $S^1=U(1)$，$O(2)$，$U(2)$ | $S^1=\mathrm{St}_{\mathbb{R}}(2,1)$，球面 |

教科書がStiefel多様体を軸に置くのは，応用の主戦場が$p\ll n$だからである．上位$p$本の固有ベクトル・特異ベクトルの計算や直交制約つきの重み行列など，実務の制約は縦長の行列に現れることが多く，$U(n)$へ持ち上げると$n^2$個の自由度を持ち回ることになって無駄が大きい．さらに目的函数が$X$の列の張る部分空間$\operatorname{span}(X)$にしか依存しないなら，もう1段商を取った[Grassmann多様体](https://en.wikipedia.org/wiki/Grassmannian)が舞台になる．逆に$p=n$の世界ではLie群の道具（Lie代数・指数写像・閉形式の測地線）が全部使える．入門の足場としてはこちらが向いている，というのが本記事の立場である．

## まとめ

- ユニタリ制約つき最小化$\min_{U\in U(n)}f(U)$の勾配法は，Euclid勾配$\nabla f$から反Hermite行列$S=\operatorname{skew}(\nabla f\,U^\dagger)\in\mathfrak{u}(n)$を作り，$U\leftarrow\mathrm{e}^{-\eta S}U$と乗法的に回すだけで書ける．制約は機械精度で保たれる．
- 円$S^1=U(1)$の上では，接空間・Lie代数・指数写像・Riemann勾配・レトラクションのすべてが2次元平面の図になり，計算は極座標の微分に落ちる．$O(2)$でも自由度は角度1個で，対角化の勾配法はJacobi法の回転角の公式まで手計算でつながる．
- $p<n$のStiefel多様体でも反Hermite生成子による乗法的更新$\mathrm{e}^{t\widehat\Omega}X$は書けるが，生成子が非一意で$n\times n$と冗長になるため，実用ではレトラクションや商構造の測地線が更新の道具になる．$p=n$のLie群はStiefel多様体の特別な場合であり，教科書がStiefel多様体から始めるのは応用が$p\ll n$に集中しているためである．

## 文献案内

- [P.-A. Absil, R. Mahony, R. Sepulchre, _Optimization Algorithms on Matrix Manifolds_ (Princeton University Press, 2008)](https://sites.uclouvain.be/absil/amsbook/): 行列多様体上の最適化の定番教科書．公式ページで全文が公開されている．
- [N. Boumal, _An Introduction to Optimization on Smooth Manifolds_ (Cambridge University Press, 2023)](https://www.nicolasboumal.net/book/): より新しい教科書．著者ページでPDFが公開されている．
- [佐藤寛之『多様体上の最適化理論』（オーム社，2024）](https://www.ohmsha.co.jp/book/9784274231186/): 日本語の体系的な教科書．
- [A. Edelman, T. A. Arias, S. T. Smith, "The Geometry of Algorithms with Orthogonality Constraints" (1998)](https://arxiv.org/abs/physics/9806030): Stiefel・Grassmann多様体上のアルゴリズムの幾何を確立した古典論文．
- ライブラリ: [Manopt](https://www.manopt.org)（MATLAB）・[pymanopt](https://pymanopt.org)（Python）・[geoopt](https://github.com/geoopt/geoopt)（PyTorch）．多様体と目的函数を与えると各種のRiemann最適化を実行してくれる．

[^books]: 定番は[Absil, Mahony, Sepulchre](https://sites.uclouvain.be/absil/amsbook/)と[Boumal](https://www.nicolasboumal.net/book/)で，どちらも無料で全文が読める．日本語では[佐藤寛之『多様体上の最適化理論』](https://www.ohmsha.co.jp/book/9784274231186/)がある．文献案内の節も参照．

[^retraction]: 正確には，レトラクションは「接ベクトルから多様体上の点への滑らかな写像$R_U(\xi)$で，$R_U(0)=U$かつ$\frac{d}{dt}R_U(t\xi)\big|_{t=0}=\xi$を満たすもの」（指数写像の1次近似の族）として定義され，Riemann最適化の標準的な一歩は接ベクトルに適用する$R_z(-\eta\operatorname{grad}f)$である（円では$R_z(\xi)=(z+\xi)/|z+\xi|$がその一例）．一方，本文の$w/|w|$は周囲空間の勾配で動いた点$w=z-\eta\nabla f$を円へ射影するもので，これは射影付き勾配法に当たる．両者は$\eta$の1次では一致するが，有限のステップ幅では一般に別の点を与える．Absil et al. の4章を参照．

[^bracket]: Lie代数という名前は，交換子$[\Omega_1,\Omega_2]\coloneqq\Omega_1\Omega_2-\Omega_2\Omega_1$（反Hermite行列同士の交換子はまた反Hermite）という積の構造まで込めた呼び名である．本記事ではこの積は使わず，「単位元での接空間」としてだけ扱う．

[^geodesic]: Frobenius内積の実部を各接空間に制限した計量は$U(n)$上で両側不変（左右どちらの群作用でも不変）になり，$\mathrm{e}^{t\Omega}U$型の曲線はこの計量の測地線である．本文の更新則が「測地線に沿ったRiemann最急降下」であることの正確な意味づけは文献案内の教科書を参照．

[^procrustes]: 標準形のユニタリProcrustes問題の解については[Newton-Schulz法の記事](https://zenn.dev/ultimatile/articles/unitary-procrustes-newton-schulz)の脚注，特殊形（$A=I_n$）の導出は[最も近いユニタリ行列の記事](https://zenn.dev/ultimatile/articles/unitary-procrustes)を参照．展開$f(U)=\|A\|_\mathrm{F}^2+\|B\|_\mathrm{F}^2-2\operatorname{Re}\operatorname{tr}(U^\dagger BA^\dagger)$から，最大化すべき項が$\operatorname{Re}\operatorname{tr}(U^\dagger BA^\dagger)$だけになることを使う．

[^critical]: 停留条件$S=0$は$BA^\dagger U^\dagger$のHermite性と同値になる（$\nabla f\,U^\dagger=2(UAA^\dagger U^\dagger-BA^\dagger U^\dagger)$の第1項はつねにHermite）．$BA^\dagger$の特異値が相異なり正なら停留点は$U=W\operatorname{diag}(\pm1,\pm1)V^\dagger$の4点に限られる．$\operatorname{diag}(1,1)$が大域解で，残りは極小でない．そのため典型的な初期値からの勾配法は大域解に到達する（本記事の実験でも同様）．

[^sphere-group]: 単位球面$S^{d}$が群の構造（正確にはLie群の構造）を持てるのは$S^0$（実数の単位元集合）・$S^1$（複素数）・$S^3$（四元数）に限られることが知られている．円で群の道具がそのまま使えるのはこの例外に当たっている．

[^eas]: [Edelman, Arias, Smith (1998)](https://arxiv.org/abs/physics/9806030)．Stiefel多様体を商$U(n)/U(n-p)$とみなした測地線や，Grassmann多様体上のNewton法・共役勾配法の公式がまとまっている．埋め込み由来のFrobenius計量と商由来のcanonical metricが一般には異なることも，この論文が明示的に論じている．
