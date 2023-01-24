---
title: "HΦによる量子スピン系の動的相関函数の計算"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [hphi]
published: false
---

# はじめに

$$
\begin{aligned}
S^{zz}(\bm{q},\omega)&=\sum_{n=1}^{N_\mathrm{dim}}\left|\left\langle\psi_{n}|\hat{S}^z(\bm{q})| \psi_{0}\right\rangle\right|^{2} \delta\left(\omega+E_1-E_n\right)\\
&=-\frac{1}{\pi}\operatorname{Im}G(\bm{q},\omega)\\
G(\bm{q},\omega)&=\lim _{\eta \rightarrow +0}\left\langle\psi_1\left|\hat{S}^z(-\bm{q}) \frac{1}{\omega+E_1-\hat{\mathcal{H}}+\mathrm{i}\eta}\hat{S}^z(\bm{q})\right| \psi_1\right\rangle
\end{aligned}
$$

$$
S^{z z}(q, \omega)=\frac{1}{N} \sum_{j, j^{\prime}=1}^{N} e^{-i q\left(j-j^{\prime}\right)} \int_{-\infty}^{+\infty} d t e^{i \omega t}\left\langle S_{j}^{z}(t) S_{j^{\prime}}^{z}(0)\right\rangle
$$


$E_1$は基底状態のenergy.

基底状態の固有状態が必要なのでまず通常の基底状態対角化計算を行います.

```:gs.in
method = "cg"
model = "spin"
lattice = "chain lattice"
L = 16
J = 1
2S = 1
2Sz = 0

EigenVecIO = "out"
```


```
method = "cg"
model = "spin"
lattice = "chain lattice"
L = 16
J = 1
2S = 1
2Sz = 0

LanczosEPS = 8
CalcSpec = "Normal"
SpectrumType = "SzSz"
OmegaMin = 0.0
OmegaMax = 3.15
OmegaIM = 0.0
spectrumQL = 0.5
```

`spectrumQL = 0.5` は$q=\pi$を意味します.
`OmegaIM`はdamping factorです.
小さいほど正確な値になります.
2次元系では`spectrumQW`も指定する.
すなわち$\bm{q}=(\frac{2\pi}{L}$`spectrumQL`$,\frac{2\pi}{W}$`spectrumQW`$)$

| key | 型 | default | 説明 |
|:---:|:---:|:---:|:---|
| `CalcSpec` | 文字列 | `"None"` | `"None"`, `"Normal"`, `"NoIteration"`, `"Restart_out"`, `"Restart_in"`, `"Restart"`|
| `SpectrumType` | 文字列 | `"SzSz"` | `"SzSz"`, `"S+S-"`, `"Density"`, `"up"`, `"down"` |
| `SpectrumQW` | 実数 | 0.0 | `W`方向の分率座標 |
| `SpectrumQL` |  実数 | 0.0 | `L`方向の分率座標 |
| `OemgaOrg` |  実数 | 0.0 | 実部の原点 |
| `OemgaMin` |  実数 | $-$`LargeValue`$\times N$ | 実部の最小値 |
| `OmegaMax` |  実数 | `LargeValue`$\times N$ | 実部の最大値 |
| `OmegaIm` |  実数 | 0.01 $\times$`LargeValue` | 虚部 |
| `NOmega` | 正整数 | 200 | 計算する振動数の数 |

- 出力形式は常に`OemgaMin`から`OemgaMax`までの値が出力される.つまり`OemgaOrg`で原点をずらしても出力される周波数の値は変化しない.
- `LargeValue`のdefault値は?



```bash:
#!/bin/bash
L=16
omegamax=3.15
omegaim=0.1

output="spectrum-L${L}.dat"

MPIEXEC=""
HPHI=HPhi

cat << PARAM > gs.in
model = "spin"
method = "cg"
lattice = "chain lattice"
2S = 1
2Sz = 0
J = 1
L = $L
PARAM

cp gs.in exc.in.org
echo 'EigenvecIO = "out"' >> gs.in

$MPIEXEC $HPHI -s gs.in

ge=$(awk '$1~/Energy/ {print $2}' output/zvo_energy.dat)
cat << PARAM >> exc.in.org
LanczosEPS = 8
CalcSpec = "Normal"
SpectrumType = "SzSz"
OmegaMin = 0.0
OmegaOrg = $ge
OmegaMax = $omegamax
OmegaIM = $omegaim
PARAM

rm -f $output

L2=$(echo "$L / 2" | bc)
for iq in `seq 0 $L2`; do
  cp exc.in.org exc.in
  q=$(echo "$iq/$L" | bc -l)
  echo "spectrumQL = $q" >> exc.in
  $MPIEXEC $HPHI -s exc.in
  awk --assign=q=$q '{print q, $1, $3, $4}' output/zvo_DynamicalGreen.dat >> $output
done

```

# 参考文献
https://ma.issp.u-tokyo.ac.jp/app-post/1605