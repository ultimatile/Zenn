---
title: "mytitle"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["線形代数"]
published: false
---

$\mathbb{C}$上の同じサイズの行列$A$, $B$について，与えられた$B$に対してFrobeniusノルムで最も近いユニタリ行列$A_\mathrm{opt}$を求める問題を考える．すなわち，

$$
A_\mathrm{opt} = \argmin_{\{A|\,A^\dagger A = AA^\dagger=1\}} \|A - B\|_\mathrm{F}^2
$$

を考える．展開すると，

$$
\|A - B\|_\mathrm{F}^2 = \|A\|_\mathrm{F}^2 + \|B\|_\mathrm{F}^2 - 2\mathrm{Re}\,\mathrm{tr}(A^{\dagger}B)
$$

$\|A\|_\mathrm{F}^2$と$\|B\|_\mathrm{F}^2$は定数なので，元の問題は

$$
\max_{\{A|\,A^\dagger A = AA^\dagger=1\}}\mathrm{Re}\,\mathrm{tr}(A^{\dagger}B)
$$

を求める問題と等価である．
ここで，$B$の特異値分解を$B = U\Sigma V^{\dagger}$として代入すると，

$$
\mathrm{Re}\,\mathrm{tr}(A^{\dagger}U\Sigma V^{\dagger})
$$

トレースの循環性を用いると，

$$
= \mathrm{Re}\,\mathrm{tr}(V^{\dagger}A^{\dagger}U\Sigma)
$$

$W = V^{\dagger}A^{\dagger}U$とおくと，$A$がユニタリなら$W$もユニタリである．$\Sigma$は対角行列なので，

$$
\mathrm{Re}\,\mathrm{tr}(W\Sigma) = \mathrm{Re}\sum_i W_{ii}\sigma_i \leq \sum_i |W_{ii}|\sigma_i
$$

$W$がユニタリのとき，各列は正規直交基底をなすので$\sum_i |W_{ij}|^2 = 1$である．特に$|W_{ii}| \leq 1$が成り立ち，

$$
\sum_i |W_{ii}|\sigma_i \leq \sum_i \sigma_i
$$

等号成立は全ての$i$で$|W_{ii}| = 1$かつ$W_{ii} > 0$のとき，すなわち$W = I$のときである．$W = I$を解くと$A = UV^{\dagger}$が得られる．
