---
title: "HΦによる量子系の実時間発展"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["hphi","c言語","quantum"]
published: false
---

## はじめに
閉じた量子系の時刻$t=t_\mathrm{begin}$から時刻$t=t_\mathrm{end}$のHamiltonian$\mathcal{H}(t)$による実時間発展^[実時間という言い方は，統計力学における逆温度$\beta\leftrightarrow\mathrm{i}t$という形式的対応から虚時間と呼ばれることに対するretronymです．英語で書くとreal-time dynamicsとかreal-time evolutionとかになりますが，量子系の時間発展の文脈では日常語のリアルタイムという意味ではないので注意して下さい．]は$\ket{\psi(t=t_\mathrm{begin})}$を初期状態として，unitary演算子$\mathcal{U}(t_1,t_2)$を用いて，

$$\ket{\psi(t=t_\mathrm{end})} = \mathcal{U}(t_1=t_\mathrm{end},t_2=t_\mathrm{begin})\ket{\psi(t=t_\mathrm{begin})}$$

と書けます．

$$
\mathcal{T}\mathrm{exp}\left(-\mathrm{i}\mathcal{H}_t\right)\ket{\psi_{t_0}}
$$

ここで時間を$N$等分する離散化を行い，$t_n\coloneqq n\Delta t$, $\Delta t \coloneqq (t-t_0)/N$とすると