---
title: "ある行列に最も近いユニタリ行列を求める問題（ユニタリProcrustes問題の特殊形）"
emoji: "🧮"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["線形代数"]
published: true
---

$A, B \in \mathbb{C}^{n\times n}$について，与えられた$B$に対してFrobeniusノルムで最も近いユニタリ行列$A_\mathrm{opt}$を求める問題

$$
A_\mathrm{opt} = \argmin_{\{A \in \mathbb{C}^{n\times n}\mid A^\dagger A = AA^\dagger = I_n\}} \|A - B\|_\mathrm{F}^2
$$

を考える．
ここで行列$A$のFrobeniusノルムは$\|A\|_\mathrm{F}=\sqrt{\sum_{ij}|A_{ij}|^2}=\sqrt{\mathrm{tr}(A^{\dagger}A)}$で定義される．
$(\cdot)^\dagger$を随伴，$(\cdot)^*$を複素共役とする．
最小化する式を展開すると，

$$
\|A - B\|_\mathrm{F}^2 = \|A\|_\mathrm{F}^2 + \|B\|_\mathrm{F}^2 - 2\mathrm{Re}\,\mathrm{tr}(A^{\dagger}B)\tag{1}
$$

となる．

::: details (1)の確認
$$
\|A - B\|_\mathrm{F}^2 = \mathrm{tr}((A-B)^{\dagger}(A-B)) = \mathrm{tr}(A^{\dagger}A) + \mathrm{tr}(B^{\dagger}B) - \mathrm{tr}(A^{\dagger}B) - \mathrm{tr}(B^{\dagger}A)
$$
$$
(\mathrm{tr}(A^\dagger B))^*=\left(\sum_{ij}(A^\dagger)_{ij}B_{ji}\right)^*=\left(\sum_{ij}A^*_{ji}B_{ji}\right)^*=\sum_{ij}B^*_{ji}A_{ji}=\sum_{ij}(B^\dagger)_{ij}A_{ji}=\mathrm{tr}(B^\dagger A)
$$
よって$\mathrm{tr}(A^{\dagger}B) + \mathrm{tr}(B^{\dagger}A) = 2\mathrm{Re}\,\mathrm{tr}(A^{\dagger}B)$である．
:::

$\|A\|_\mathrm{F}^2$と$\|B\|_\mathrm{F}^2$は定数なので，元の問題は

$$
\max_{\{A \in \mathbb{C}^{n\times n}\mid A^\dagger A = AA^\dagger = I_n\}}\mathrm{Re}\,\mathrm{tr}(A^{\dagger}B)
$$

を求める問題と等価である．
ここで，$B$の特異値分解を$B = U\Sigma V^{\dagger}$として代入すると，トレースの巡回性より

$$
\mathrm{Re}\,\mathrm{tr}(A^{\dagger}U\Sigma V^{\dagger})=\mathrm{Re}\,\mathrm{tr}(V^{\dagger}A^{\dagger}U\Sigma)．
$$

$W = V^{\dagger}A^{\dagger}U$とおくと，$A$がユニタリなら$W$もユニタリである．$\Sigma$は対角行列なので，

$$
\mathrm{Re}\,\mathrm{tr}(W\Sigma)=\mathrm{Re}\sum_i W_{ii}\sigma_i\leq\sum_i|W_{ii}|\sigma_i．
$$

$W$がユニタリのとき，各列は正規直交基底をなすので，各列$j$に対して$\sum_i |W_{ij}|^2 = 1$である．特に$|W_{ii}| \leq 1$が成り立ち^[列$i$について$\sum_k|W_{ki}|^2=1$である．ここで仮に$|W_{ii}|>1$とすると$|W_{ii}|^2>1$だから，$\sum_k|W_{ki}|^2=|W_{ii}|^2+\sum_{k\neq i}|W_{ki}|^2>1$となって矛盾する．したがって$|W_{ii}|\le 1$である．]，

$$
\sum_i|W_{ii}|\sigma_i\leq\sum_i\sigma_i
$$

となる．最大値は等号が成立するときに得られるので，$A_\mathrm{opt}$は

$$
\mathrm{Re}\,\mathrm{tr}(A_\mathrm{opt}^\dagger B)=\mathrm{Re}\,\mathrm{tr}(V^\dagger A_\mathrm{opt}^\dagger U\Sigma)=\sum_i\sigma_i=\mathrm{tr}\Sigma
$$

の解である．
したがって，$A_\mathrm{opt}=UV^\dagger$のとき，$\mathrm{Re}\,\mathrm{tr}(V^\dagger A_\mathrm{opt}^\dagger U\Sigma)=\mathrm{Re}\,\mathrm{tr}\Sigma=\mathrm{tr}\Sigma$となり最大値を取る．

::: details von Neumannのトレース不等式を用いた別解
$\sigma_i(A)$と$\sigma_i(B)$（本文では単に$\sigma_i$）をそれぞれ$A$と$B$の特異値として，
von Neumannのトレース不等式

$$
\mathrm{Re}\,\mathrm{tr}(A^{\dagger}B) \leq \sum_i \sigma_i(A)\sigma_i(B)
$$

を認める^[証明は[R. A. Horn and C. R. Johnson, Matrix Analysis 2nd Edition](https://www.amazon.co.jp/dp/0521839408), Theorem 7.4.1.1 (p. 258)などを参照]と$A$がユニタリであることから，その特異値$\sigma(A)_i$は全て1であることがわかるので，$\mathrm{Re}\,\mathrm{tr}(A^{\dagger}B)\leq\sum_i\sigma_i$が得られる．
:::

## まとめ

与えられた行列$B$に対してFrobeniusノルムで最も近いユニタリ行列$A_\mathrm{opt}$は、$B$を$B=U\Sigma V^\dagger$と特異値分解して，$A_\mathrm{opt}=UV^\dagger$とすることで得られる．

::: message
余談ですが，テンソルネットワークでは[Evenbly-Vidalの論文](https://link.aps.org/doi/10.1103/PhysRevB.79.144108)で使用されたのが有名になったようでEvenbly-Vidalアルゴリズムと呼ばれることがあるようですが，この問題は古くから[直交（ユニタリ）Procrustes問題](https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem)(の特殊形)として知られており^[リンク先のWikipediaによると1964年に最初に解かれたそうです]，ユニタリProcrustes解と呼ぶ方が自然だと思います．
:::
