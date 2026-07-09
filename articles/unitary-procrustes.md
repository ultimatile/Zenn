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

を考える．ここで行列$A$のFrobeniusノルムは$\|A\|_\mathrm{F}=\sqrt{\sum_{ij}|A_{ij}|^2}=\sqrt{\mathrm{tr}(A^{\dagger}A)}$で定義される．$(\cdot)^\dagger$を随伴，$(\cdot)^*$を複素共役とする．最小化する式を展開すると，

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

を求める問題と等価である．ここで，$B$の特異値分解を$B = U\Sigma V^{\dagger}$として代入すると，トレースの巡回性より

$$
\mathrm{Re}\,\mathrm{tr}(A^{\dagger}U\Sigma V^{\dagger})=\mathrm{Re}\,\mathrm{tr}(V^{\dagger}A^{\dagger}U\Sigma)．
$$

$W = V^{\dagger}A^{\dagger}U$とおくと，$A$がユニタリなら$W$もユニタリである．$\Sigma$は非負対角行列なので，成分ごとの平方根で$\sqrt{\Sigma}=\mathrm{diag}(\sqrt{\sigma_1},\dots,\sqrt{\sigma_n})$が取れる．$\Sigma=\sqrt{\Sigma}\sqrt{\Sigma}$と分けて，Frobenius内積$\langle X, Y\rangle_\mathrm{F}=\mathrm{tr}(X^{\dagger}Y)$に対するCauchy–Schwarz不等式$|\langle X, Y\rangle_\mathrm{F}|\leq\|X\|_\mathrm{F}\|Y\|_\mathrm{F}$を適用すると^[$\sqrt{\Sigma}$で等分する理由：素朴に$\mathrm{tr}(W\Sigma)=\langle W^{\dagger},\Sigma\rangle_\mathrm{F}$と見て$W^{\dagger}$と$\Sigma$に分けると，$\|W^{\dagger}\|_\mathrm{F}=\sqrt{\mathrm{tr}(WW^{\dagger})}=\sqrt{n}$なので上界は$\sqrt{n}\,\|\Sigma\|_\mathrm{F}$となる．ところがベクトル$(\sigma_1,\dots,\sigma_n)$と$(1,\dots,1)$に対するCauchy–Schwarz不等式から$\mathrm{tr}\Sigma=\sum_i\sigma_i\cdot 1\leq\sqrt{\sum_i\sigma_i^2}\sqrt{\sum_i 1^2}=\sqrt{n}\,\|\Sigma\|_\mathrm{F}$（等号は特異値がすべて等しいときに限る）なので，この上界は目標の$\mathrm{tr}\Sigma$より緩く届かない．$\Sigma$を$\sqrt{\Sigma}$で両因子に等分すると，$W$のユニタリ性が効いて両因子とも$\sqrt{\mathrm{tr}\Sigma}$となり，上界がちょうど$\mathrm{tr}\Sigma$に締まる．]^[Cauchy-Schwarz不等式を用いた証明は[S.-H. Lin, M. P. Zaletel, and F. Pollmann, Phys. Rev. B **106**, 245102, (2022)](https://doi.org/10.1103/PhysRevB.106.245102)のAppendix A.1を参考にした．]

$$
\mathrm{Re}\,\mathrm{tr}(W\Sigma)\leq|\mathrm{tr}(W\sqrt{\Sigma}\sqrt{\Sigma})|=|\langle\sqrt{\Sigma}W^{\dagger},\sqrt{\Sigma}\rangle_\mathrm{F}|\leq\|\sqrt{\Sigma}W^{\dagger}\|_\mathrm{F}\,\|\sqrt{\Sigma}\|_\mathrm{F}=\mathrm{tr}\Sigma
$$

が得られる．最後の等号は，$W$のユニタリ性とトレースの巡回性から示せる$\|\sqrt{\Sigma}W^{\dagger}\|_\mathrm{F}^2=\mathrm{tr}(W\Sigma W^{\dagger})=\mathrm{tr}\Sigma$と，$\|\sqrt{\Sigma}\|_\mathrm{F}^2=\mathrm{tr}\Sigma$による．最大値は等号が成立するときに得られるので，$A_\mathrm{opt}$は

$$
\mathrm{Re}\,\mathrm{tr}(A_\mathrm{opt}^\dagger B)=\mathrm{Re}\,\mathrm{tr}(V^\dagger A_\mathrm{opt}^\dagger U\Sigma)=\sum_i\sigma_i=\mathrm{tr}\Sigma
$$

の解である．したがって，$A_\mathrm{opt}=UV^\dagger$のとき，$\mathrm{Re}\,\mathrm{tr}(V^\dagger A_\mathrm{opt}^\dagger U\Sigma)=\mathrm{Re}\,\mathrm{tr}\Sigma=\mathrm{tr}\Sigma$となり最大値を取る．

::: details 以前の証明

$\Sigma$は対角行列なので，

$$
\mathrm{Re}\,\mathrm{tr}(W\Sigma)=\mathrm{Re}\sum_i W_{ii}\sigma_i\leq\sum_i|W_{ii}|\sigma_i．
$$

$W$がユニタリのとき，各列は正規直交基底をなすので，各列$j$に対して$\sum_i |W_{ij}|^2 = 1$である．特に$|W_{ii}| \leq 1$が成り立ち^[列$i$について$\sum_k|W_{ki}|^2=1$である．ここで仮に$|W_{ii}|>1$とすると$|W_{ii}|^2>1$だから，$\sum_k|W_{ki}|^2=|W_{ii}|^2+\sum_{k\neq i}|W_{ki}|^2>1$となって矛盾する．したがって$|W_{ii}|\le 1$である．]，

$$
\sum_i|W_{ii}|\sigma_i\leq\sum_i\sigma_i
$$

となり，$\mathrm{Re}\,\mathrm{tr}(W\Sigma)\leq\mathrm{tr}\Sigma$が得られる．

:::

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
余談ですが，テンソルネットワークでは[Evenbly-Vidalの論文](https://link.aps.org/doi/10.1103/PhysRevB.79.144108)で使用されたのが有名になったようでEvenbly-Vidalアルゴリズムと呼ばれることがあるようですが，この問題は古くから[直交（ユニタリ）Procrustes問題](https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem)(の特殊形)として知られており^[リンク先のWikipediaによると1964年に初めて解かれたそうです]，ユニタリProcrustes解と呼ぶ方が自然だと思います．
:::

## 付録: Evenbly-Vidalアルゴリズム

[Evenbly-Vidalアルゴリズム](https://link.aps.org/doi/10.1103/PhysRevB.79.144108)は、ユニタリProcrustes解が厳密解ではない場合、つまりユニタリProcrustes問題ではない目的函数に対する最適化問題に対して、ユニタリProcrustes解を反復的に代入して計算する近似解法である．

以下の目的函数を最大化する問題を考える．

$$
f(A) = \operatorname{tr}(A E(A)).
$$

ユニタリProcrustes問題との相違点は，$A^\dagger\to A$と$B\to E(A)$の2点である．前者はユニタリProcrustes解$UV^\dagger$と随伴分が異なるので，随伴を吸収して解形式が$VU^\dagger$に変わる．後者は$B$，つまり$A$依存性がなかったターゲット行列の代わりに$A$依存性がある$E(A)$を考えている．したがって，$VU^\dagger$はもはや目的函数の上界を達成する最適解ではない．しかし，反復解としてこれを採用するのがEvenbly-Vidalアルゴリズムである．$k$回目の反復解$A_k$が与えられたとして，次の反復解$A_{k+1}$を，$E(A_k)=U_k\Sigma_kV^\dagger_k$と特異値分解し，$A_{k+1}=V_kU_k^\dagger$とする．これを$f(A_k)$が収束するまで繰り返す．
