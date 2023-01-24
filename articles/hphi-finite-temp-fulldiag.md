---
title: "HΦによる量子スピン系の有限温度計算(全対角化)" # 記事のタイトル
emoji: "🦀" # アイキャッチとして使われる絵文字（1文字だけ）
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["hphi"] # トピックス（タグ）["markdown", "rust", "aws"]のように指定する
published: false # 公開設定（falseにすると下書き）
---

# はじめに
Boltzmann定数$k_\mathrm{B}$は$1$とします.
数値対角化を用いた量子spin系の有限温度計算のtutorialです.
$S=1/2$ Heisenberg鎖の計算を行います.
なお全対角化とは, 最小固有値から最大固有値まで全て求める対角化計算を指します.
​
対角化計算には$\mathcal{H}\Phi$を用います.
​
逆温度$\beta$でのcanonical ensembleにおける熱期待値は以下のように書けます.

$$
\braket{\hat{\mathcal{O}}}_\beta=\frac{\mathrm{Tr}\left(\hat{\mathcal{O}}\mathrm{e}^{-\beta\hat{\mathcal{H}}}\right)}{\mathrm{Tr}\mathrm{e}^{-\beta\hat{\mathcal{H}}}}
=\frac{\sum_{i=1}^{N_\mathrm{dim}}O_i\mathrm{e}^{-\beta E_i}}{\sum_{i=1}^{N_\mathrm{dim}}\mathrm{e}^{-\beta E_i}}
$$

ここで$N_\mathrm{dim}$は対象とするHamiltonian行列の次元です.
$O_i$, $E_i$はそれぞれ演算子(行列)$\hat{O}$, $\hat{\mathcal{H}}$の$i$番目の固有状態$\ket{\psi_i}$での量子力学的期待値(固有値)です.

この式から熱期待値を求めるには各固有状態$i$に対してenergy固有値$E_i$と対象の物理量の固有値$O_i$を求めれば良いことがわかります.

そのために$\mathcal{H}\Phi$で全対角化を行います.
以下のinput fileを用意します.

```:stan.in
model   = "SpinGC"
method  = "FullDiag"
lattice = "chain"
J = 1
L = 3
```

以下のように$\mathcal{H}\Phi$を実行します.
```bash:terminal
HPhi -s stan.in
```

計算が終了すれば実行directoryに`output` directoryが作成され, 以下のような出力fileがあるはずです.

```:output/zvo_phys.dat
  <H>         <N>        <Sz>       <S2>       <D> 
  -0.750000   3.000000  -0.500000   0.750000   0.000000
  -0.750000   3.000000   0.500000   0.750000   0.000000
  -0.750000   3.000000   0.500000   0.750000   0.000000
  -0.750000   3.000000  -0.500000   0.750000   0.000000
   0.750000   3.000000  -0.500000   3.750000   0.000000
   0.750000   3.000000   0.500000   3.750000   0.000000
   0.750000   3.000000  -1.500000   3.750000   0.000000
   0.750000   3.000000   1.500000   3.750000   0.000000
```

固有状態毎に物理量が出力されます.
1列目から順にenergy, 粒子数, 全$\hat{S}_z$, 全$\hat{S}^2$, 全doublonです.

まずenergyの熱期待値を求めましょう.

$$
E_\beta=\braket{\hat{\mathcal{H}}}_\beta=\frac{\sum_{i=1}^{N_\mathrm{dim}}E_i\mathrm{e}^{-\beta E_i}}{\sum_{i=1}^{N_\mathrm{dim}}\mathrm{e}^{-\beta E_i}}
$$

`zvo_phys.dat`の1列目の値を指数函数に入れて和を取るだけですが, 指数函数の扱いには注意が必要です.

$$
\braket{\hat{\mathcal{H}}}_\beta=\frac{\mathrm{e}^{\beta E_\mathrm{min}}\sum_{i=1}^{N_\mathrm{dim}}E_i\mathrm{e}^{-\beta E_i}}{\mathrm{e}^{\beta E_\mathrm{min}}\sum_{i=1}^{N_\mathrm{dim}}\mathrm{e}^{-\beta E_i}}
=\frac{\sum_{i=1}^{N_\mathrm{dim}}E_i\mathrm{e}^{-\beta (E_i-E_\mathrm{min})}}{\sum_{i=1}^{N_\mathrm{dim}}\mathrm{e}^{-\beta (E_i-E_\mathrm{min})}}
$$

```julia:FT.jl
using DelimitedFiles
#skipstartで最初に読み飛ばす行数を指定して読み込み
data = readdlm("zvo_phys.dat", Float64, skipstart=1)
T = parse(Float64, ARGS[1])#温度を実行時引数として指定

β = 1 / T
E = data[:, 1]
Emin = E[1]

#energyと比熱の計算
Z = sum(@. exp(-β * (E - Emin)))
Eave = sum(@. E * exp(-β * (E - Emin))) / Z
E2ave = sum(@. E^2 * exp(-β * (E - Emin))) / Z
C = β^2 * (E2ave - Eave^2)

#比較用の解析解
Eexa = -0.75 * (exp(β) - 1) / (exp(β) + 3)
Cexa = 3β^2 * exp(β) / (exp(β) + 3)^2

println("$T $Eave $Eexa $C $Cexa")
```

# 参考文献

 2 siteの$S=1/2$ Heisenberg模型

$$
\hat{\bm{S}}_1\cdot\hat{\bm{S}}_2
$$

の対角化は$S=1/2$ $2$つの合成と等価ですので固有値は$-3/4, 1/4(3$重縮退)です.
したがって分配函数は

$$
Z_\beta=\mathrm{e}^\frac{3\beta}{4}+3\mathrm{e}^{-\frac{\beta}{4}}
$$

となりenergy$E_\beta$と(定積)比熱$C_\beta$は

$$
\begin{aligned}
E_\beta&=-\frac{\partial}{\partial \beta}\log Z_\beta=-\frac{3 \left(\mathrm{e}^\beta-1\right)}{4\left(\mathrm{e}^\beta+3\right)}\\
C_\beta&=\beta^2\frac{\partial^2}{\partial \beta^2}\log Z_\beta=\frac{3\beta^2\mathrm{e}^\beta}{\left(\mathrm{e}^\beta+3\right)^2}
\end{aligned}
$$
となります.