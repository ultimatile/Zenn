---
title: "虚時間発展と最急降下法の関係"
emoji: "📉"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["量子力学", "物理"]
published: true
---

## はじめに

量子力学において，系の基底状態（エネルギー最小の状態）を求める手法として虚時間発展がよく用いられる．一方，最適化の文脈では最急降下法が基本的な手法として知られている．本記事では，Rayleigh商の最小化問題に対する最急降下法が，虚時間発展（の一種）と等価であることを示す．

## セットアップと記法

[ブラケット記法](https://ja．wikipedia．org/wiki/%E3%83%96%E3%83%A9-%E3%82%B1%E3%83%83%E3%83%88%E8%A8%98%E6%B3%95)を用いる．

- $\mathcal{H}$: Hermite演算子（ハミルトニアン）
- $|\psi\rangle \in \mathbb{C}^n$: 状態ベクトル
- $\{|\psi_k\rangle\}_{k=1}^n$: 正規直交基底，すなわち$\langle\psi_i|\psi_j\rangle = \delta_{ij}$
- $c_k \in \mathbb{C}$: 展開係数，$|\psi\rangle = \sum_k c_k |\psi_k\rangle$
- $|\nabla_{\boldsymbol{z}^*} f\rangle$: $f$の$\boldsymbol{z}^*$に関するWirtinger勾配（[Wirtinger微分](https://ja．wikipedia．org/wiki/%E3%82%A6%E3%82%A3%E3%83%AB%E3%83%86%E3%82%A3%E3%83%B3%E3%82%AC%E3%83%BC%E3%81%AE%E5%BE%AE%E5%88%86)$\partial f / \partial z_i^*$を各成分に並べたベクトル）

最小化したい目的函数はRayleigh商

$$
E = \frac{\langle\psi|\mathcal{H}|\psi\rangle}{\langle\psi|\psi\rangle}
$$

である．これは状態$|\psi\rangle$のエネルギーを表し，$|\psi\rangle$が$\mathcal{H}$の固有状態のとき対応する固有値に一致する．

## 実値函数$f$の最急降下方向は$\boldsymbol{z}^*$に関する勾配だけで書ける

実値函数$f: \mathbb{C}^n \to \mathbb{R}$に対して変数$|z\rangle \in \mathbb{C}^n$を$|z\rangle+|\mathrm{d}z\rangle$と変化させたときの$f$の変化量$\mathrm{d}f$は

$$
\mathrm{d}f = 2 \mathrm{Re}\langle\nabla_{\boldsymbol{z}^*} f | \mathrm{d}z\rangle \tag{1}
$$

であることから，$\mathrm{d}f$を最小化させる最急降下方向$|\mathrm{d}z\rangle$は$-|\nabla_{\boldsymbol{z}^*}f\rangle$であることがわかる．実際，$\mathrm{Re}\langle a | b \rangle = \|a\|\|b\|\cos\theta$（$\theta$は$|a\rangle$と$|b\rangle$のなす角）なので，$|b\rangle$が$|a\rangle$と反平行($\ket{b}=-\ket{a}$)のとき$\cos\theta = -1$で最小となる．

:::details 式(1)の導出
$|z\rangle \in \mathbb{C}^n$の各要素$z_i \in \mathbb{C}$を$z_i=x_i+\mathrm{i}y_i$, ($x_i, y_i \in \mathbb{R}$)と書くと，
$f:\mathbb{R}^{2n}\to\mathbb{R}$と見て，全微分$\mathrm{d}f$は

$$
\mathrm{d}f=\sum_i \left( \frac{\partial f}{\partial x_i} \mathrm{d}x_i + \frac{\partial f}{\partial y_i} \mathrm{d}y_i\right) \tag{2}
$$

と書ける．

Wirtinger微分の表式

$$
\frac{\partial}{\partial z} := \frac{1}{2} \left(\frac{\partial}{\partial x} - \mathrm{i} \frac{\partial}{\partial y}\right), \quad
\frac{\partial}{\partial z^*} := \frac{1}{2} \left(\frac{\partial}{\partial x} + \mathrm{i} \frac{\partial}{\partial y}\right) \tag{3}
$$

から

$$
\frac{\partial}{\partial x} = \frac{\partial}{\partial z} + \frac{\partial}{\partial z^*}, \quad
\frac{\partial}{\partial y} = \mathrm{i}\left(\frac{\partial}{\partial z} - \frac{\partial}{\partial z^*}\right)
$$

であることがわかるので，$x=(z+z^*)/2, y=(z-z^*)/(2\mathrm{i})$と合わせて式(2)を書き直すと

$$
\begin{aligned}
\mathrm{d}f&=\sum_i \frac{\partial f}{\partial x_i} \mathrm{d}x_i + \sum_i \frac{\partial f}{\partial y_i} \mathrm{d}y_i\\
&=\sum_i \left(\left(\frac{\partial f}{\partial z_i} + \frac{\partial f}{\partial z_i^*}\right)\frac{\mathrm{d}z_i+\mathrm{d}z_i^*}{2}
+\mathrm{i}\left(\frac{\partial f}{\partial z_i} - \frac{\partial f}{\partial z_i^*}\right)\frac{\mathrm{d}z_i-\mathrm{d}z_i^*}{2\mathrm{i}}\right)\\
&=\sum_i \left(\frac{\partial f}{\partial z_i}\mathrm{d}z_i +\frac{\partial f}{\partial z_i^*}\mathrm{d}z_i^*\right)．
\end{aligned}
$$

ここで，$f$が実値函数であることより$\frac{\partial f}{\partial x_i}$, $\frac{\partial f}{\partial y_i}$も実数であることが従うので，

$$
\left(\frac{\partial f}{\partial z_i}\right)^* =\frac{1}{2}\left(\left(\frac{\partial f}{\partial x_i}\right)^*-\mathrm{i}\left(\frac{\partial f}{\partial y_i}\right)^*\right)
=\frac{1}{2}\left(\frac{\partial f}{\partial x_i}-\mathrm{i} \frac{\partial f}{\partial y_i}\right)
=\frac{\partial f}{\partial z_i^*}
$$

が成り立ち，

$$
\mathrm{d}f =\sum_i \left(\frac{\partial f}{\partial z_i}\mathrm{d}z_i +\left(\frac{\partial f}{\partial z_i}\right)^*\mathrm{d}z_i^*\right)
=\sum_i \left(\frac{\partial f}{\partial z_i}\mathrm{d}z_i +\left(\frac{\partial f}{\partial z_i}\mathrm{d}z_i\right)^*\right)
=\sum_i 2\mathrm{Re}\left(\frac{\partial f}{\partial z_i}\mathrm{d}z_i\right)
$$

となる．ブラケット表記にすると

$$
\mathrm{d}f=2\mathrm{Re}\langle(\nabla_{\boldsymbol{z}}f)^*| \mathrm{d}z\rangle=2\mathrm{Re}\langle\nabla_{\boldsymbol{z}^*}f| \mathrm{d}z\rangle
$$

となり，式(1)が得られる．
:::

## $E=\langle\psi|\mathcal{H}|\psi\rangle / \langle\psi|\psi\rangle$に対する$\boldsymbol{z}^*$勾配の計算

時刻$t$でのエネルギー期待値を

$$
E(t) = \frac{\langle\psi(t)|\mathcal{H}|\psi(t)\rangle}{\langle\psi(t)|\psi(t)\rangle}
$$

と定義する．以下では簡単のため$t$依存性を省略して$E$, $|\psi\rangle$と書く．

ある$k$に対する$E$の$c_k^*$微分は

$$
\frac{\partial E}{\partial c^*_k}=\frac{(\frac{\partial}{\partial c^*_k}\langle\psi|\mathcal{H}|\psi\rangle)\langle\psi|\psi\rangle-\langle\psi|\mathcal{H}|\psi\rangle\frac{\partial}{\partial c^*_k}\langle\psi|\psi\rangle}{\langle\psi|\psi\rangle^2}
=\frac{\frac{\partial}{\partial c^*_k}\langle\psi|\mathcal{H}|\psi\rangle}{\langle\psi|\psi\rangle}
-\frac{E \frac{\partial}{\partial c^*_k}\langle\psi|\psi\rangle}{\langle\psi|\psi\rangle}
$$

となる．

$c_k^*$微分はブラにしか当たらないので

$$
\frac{\partial}{\partial c^*_k}\langle\psi| = \sum_i \frac{\partial c_i^*}{\partial c^*_k}\langle\psi_i|=\sum_i \delta_{ik} \langle\psi_i|=\langle\psi_k|
$$

となる．よって

$$
\frac{\partial E}{\partial c^*_k}=\frac{\langle\psi_k|\mathcal{H}|\psi\rangle}{\langle\psi|\psi\rangle}
-\frac{E \langle\psi_k|\psi\rangle}{\langle\psi|\psi\rangle}
=\frac{\langle\psi_k|(\mathcal{H}-E)|\psi\rangle}{\langle\psi|\psi\rangle}
$$

となる．

$\boldsymbol{c}^*$勾配ベクトル$|\nabla_{\boldsymbol{c}^*}E\rangle$は

$$
|\nabla_{\boldsymbol{c}^*}E\rangle =\sum_k \frac{\partial E}{\partial c^*_k} |\psi_k\rangle
= \sum_k \frac{ |\psi_k\rangle\langle\psi_k|(\mathcal{H}-E)|\psi\rangle}{\langle\psi|\psi\rangle}．
$$

正規直交基底の完全性$\sum_k |\psi_k\rangle\langle\psi_k|=1$より，

$$
|\nabla_{\boldsymbol{c}^*}E\rangle=\frac{(\mathcal{H}-E)|\psi\rangle}{\langle\psi|\psi\rangle}．
$$

## まとめ：虚時間発展と最急降下法の対応

以上より，$E(t)$に対する最急降下法の更新則は

$$
|\psi(t+\mathrm{d}t)\rangle = |\psi(t)\rangle - \eta (\mathcal{H} - E(t)) |\psi(t)\rangle
$$

で与えられる．ここで$\eta > 0$は学習率である．

勾配流（$\eta \to 0$の連続極限）を考えれば

$$
|\dot{\psi}(t)\rangle = - (\mathcal{H} - E(t)) |\psi(t)\rangle
$$

となる．これは通常の虚時間Schrödinger方程式$|\dot{\psi}\rangle = -\mathcal{H}|\psi\rangle$に，エネルギー期待値$E(t)$によるシフトが加わった形になっている．

:::details 補足：ノルム保存について
$E$によるシフトにより，ノルムの2乗$\langle\psi|\psi\rangle$が時間発展で保存される．
実際，$\mathcal{H}$のHermite性と$E$の実数性から

$$
\frac{\mathrm{d}}{\mathrm{d}t}\langle\psi|\psi\rangle = \langle\dot{\psi}|\psi\rangle + \langle\psi|\dot{\psi}\rangle = -2\langle\psi|(\mathcal{H}-E)|\psi\rangle．
$$

ここで$E$の定義$E = \langle\psi|\mathcal{H}|\psi\rangle / \langle\psi|\psi\rangle$より

$$
\langle\psi|(\mathcal{H}-E)|\psi\rangle = \langle\psi|\mathcal{H}|\psi\rangle - E\langle\psi|\psi\rangle = 0
$$

となるので，

$$
\frac{\mathrm{d}}{\mathrm{d}t}\langle\psi|\psi\rangle = 0
$$

が示される．
:::
