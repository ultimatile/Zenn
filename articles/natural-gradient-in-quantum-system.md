---
title: "mytitle"
emoji: "📉"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["量子力学","物理"]
published: false
---

前回に引き続き基底状態探索を考える。
目的関数はエネルギー

$$
E = \frac{\braket{\psi|\mathcal{H}|\psi}}{\braket{\psi|\psi}}
$$

の最小化である。

前回の話では正規直交基底で展開していたことを思い出す。
つまり、状態が住んでいるHilbert空間の元が厳密に表示できていた。
今回は正規でも、直交でも、基底でもない場合にどうなるかを考える。
これはいわゆる変分法と呼ばれる手法で使われる設定である。
ノーテーションは前回と同様に$\ket{\psi}=\sum_i c_k \ket{\psi_k}$とする。
今回は正規でも直交でもないので$\braket{\psi_i|\psi_j} \neq \delta_{ij}$であることに注意する。

前回の議論を踏襲すると、まず「実値函数$f$の最急降下方向は$z^*$に関する勾配だけで書ける」というのは変わらない。
続いて、エネルギー$E$の勾配を計算する。

前回と同じ部分は省略すると
$\bm{c}^\ast$勾配ベクトルが

$$
|\nabla_{\boldsymbol{c}^*}E\rangle = \sum_k \frac{ |\psi_k\rangle\langle\psi_k|(\mathcal{H}-E)|\psi\rangle}{\langle\psi|\psi\rangle}．
$$

と書けるところまではいける。

前回使っていた完全性関係$\sum_k |\psi_k\rangle\langle\psi_k|=1$が使えない。
ここで$\langle\psi_k|(\mathcal{H}-E)|\psi\rangle$に$\ket{\psi}=\sum_j c_j \ket{\psi_j}$を代入すると

$$
\langle\psi_k|(\mathcal{H}-E)|\psi\rangle = \sum_j c_j \langle\psi_k|(\mathcal{H}-E)|\psi_j\rangle
$$
