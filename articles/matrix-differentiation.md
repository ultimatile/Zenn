---
title: "行列の微分の基本"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["微分", "行列", "線形代数"]
published: false
register: joutai
---

## はじめに

応用線形代数において行列の微分を考えることは基本的な概念である一方、非Euclid空間での微分の取り扱いを統一的に説明される機会はあまりなく、アドホックな計算規則として理解されることが多い。ここではFrobenius内積を用いた内積空間上でのFrechet微分の定義を用いて、行列の微分を統一的に説明する。

本記事では有限次元を仮定する。

## Frobenius内積

複素数値行列の集合を $\mathbb{C}^{m \times n}$ とする。ここで、Frobenius内積は次のように定義される。

$$
\langle A, B \rangle \coloneqq\text{tr}(A^\dagger B) = \sum_{i=1}^{m} \sum_{j=1}^{n} A_{ij}^* B_{ij}.
$$

これにより、Frobeniusノルムは次のように定義される。

$$
\|A\| \coloneqq \sqrt{\langle A, A \rangle}.
$$

## Fréchet微分

先ほど定義したFrobeniusノルムを用いてFréchet微分を以下のように定義する。

$$
\mathrm{d}f\coloneqq f(X+\mathrm{d}X)+o(\|\mathrm{d}X\|)
$$
