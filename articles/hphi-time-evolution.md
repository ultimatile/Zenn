---
title: "HΦによる量子系の実時間発展"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["hphi","c言語","quantum"]
published: false
---

## はじめに
閉じた量子系の時刻$t=t_\mathrm{begin}$から時刻$t=t_\mathrm{end}$のHamiltonian$\mathcal{H}(t)$による実時間発展^[実時間という言い方は，統計力学における逆温度$\beta\leftrightarrow\mathrm{i}t$という形式的対応から虚時間と呼ばれることに対するretronymです．実時間発展を英語で書くとreal-time dynamicsとかreal-time evolutionとかになりますが，量子系の時間発展の文脈では日常語のリアルタイムという意味ではないので注意して下さい．]は$\ket{\psi(t=t_\mathrm{begin})}$を初期状態として，unitary演算子$\mathcal{U}(t_1,t_2)$を用いて，

$$\ket{\psi(t=t_\mathrm{end})} = \mathcal{U}(t_1=t_\mathrm{end},t_2=t_\mathrm{begin})\ket{\psi(t=t_\mathrm{begin})}$$

と書けます．

$$
\mathcal{T}\mathrm{exp}\left(-\mathrm{i}\mathcal{H}_t\right)\ket{\psi_{t_0}}
$$

ここで時間を$N$等分する離散化を行い，$t_n\coloneqq n\Delta t$, $\Delta t \coloneqq (t-t_0)/N$とすると

$S=1/2$の場合のBogoliubov表現は

$$
\begin{aligned}
& S^z_{i}=\frac12 \left(c_{i \uparrow}^{\dagger} c_{i \uparrow}^{}- c_{i \downarrow}^{\dagger} c_{i \downarrow}^{}\right)\\
& S_i^{+}=c_{i \uparrow}^{\dagger} c_{i\downarrow}^{} \\
& S_i^{-}=c_{i \downarrow}^{\dagger} c_{i \uparrow}^{}
\end{aligned}
$$

$$
\begin{aligned}
S^+_iS^-_j&=c_{i\uparrow}^{\dagger}c_{i\downarrow}^{}c_{j\downarrow}^{\dagger}c_{j \uparrow}^{}\\
S^-_iS^+_j&=c_{i\downarrow}^{\dagger}c_{i\uparrow}^{}c_{j\uparrow}^{\dagger}c_{j\downarrow}^{}\\
S^z_iS^z_j&=
\frac14 \left(c_{i\uparrow}^{\dagger}c_{i\uparrow}^{}-c_{i \downarrow}^{\dagger}c_{i\downarrow}^{}\right)
\left(c_{j\uparrow}^{\dagger}c_{j\uparrow}^{}-c_{j\downarrow}^{\dagger}c_{j\downarrow}^{}\right)\\
&=\frac14\left(c_{i\uparrow}^{\dagger}c_{i\uparrow}^{}c_{j\uparrow}^{\dagger}c_{j\uparrow}^{}
-c_{i\uparrow}^{\dagger}c_{i\uparrow}^{}c_{j\downarrow}^{\dagger}c_{j\downarrow}^{}
-c_{i \downarrow}^{\dagger}c_{i\downarrow}^{}c_{j\uparrow}^{\dagger}c_{j\uparrow}^{}
+c_{i \downarrow}^{\dagger}c_{i\downarrow}^{}c_{j\downarrow}^{\dagger}c_{j\downarrow}^{}
\right)
\end{aligned}
$$

`TwoBodyTE`
一般2体項は

$$
(\Re + \mathrm{i}\Im) c^{\dagger}_{i\sigma_i}c^{}_{j\sigma_j}c^{\dagger}_{k\sigma_k}c^{}_{l\sigma_l}
$$
の形に書けます．
spin演算子は同じsite $i$に作用する2点函数の形になるため，常に$i=j$かつ$k=l$として指定します．
変数の並びは
```
i sigmai j sigmaj k sigmak l sigmal Re Im
```
です．

upspin:0, downspin:1として指定します．

### $S^+_iS^-_j$

```
i 0 i 1 j 1 j 0 ReJ+- ImJ+-
```