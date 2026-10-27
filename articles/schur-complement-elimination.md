---
title: "Schur補行列で見る自由度の消去：連分数，cross interpolation，Feshbach射影，Mori-Zwanzig形式"
emoji: "🧮"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["数学", "線形代数", "物理", "テンソルネットワーク"]
published: false
register: joutai
---

## はじめに

ブロックに分けた正方行列

$$
M=\begin{pmatrix}A&B\\C&D\end{pmatrix}
$$

で$A$が正則なとき，

$$
M/A\coloneqq D-CA^{-1}B
$$

を$M$の$A$に関する[Schur補行列](https://en.wikipedia.org/wiki/Schur_complement)と呼ぶ．線形代数の講義では，ブロック行列の行列式や逆行列の公式の途中に一度出てきて，それきりになることが多い．

ところが同じ式は，分野ごとに別の名前で何度も現れる．

- 三重対角行列の逆行列の成分を連分数に展開する計算．
- 行列の一部の行と列だけから低ランク近似を作るcross interpolation（CI）と，それを安定に計算するprrLU（partial rank-revealing LU）分解．
- 量子力学で状態空間の一部を消去し，エネルギーに依存する有効Hamiltonianを作るFeshbach射影．
- 統計力学で着目しない自由度を消去し，過去の履歴に依存する運動方程式を導くMori-Zwanzig形式．

どれも連立一次方程式の変数の一部を消去して残りの変数だけの方程式を作る操作で，そのとき残りの変数に掛かる行列がSchur補行列である．本記事はこの4つを順にたどり，次の対比でつなぐ．消去そのものは厳密な操作で，近似が入るのは消去の結果現れたSchur補行列をどう扱うかの段階である．連分数・Feshbach射影・Mori-Zwanzig形式ではSchur補行列を残すことで厳密な縮約が得られ，近似はそれを打ち切ったり単純化したりするときに入る．CIは逆にSchur補行列を丸ごと捨てる近似で，捨てたものがそのまま近似誤差になる．

連分数・Feshbach射影・Mori-Zwanzig形式の節では，最近接ホッピングだけをもつ一様な半無限鎖を共通の例に使う．鎖の端のサイト以外を消去すると1つの函数$\Sigma(z)$が得られ，これは連分数の尾とエネルギー依存の自己エネルギーとして現れ，変数の読み替えと定数倍のもとで記憶核のLaplace変換にもなる．手で追える導出は「導出」と題した折りたたみに入れたので，本文は結果だけを追って読み進められる．

前提は線形代数（逆行列・行列式・LU分解）と，後半の節ではLaplace変換と量子力学の初歩（Hamiltonian，Green函数）である．

## Schur補行列の基本

### 変数の消去としてのSchur補行列

連立一次方程式

$$
\begin{pmatrix}A&B\\C&D\end{pmatrix}\begin{pmatrix}x\\y\end{pmatrix}=\begin{pmatrix}f\\g\end{pmatrix}
$$

を考える（$A$は正則な正方行列）．1本目を$x=A^{-1}(f-By)$と解いて2本目に代入すると，$y$だけの方程式

$$
(D-CA^{-1}B)\,y=g-CA^{-1}f
$$

が残る．左辺の係数がSchur補行列$M/A$である．つまり$M/A$は$x$を消去したあと残った変数$y$に掛かる行列で，消去した$x$の影響は$-CA^{-1}B$という補正として$D$に織り込まれている．

同じ操作を行列の分解として書くと，ブロック版のGauss消去

$$
M=\begin{pmatrix}I&0\\CA^{-1}&I\end{pmatrix}\begin{pmatrix}A&0\\0&M/A\end{pmatrix}\begin{pmatrix}I&A^{-1}B\\0&I\end{pmatrix}
$$

になる．左右の因子は対角ブロックが単位行列のブロック三角行列なので，行列式は1で，逆行列もすぐ書ける．

$D$が正則なら，逆に$y$を消去して$x$だけの方程式を作ることもでき，そのとき$x$に掛かる行列は

$$
M/D\coloneqq A-BD^{-1}C
$$

である．記号$M/X$は，どちらの場合もブロック$X$に対応する変数を消去したあと残りの変数に掛かる行列を表す．CIの節では$M/A$を，連分数・Feshbach射影・Mori-Zwanzig形式の節では$M/D$を使う．

### 4つの恒等式

ブロックGauss消去の分解から，以降の節で使う4つの恒等式が出る．

行列式は，左右の因子の行列式が1なので

$$
\det M=\det A\,\det(M/A)
$$

である．同様に$D$が正則なら$\det M=\det D\,\det(M/D)$．$2\times2$の数値の行列$M=\begin{pmatrix}a&b\\c&d\end{pmatrix}$なら$M/a=d-bc/a=(ad-bc)/a$で，見慣れた行列式の公式に戻る．

逆行列のブロックは，連立方程式の消去から直接読める．$M$が正則なとき，$f=0$とおくと$y=(M/A)^{-1}g$なので，$M^{-1}$の右下ブロックは

$$
(M^{-1})_{22}=(M/A)^{-1}
$$

である．同様に$D$が正則なら$(M^{-1})_{11}=(M/D)^{-1}$．逆行列の一部のブロックだけが欲しいときは，Schur補行列を作ってその逆行列を取れば足りる．後半の節でGreen函数の成分を求める計算はこの式を使う．

ランクについては，左右の因子が正則なので$M$のランクは中央のブロック対角行列のランクに等しく，

$$
\operatorname{rank}M=\operatorname{rank}A+\operatorname{rank}(M/A)
$$

が成り立つ．$M$が長方行列でも，$A$が正則な正方ブロックなら同じ分解と同じ式が使える．

最後は商の公式である．$A$自体をさらに

$$
A=\begin{pmatrix}E&F\\G&H\end{pmatrix}
$$

と分け，$E$も正則だとする．$x=(x_1,x_2)$のうち$x_1$だけを消去した係数行列$M/E$の左上ブロックは$A/E$になっていて，

$$
M/A=(M/E)/(A/E)
$$

が成り立つ[^quotient]．変数の言葉で言えば，$x=(x_1,x_2)$をまとめて消去しても，$x_1$を消去してから$x_2$を消去しても，$y$に残る方程式は同じだということである．1変数ずつ消去を繰り返す算法（連分数の再帰やprrLU分解）は，これによって一括の消去と結びつく．

:::details 導出：商の公式

$f=0$のとき，$y$を与えると1本目の式$Ax+By=0$から$x=-A^{-1}By$が一意に決まり，2本目から$g=(M/A)\,y$となる．つまり$M/A$は，1本目の式を満たすように$x$を決めたときの写像$y\mapsto g$の行列である．

一方，$x_1$を先に消去すると，$(x_2,y)$についての連立方程式の係数行列は$M/E$になり，その左上ブロックは$H-GE^{-1}F=A/E$である．$\det A=\det E\,\det(A/E)$より$A/E$は正則なので，続けて$x_2$を消去でき，$y$に掛かる行列は$(M/E)/(A/E)$になる．どちらの手順でも$x=(x_1,x_2)$は1本目の式$Ax+By=0$の唯一の解として同じものに決まるので，写像$y\mapsto g$も同じであり，$M/A=(M/E)/(A/E)$を得る．

:::

## 連分数：消去の再帰

### 三重対角行列の逆行列の成分

$n\times n$の三重対角行列

$$
M=\begin{pmatrix}a_1&b_1&&\\c_1&a_2&\ddots&\\&\ddots&\ddots&b_{n-1}\\&&c_{n-1}&a_n\end{pmatrix}
$$

の逆行列の左上成分$(M^{-1})_{11}$を考える（途中に現れる行列はすべて正則とする）．1番目の変数を$x$，2番目以降を$y$として分けると，$A=a_1$，$B=(b_1,0,\dots,0)$，$C=(c_1,0,\dots,0)^\top$で，$D=M_{2:n}$は2番目以降の行と列からなる三重対角行列である．$(M^{-1})_{11}=(M/D)^{-1}$で，$B$と$C$は$D$の1番目の変数にしか触れないので

$$
(M^{-1})_{11}=\frac{1}{a_1-b_1c_1\bigl((M_{2:n})^{-1}\bigr)_{11}}
$$

となる．右辺の$\bigl((M_{2:n})^{-1}\bigr)_{11}$は，1サイト短い同じ形の問題である．これを繰り返すと

$$
(M^{-1})_{11}=\cfrac{1}{a_1-\cfrac{b_1c_1}{a_2-\cfrac{b_2c_2}{\ddots-\cfrac{b_{n-1}c_{n-1}}{a_n}}}}
$$

という連分数が得られる．各段は，1サイトを残してそれより先をすべて消去するSchur補行列である．末尾から1サイトずつ消去していくと見ても同じ式になり，その1段ずつの消去と一括の消去を結ぶのが商の公式である．

量子力学で使うのは$M=zI-H$の場合である．$H$がHermite行列（Hamiltonian）で$z$が実軸から外れた複素数のとき，$G(z)\coloneqq(zI-H)^{-1}$をGreen函数と呼ぶ．$H$が三重対角なら$G_{11}(z)$は上の連分数で書け，$a_k=z-H_{kk}$，$b_kc_k=|H_{k,k+1}|^2$となる．三重対角でない一般のHermite行列でも，[Lanczos法](https://en.wikipedia.org/wiki/Lanczos_algorithm)で着目するベクトルから始まる基底に移せば三重対角になるので，そのベクトルについてのGreen函数の対角成分は同じ連分数で表せる．これを局所状態密度の計算に使うのが再帰法と呼ばれる手法である[^haydock]．

### 半無限鎖と自己エネルギー

サイトエネルギー$\varepsilon$，隣接サイト間のホッピング$w>0$をもつ一様な半無限鎖

$$
H=\begin{pmatrix}\varepsilon&w&&\\w&\varepsilon&w&\\&w&\varepsilon&\ddots\\&&\ddots&\ddots\end{pmatrix}
$$

を考え，端のサイトのGreen函数を$g(z)\coloneqq G_{11}(z)$とおく．連分数のすべての段が同じ形をしているうえ，端のサイトを取り除いても同じ半無限鎖が残るので，連分数の尾は$g(z)$そのものになり

$$
g(z)=\frac{1}{z-\varepsilon-w^2g(z)}
$$

が成り立つ．$\Sigma(z)\coloneqq w^2g(z)$とおけば$\Sigma=w^2/(z-\varepsilon-\Sigma)$で，これは$\Sigma$の2次方程式なので閉じた形で解ける．

$$
\Sigma(z)=\frac{(z-\varepsilon)-\sqrt{(z-\varepsilon)^2-4w^2}}{2}
$$

平方根の枝は，$|z|\to\infty$で$\Sigma(z)\approx w^2/(z-\varepsilon)\to0$となるほうを取る．

この$\Sigma(z)$は，鎖の端のサイトから見た残りの鎖の効果をまとめた函数で，後の2節でも同じものが現れる．実軸上の帯$|\omega-\varepsilon|<2w$に$z=\omega+\mathrm{i}0$で近づくと$\Sigma$は虚部をもち，端のサイトの局所状態密度は

$$
\rho(\omega)=-\frac{1}{\pi}\operatorname{Im}g(\omega+\mathrm{i}0)=\frac{\sqrt{4w^2-(\omega-\varepsilon)^2}}{2\pi w^2}
$$

という半円型になる．

:::details 導出：$\Sigma(z)$の閉形式と状態密度

$\Sigma=w^2/(z-\varepsilon-\Sigma)$の分母を払うと$\Sigma^2-(z-\varepsilon)\Sigma+w^2=0$で，解の公式から本文の式を得る．もう一方の根は$|z|\to\infty$で$\Sigma\approx z-\varepsilon$と発散し，Green函数の振る舞い$G(z)\approx I/z$（したがって$g=\Sigma/w^2\approx1/z$）に合わない．

帯の内側$z=\omega+\mathrm{i}\eta$（$\eta\to+0$）では$(z-\varepsilon)^2-4w^2\to-\bigl(4w^2-(\omega-\varepsilon)^2\bigr)<0$である．上の枝を上半平面から連続に延ばすと$\sqrt{(z-\varepsilon)^2-4w^2}\to\mathrm{i}\sqrt{4w^2-(\omega-\varepsilon)^2}$となる（たとえば$\omega=\varepsilon$で$\eta$を大きくすると$\Sigma\approx w^2/(\mathrm{i}\eta)$となり，虚部が負であることと整合する）．よって$\operatorname{Im}\Sigma(\omega+\mathrm{i}0)=-\sqrt{4w^2-(\omega-\varepsilon)^2}/2$で，$g=\Sigma/w^2$から本文の$\rho(\omega)$が出る．

:::

連分数を$n$段で打ち切ることは，鎖を$n$サイトで切ることに当たる．有限の鎖のGreen函数は$n$個の極しかもたず，連続な状態密度は$n$本の線に置き換わる．Schur補行列による消去は厳密で，近似はこの打ち切りで入る．

## 低ランク近似：cross interpolationとprrLU分解

### CIの誤差はSchur補行列

$m\times n$行列$M$の行を$r$本，列を$r$本選び，その交点の$r\times r$部分行列$P$（ピボット行列）が正則だとする．選んだ列を並べた$m\times r$行列を$M_{:,J}$，選んだ行を並べた$r\times n$行列を$M_{I,:}$と書くと，cross interpolation（CI）は

$$
M\approx\widetilde M\coloneqq M_{:,J}\,P^{-1}M_{I,:}
$$

という階数$r$の近似である．行列全体ではなく$r$本の行と列だけから作れるので，成分を1つ求めるのに手間がかかる行列や，全成分を保持できない巨大な行列に向く．多変数函数を表すテンソルに対してこれを繰り返すのがtensor cross interpolation（TCI）である[^tci]．

選んだ行と列を並べ替えで左上へ集めると$P=A$で，

$$
\widetilde M=\begin{pmatrix}A\\C\end{pmatrix}A^{-1}\begin{pmatrix}A&B\end{pmatrix}=\begin{pmatrix}A&B\\C&CA^{-1}B\end{pmatrix},\qquad M-\widetilde M=\begin{pmatrix}0&0\\0&M/A\end{pmatrix}
$$

となる．CIは選んだ行と列を厳密に再現し，誤差は残りのブロックに現れるSchur補行列$M/A$そのものである．言い換えるとCIは，消去の結果現れるSchur補行列を0とみなす近似である．

ランクの恒等式$\operatorname{rank}M=r+\operatorname{rank}(M/A)$から，CIが厳密になる（$M/A=0$となる）のは$\operatorname{rank}M=r$のときに限られる．逆に$M$の階数がちょうど$r$なら，ピボット行列が正則になる限り，どの$r$本の行と列を選んでもCIは$M$を厳密に再現する．

### ピボットの選び方とprrLU分解

階数が$r$より大きい行列では，誤差$M/A$の大きさはピボットの選び方で変わる．$M/A$は$A^{-1}$を通じてピボット行列に依存するので，$|\det A|$が最大になるようにピボットを選ぶ指針が知られており，最大体積原理と呼ばれる[^tci]．ただし最大体積のピボットを厳密に探すには，一般に指数的な手間がかかる．

ピボットを1組ずつ貪欲に増やす場合には，Schur補行列が直接の指標になる．いまのピボット行列$A$に行$i$と列$j$を1本ずつ加えた$(r+1)\times(r+1)$行列の行列式は

$$
\det\begin{pmatrix}A&B_{:,j}\\C_{i,:}&D_{ij}\end{pmatrix}=\det A\cdot(M/A)_{ij}
$$

である．行列式の恒等式をこの$(r+1)\times(r+1)$行列に当てはめると，その$1\times1$のSchur補行列は$D_{ij}-C_{i,:}A^{-1}B_{:,j}=(M/A)_{ij}$になるからである．したがって，いまのピボット行列$A$を固定したまま，Schur補行列の成分のうち絶対値が最大のものを次のピボットとして選べば，追加後の$(r+1)\times(r+1)$ピボット行列の体積が最大になる．

この選び方で$1\times1$のピボットごとにGauss消去を進め，$r$段で止めたものが，残りの全成分を調べる全探索型のprrLU分解である．各段では$1\times1$のピボットに関するSchur補行列を作り，商の公式から$r$段のあとに残る行列は，選んだ$r\times r$のピボット行列に関するSchur補行列$M/A$に等しい．消去を$r$段で止めた分解は，残ったSchur補行列を含めれば厳密である．そこから残ったSchur補行列を0として再構成した階数$r$の近似が，同じピボットのCIに等しい．prrLU分解は，ピボット行列を作って逆行列を取る形でCIを評価するより数値的に安定である[^tci]．残ったSchur補行列の最大成分が許容誤差を下回った時点で止めれば，そこまでの段数が，成分ごとの誤差を基準にした数値的な階数の見積もりになる．厳密な算術なら，Schur補行列は$\operatorname{rank}M$段でちょうど0になる．なお，消去で得られる対角成分（ピボット）は一般には特異値と一致しない．

:::details 導出：$3\times3$のランク2行列

$$
M=\begin{pmatrix}2&1&3\\1&1&2\\3&2&5\end{pmatrix}
$$

は3行目が1行目と2行目の和なので階数2である．手計算の都合でピボットを左上から順に取る（絶対値最大の成分は$5$だが，階数2の行列では，正則なピボット行列を$2\times2$で取れば選び方によらずSchur補行列は0になる）．1段目のピボット$M_{11}=2$で消去すると

$$
M/M_{11}=\begin{pmatrix}1&2\\2&5\end{pmatrix}-\frac{1}{2}\begin{pmatrix}1\\3\end{pmatrix}\begin{pmatrix}1&3\end{pmatrix}=\begin{pmatrix}1/2&1/2\\1/2&1/2\end{pmatrix}
$$

となる．2段目のピボット$1/2$で消去すると，残る$1\times1$のSchur補行列は$1/2-(1/2)(1/2)^{-1}(1/2)=0$になる．消去は2段で終わり，階数2が検出される．商の公式どおり，これは左上$2\times2$のピボット行列$A=\begin{pmatrix}2&1\\1&1\end{pmatrix}$に関するSchur補行列

$$
M/A=5-\begin{pmatrix}3&2\end{pmatrix}\begin{pmatrix}1&-1\\-1&2\end{pmatrix}\begin{pmatrix}3\\2\end{pmatrix}=5-5=0
$$

と一致する．ピボットの積$2\cdot\frac{1}{2}=1$は$\det A=1$に等しい．

:::

## Feshbach射影：エネルギー依存の有効Hamiltonian

### 有効Hamiltonianと自己エネルギー

状態空間を着目する部分空間とその直交補空間に分け，それぞれへの射影演算子を$P$，$Q=I-P$とする．この分解に沿ってGreen函数の定義に現れる$zI-H$を書くと

$$
zI-H=\begin{pmatrix}zP-PHP&-PHQ\\-QHP&zQ-QHQ\end{pmatrix}
$$

で，$Q$側の変数を消去すると，逆行列のブロックの恒等式$(M^{-1})_{11}=(M/D)^{-1}$から

$$
PG(z)P=\bigl(zP-H_{\mathrm{eff}}(z)\bigr)^{-1},\qquad H_{\mathrm{eff}}(z)\coloneqq PHP+PHQ\,(zQ-QHQ)^{-1}\,QHP
$$

を得る（逆行列はそれぞれ$P$と$Q$の部分空間の中で取る）．これが[Feshbach射影](https://en.wikipedia.org/wiki/Feshbach%E2%80%93Fano_partitioning)の有効Hamiltonianで，第2項$\Sigma(z)\coloneqq PHQ\,(zQ-QHQ)^{-1}QHP$を自己エネルギーと呼ぶ．Feshbachはこれを原子核反応の理論で導入した[^feshbach]．同じ導出は，TCIの論文でもSchur補行列の性質の1つとして紹介されている[^tci]．

$H_{\mathrm{eff}}(z)$はエネルギー$z$に依存し，消去した$Q$側の自由度の情報はこの依存性の中に残っている．実際，状態空間が有限次元なら，行列式の恒等式$\det M=\det D\,\det(M/D)$を$z=E$で使うと，$E$が$QHQ$の（$Q$空間での）固有値でない限り

$$
\det(EI-H)=\det(EQ-QHQ)\,\det\bigl(EP-H_{\mathrm{eff}}(E)\bigr)
$$

なので，$E$が$H$の固有値であることと，非線形な固有値問題$H_{\mathrm{eff}}(E)\psi=E\psi$が$P$空間で解をもつことは同値である．$QHQ$の固有値と重ならない$H$の固有値は，すべて$P$空間の小さな問題から求まる．

:::details 導出：2準位系

$H=\begin{pmatrix}\varepsilon_1&v\\v&\varepsilon_2\end{pmatrix}$（$v\neq0$）で$P$を1番目の状態への射影とすると，$H_{\mathrm{eff}}(z)=\varepsilon_1+v^2/(z-\varepsilon_2)$は$1\times1$である．$E=H_{\mathrm{eff}}(E)$の両辺に$E-\varepsilon_2$を掛けると$(E-\varepsilon_1)(E-\varepsilon_2)-v^2=0$となり，これは$H$の固有多項式そのものである．$1\times1$の有効Hamiltonianから，$H$の2つの固有値が両方とも出てくる．

$|v|\ll|\varepsilon_1-\varepsilon_2|$のとき，$H_{\mathrm{eff}}(E)$の$E$を$\varepsilon_1$で置き換えると，2次摂動のエネルギー$\varepsilon_1+v^2/(\varepsilon_1-\varepsilon_2)$になる．近似はこの置き換えで入る．

:::

### 半無限鎖の自己エネルギー

半無限鎖で$P$を端のサイト，$Q$を残りの鎖とすると，$QHQ$は2番目のサイトから始まる同じ半無限鎖で，$PHQ$はホッピング$w$だけである．したがって自己エネルギーは$w^2\bigl((zQ-QHQ)^{-1}\bigr)_{22}=w^2g(z)$で，連分数の節の$\Sigma(z)$に一致する．連分数の1段目$G_{11}(z)=1/(z-\varepsilon-\Sigma(z))$は，物理の言葉で読めば，端のサイトのエネルギー$\varepsilon$に残りの鎖からの自己エネルギーが加わるという式である．帯の中で$\Sigma$が虚部をもつことは，端のサイトに置いた粒子が残りの鎖へ広がっていくことの表れで，次節ではこれを時間の言葉で見る．

## Mori-Zwanzig形式：記憶をもつ運動方程式

### 線形の運動方程式からの消去

着目する変数$x$と，消去したい変数$y$からなる線形の運動方程式

$$
\frac{d}{dt}\begin{pmatrix}x\\y\end{pmatrix}=\begin{pmatrix}L_{11}&L_{12}\\L_{21}&L_{22}\end{pmatrix}\begin{pmatrix}x\\y\end{pmatrix}
$$

を考える．[Laplace変換](https://en.wikipedia.org/wiki/Laplace_transform)$\hat x(s)\coloneqq\int_0^\infty\mathrm{e}^{-st}x(t)\,dt$を施すと（$\operatorname{Re}s$は以下の積分がすべて収束するだけ大きく取る），微分が$s$倍になり，初期値を右辺に移した連立一次方程式

$$
\begin{pmatrix}s-L_{11}&-L_{12}\\-L_{21}&s-L_{22}\end{pmatrix}\begin{pmatrix}\hat x\\\hat y\end{pmatrix}=\begin{pmatrix}x(0)\\y(0)\end{pmatrix}
$$

になる．ここから$\hat y$を消去すると

$$
\bigl(s-L_{11}-\hat K(s)\bigr)\hat x(s)=x(0)+L_{12}(s-L_{22})^{-1}y(0),\qquad\hat K(s)\coloneqq L_{12}(s-L_{22})^{-1}L_{21}
$$

で，左辺の係数はSchur補行列であり，Feshbach射影の$zP-H_{\mathrm{eff}}(z)$と同じ形をしている．逆Laplace変換で時間領域に戻すと

$$
\frac{dx}{dt}=L_{11}x(t)+\int_0^tK(t-\tau)\,x(\tau)\,d\tau+F(t),\qquad K(\tau)=L_{12}\mathrm{e}^{L_{22}\tau}L_{21},\quad F(t)=L_{12}\mathrm{e}^{L_{22}t}y(0)
$$

となる．Laplace変換の側の積$\hat K(s)\hat x(s)$は時間領域では畳み込みになり，$x$の時間変化が現在の値だけでなく過去の履歴$x(\tau)$（$0\le\tau\le t$）にも依存するようになる．この$K$を記憶核と呼ぶ．$F(t)$は消去した変数の初期値だけで決まる項で，$y(0)$が統計的にしか与えられない状況では揺動力として扱われる．

力学そのものが非線形でも，物理量の時間発展はLiouville演算子による線形の方程式に従う．そこで着目する物理量への射影演算子とその補を物理量の空間で定義すると，同じ消去が演算子のレベルで実行でき，瞬間的な項・記憶項・揺動力の項からなる方程式が厳密に導かれる．これがZwanzigとMoriによる射影演算子法，Mori-Zwanzig形式である[^mz]．上の線形の例は，その消去がSchur補行列として直接見える場合にあたる．射影の対象を物理量ではなく状態（密度演算子）に取ったものがNakajima-Zwanzig方程式で[^nz]，開放量子系で着目系の縮約密度行列の運動方程式を導くのに使われる．次の半無限鎖の例は状態ベクトルの成分を射影しているので，構造としてはこちらにあたる．

### 半無限鎖の記憶核

量子力学の時間発展$\mathrm{i}\,d\psi/dt=H\psi$は$L=-\mathrm{i}H$の線形方程式で，$sI-L=-\mathrm{i}(zI-H)$（ただし$z=\mathrm{i}s$，$\operatorname{Re}s>0$と$\operatorname{Im}z>0$が対応する）となるので，$\hat K(s)=-\mathrm{i}\,\Sigma(\mathrm{i}s)$が成り立つ．Feshbach射影の自己エネルギーと記憶核のLaplace変換は，$z=\mathrm{i}s$という変数の読み替えで結ばれている．

半無限鎖で端のサイトから出発した粒子が端のサイトに残る振幅$a(t)\coloneqq\bigl(\mathrm{e}^{-\mathrm{i}Ht}\bigr)_{11}$を考える．$x$を端のサイトの振幅，$y$を残りのサイトの振幅とすると$y(0)=0$なので，揺動力の項はない．記憶核は$K(\tau)=-w^2\bigl(\mathrm{e}^{-\mathrm{i}QHQ\tau}\bigr)_{22}$で，残りの鎖も同じ半無限鎖なので，これは$-w^2a(\tau)$に等しい．運動方程式は

$$
\frac{da}{dt}=-\mathrm{i}\varepsilon\,a(t)-w^2\int_0^ta(t-\tau)\,a(\tau)\,d\tau
$$

という閉じた方程式になる．$a$自身が記憶核として右辺に現れる．解は[Bessel函数](https://en.wikipedia.org/wiki/Bessel_function)$J_1$を使って

$$
a(t)=\mathrm{e}^{-\mathrm{i}\varepsilon t}\,\frac{J_1(2wt)}{wt}
$$

と書ける．短時間では$a(t)\approx\mathrm{e}^{-\mathrm{i}\varepsilon t}\bigl(1-(wt)^2/2\bigr)$と減り，長時間では$J_1$の漸近形から振動しながら$(wt)^{-3/2}$で減衰する．

:::details 導出：$a(t)$のBessel函数表示

$H$の固有状態で展開すると$a(t)=\int\rho(\omega)\,\mathrm{e}^{-\mathrm{i}\omega t}\,d\omega$で，$\rho$は連分数の節で求めた端のサイトの局所状態密度である．$\omega-\varepsilon=2wu$と置換すると

$$
a(t)=\mathrm{e}^{-\mathrm{i}\varepsilon t}\,\frac{2}{\pi}\int_{-1}^{1}\sqrt{1-u^2}\,\mathrm{e}^{-2\mathrm{i}wtu}\,du
$$

となる．被積分函数の虚部は$u$について奇函数なので消え，Bessel函数の積分表示$J_1(\xi)=\frac{\xi}{\pi}\int_{-1}^{1}\sqrt{1-u^2}\cos(\xi u)\,du$を$\xi=2wt$で使うと本文の式を得る．

:::

記憶核を，過去の履歴を現在の値で置き換えた瞬間的な項にする近似がMarkov近似である．自由な位相回転だけを戻して$x(\tau)\approx\mathrm{e}^{\mathrm{i}\varepsilon(t-\tau)}x(t)$と置き，積分の上限を無限大に延ばすと，記憶項は$\hat K(-\mathrm{i}\varepsilon+0)\,x(t)=-\mathrm{i}\,\Sigma(\varepsilon+\mathrm{i}0)\,x(t)$になる．帯の中心では$\Sigma(\varepsilon+\mathrm{i}0)=-\mathrm{i}w$なので

$$
\frac{da}{dt}\approx(-\mathrm{i}\varepsilon-w)\,a(t),\qquad a(t)\approx\mathrm{e}^{-\mathrm{i}\varepsilon t-wt}
$$

の指数減衰になる．Laplace変換の側で見れば，Markov近似は$\Sigma(z)$を定数$\Sigma(\varepsilon+\mathrm{i}0)$で置き換える近似である．この鎖では記憶核の変化と振幅の減衰がどちらも$1/w$程度の時間で起こり，置き換えを正当化する時間尺度の分離がないので，厳密解の$(wt)^{-3/2}$のべき減衰も短時間の$1-(wt)^2/2$も再現されない．

### 記憶核の階層とMoriの連分数

記憶核$K(\tau)=-w^2a(\tau)$の中身は，2番目のサイトから始まる鎖で2番目のサイトに残る振幅である．これにも同じ消去を当てると，3番目以降のサイトによる記憶核が現れる．この階層をLaplace変換の側で並べると，連分数の節の$g(z)=1/\bigl(z-\varepsilon-w^2/(z-\varepsilon-\cdots)\bigr)$に戻る．一般の系でも，記憶核に射影演算子法を繰り返し当てることで，時間相関函数のLaplace変換が連分数で表せることをMoriが示している[^mori-cf]．

## まとめ

|  | 消去する変数 | 消去で現れるもの | 扱い | 近似の入り方 |
| ---- | ---- | ---- | ---- | ---- |
| 連分数 | 2番目以降のサイト | 各段の分母の補正項 | 残す | 有限段での打ち切り |
| CI・prrLU分解による低ランク近似 | ピボットの行と列 | 残りのブロックのSchur補行列$M/A$ | 捨てる（近似誤差になる） | Schur補行列を0とみなす |
| Feshbach射影 | $Q$空間 | 自己エネルギー$\Sigma(z)$ | 残す | 摂動などによる$\Sigma(z)$の近似 |
| Mori-Zwanzig形式 | 着目しない変数$y$ | 記憶核$K$と揺動力$F$ | 残す | Markov近似など |

- Schur補行列$M/A=D-CA^{-1}B$は，連立一次方程式から変数$x$を消去したとき残りの変数$y$に掛かる行列である．行列式・逆行列のブロック・ランク・商の公式の4つの恒等式が，これらの応用を支える．
- 連分数・Feshbach射影・Mori-Zwanzig形式ではSchur補行列を残すので消去は厳密で，近似は連分数の打ち切り，自己エネルギーの近似，Markov近似としてその後に入る．半無限鎖では3つとも同じ函数$\Sigma(z)$で書ける．
- CIはSchur補行列を捨てる近似で，誤差はSchur補行列そのものである．最大体積原理は誤差を小さくするピボットの選び方として，prrLU分解はSchur補行列を1段ずつ作る算法として理解できる．

## 文献案内

- [Y. Núñez Fernández et al., "Learning tensor networks with tensor cross interpolation: New algorithms and libraries", SciPost Phys. 18, 104 (2025)](https://doi.org/10.21468/SciPostPhys.18.3.104)（[arXiv:2407.02454](https://arxiv.org/abs/2407.02454)）: 3節でSchur補行列の性質（商の公式，CIとの関係，自己エネルギーとの関係）とprrLU分解をまとめている．
- [F. Zhang (ed.), _The Schur Complement and Its Applications_ (Springer, 2005)](https://doi.org/10.1007/b105056): Schur補行列とその応用を扱った本．
- [J. Sjöstrand, M. Zworski, "Elementary linear algebra for advanced spectral problems", Ann. Inst. Fourier 57, 2095 (2007)](https://doi.org/10.5802/aif.2328)（[arXiv:math/0312166](https://arxiv.org/abs/math/0312166)）: Grushin問題の方法を軸に，Schur補行列やFeshbach射影を数理物理の無限次元のスペクトル問題に使う解説．

[^quotient]: [D. E. Crabtree, E. V. Haynsworth, "An identity for the Schur complement of a matrix", Proc. Amer. Math. Soc. 22, 364 (1969)](https://doi.org/10.1090/S0002-9939-1969-0255573-1)．

[^haydock]: [R. Haydock, V. Heine, M. J. Kelly, "Electronic structure based on the local atomic environment for tight-binding bands", J. Phys. C 5, 2845 (1972)](https://doi.org/10.1088/0022-3719/5/20/004)．

[^tci]: [Núñez Fernández et al. (2025)](https://doi.org/10.21468/SciPostPhys.18.3.104)の3節．文献案内も参照．

[^feshbach]: [H. Feshbach, "Unified theory of nuclear reactions", Ann. Phys. 5, 357 (1958)](https://doi.org/10.1016/0003-4916(58)90007-1)．

[^mz]: [R. Zwanzig, "Memory effects in irreversible thermodynamics", Phys. Rev. 124, 983 (1961)](https://doi.org/10.1103/PhysRev.124.983)；[H. Mori, "Transport, collective motion, and Brownian motion", Prog. Theor. Phys. 33, 423 (1965)](https://doi.org/10.1143/PTP.33.423)．

[^nz]: [S. Nakajima, "On quantum theory of transport phenomena", Prog. Theor. Phys. 20, 948 (1958)](https://doi.org/10.1143/PTP.20.948)；[R. Zwanzig, "Ensemble method in the theory of irreversibility", J. Chem. Phys. 33, 1338 (1960)](https://doi.org/10.1063/1.1731409)．

[^mori-cf]: [H. Mori, "A continued-fraction representation of the time-correlation functions", Prog. Theor. Phys. 34, 399 (1965)](https://doi.org/10.1143/PTP.34.399)．
