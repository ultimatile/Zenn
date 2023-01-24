---
title: "スパコンでHPXをbuildする"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [cpp, hpx, 並列計算]
published: true
---

# はじめに
HPXはC++ 並列・並行計算libraryです.
https://hpx.stellar-group.org
https://github.com/STEllAR-GROUP/hpx
https://youtube.com/watch?v=npufmMlGOoM&si=EnSIkaIECMiOmarE
https://qiita.com/MitsutakaTakeda/items/ebf920ae1855423aaee2

とりあえず動いたので試したい人にこれでbuildできたという情報を共有します.

ちなみにvcpkg/Spack/dnfとか使える場合はこんなことしなくて良いです↓.
https://hpx-docs.stellar-group.org/latest/html/quickstart.html

環境はRed Hat Enterprise Linux release 8.6 (Ootpa)で, CPUは128論理コアのものを使っています.

# buildに必要なもの
buildには[CMake](https://cmake.org)を使います.
buildに必要なlibraryは[Boost](https://www.boost.org)と[hwloc](https://www.open-mpi.org/projects/hwloc/)です.
TCMallocは使わなくてもbuildは可能ですが使わないと遅いとキレられるので入れます^[[gperftools](https://github.com/gperftools/gperftools)のものと[Google repositoryのもの](https://github.com/google/tcmalloc)があります.
後者のbuildに[Bazel](https://github.com/bazelbuild/bazel)というbuilderが必要で面倒なので前者にします.
https://google.github.io/tcmalloc/gperftools.html]^[ちなみに必ずしもTCMallocである必要はなく, [jemalloc](https://jemalloc.net), [mimalloc](https://microsoft.github.io/mimalloc/), [tbbmalloc](https://github.com/oneapi-src/oneTBB/tree/c21e688ad07a446f168b4298443e2d1ced57e7bd/src/tbbmalloc)にも対応しているようです.].

HPXのbuildに関する詳細な情報は[こちら](https://hpx-docs.stellar-group.org/branches/master/html/manual/building_hpx.html)です.

# やること
1. CMakeの準備(省略)
2. Boostのdownload
3. hwlocのbuild
4. tcmallocのbuild
5. HPXのbuild

# Boostのdownload
[公式website](https://www.boost.org)から落とします.
Boostを置きたい場所で以下を実行します.

```bash:
wget https://boostorg.jfrog.io/artifactory/main/release/1.81.0/source/boost_1_81_0.tar.gz
tar xvf boost_1_81_0.tar.gz
```

versionは適宜読み替えてください.

## Boostのbuildの必要性
HPXはAsioを要求するのですが, [Boost.Asio](https://www.boost.org/doc/libs/1_81_0/doc/html/boost_asio.html)を使いたい場合はBoostのbuildが必要です.
最初はBoost.Asioを使おうとしようとしていたのですがBoost.Asioのversion情報がうまく渡せなくて動かなかったので, `-DHPX_WITH_FETCH_ASIO=ON`を指定してHPXに落としてきてもらいました.
HPXに落としてもらう場合はBoostのbuildは不要です.
この設定を使うとAsioを落とすために外部と通信する必要があるため, 計算nodeではbuildの設定ができないことに注意してください.

## hwlocのbuild
[公式website](https://www.open-mpi.org/projects/hwloc/)から落としてGNU Autotoolsでbuildします.
hwlocのsourceを置きたい場所で以下を実行します.

```bash:
wget https://download.open-mpi.org/release/hwloc/v2.9/hwloc-2.9.0.tar.gz
tar xvf hwloc-2.9.0.tar.gz
mkdir hwloc-2.9.0/build && cd hwloc-2.9.0/build
../configure --prefix=$HOME
make 
make install
```

versionは適宜読み替えてください.
`--prefix`にはhwlocのbinaryを置く場所を指定してください.
恐らくdefaultが`/usr/local/`でスパコンuserは使えないと思うのでどこか使える場所を指定してください.
またbuild directoryを`build`にしていますが, 他の名前でも問題ありません.

## tcmallocのbuild
[gperftoolsのrelease](https://github.com/gperftools/gperftools/releases)から落としてbuildします.

```bash:
wget https://github.com/gperftools/gperftools/releases/download/gperftools-2.10/gperftools-2.10.tar.gz
tar xvf gperftools-2.10.tar.gz
cd gperftools-2.10
cmake -S . -Bbuild
cmake --build build
```

versionは適宜読み替えてください.

説明が見つからなくて適当にやったので間違っていたら教えてください.

# HPXのbuild
## HPXのdownload
まず[HPXのリリース](https://github.com/STEllAR-GROUP/hpx/releases)を落として展開します.

```bash:
wget https://github.com/STEllAR-GROUP/hpx/archive/refs/tags/1.8.1.tar.gz
tar xvf 1.8.1.tar.gz
```

versionは適宜読み替えてください.

## buildの設定
展開したHPXのdirectoryに移動して以下を実行します.

```bash:
cmake -S . -Bbuild -DCMAKE_INSTALL_PREFIX=$HOME -DBOOST_ROOT=$HOME/boost_1_81_0 -DHPX_WITH_FETCH_ASIO=ON -DHWLOC_ROOT=$HOME/hwloc-2.9.0/build/hwloc/.libs -DTCMALLOC_ROOT=$HOME/gperftools-2.10/build -DTCMALLOC_INCLUDE_DIR=$HOME/gperftools-2.10/build/gperftools -DHPX_WITH_MORE_THAN_64_THREADS=ON -DHPX_WITH_MAX_CPU_COUNT=128 -DHPX_WITH_PARCELPORT_MPI=ON -DHPX_WITH_PARCELPORT_TCP=OFF
```

変数に渡している値は私が用いたものですので, 実行する際は適宜書き換えてください.
各変数については以下で説明します.

### 変数の説明
ここに登場していない変数も多数ありますので他の変数が気になる方は[こちら](https://hpx-docs.stellar-group.org/latest/html/manual/cmake_variables.html)を読んでください.

#### `-S`, `-B`
`-S`はsourceのdirectory, `-B`はbuild directoryを指定します.
build directoryの名前は`build`以外でも構いませんので`-Bhoge`などのように変更できます.

#### `-DCMAKE_INSTALL_PREFIX`
HPXのbinaryを置く場所を指定します.
default設定が`/usr/local/`でスパコンuserは使えないと思うのでどこか使える場所を指定してください.

#### `-DBOOST_ROOT`
そのままですがBoostのrootの場所を指定します.

#### `-DHPX_WITH_FETCH_ASIO=ON`
AsioをHPXに落としてもらう場合に指定します.
Boost.Asioを使う場合はこの変数の指定は不要です.

#### `-DHWLOC_ROOT`
そのままですがhwlocのrootの場所を指定します.

#### `-DTCMALLOC_ROOT`
そのままですがTCMallocのrootの場所を指定します.

#### `-DTCMALLOC_INCLUDE_DIR`
そのままですがTCMallocのincludeする場所を指定します.

#### `-DHPX_WITH_MORE_THAN_64_THREADS=ON`
65 thread以上の計算を走らせるには`-DHPX_WITH_MORE_THAN_64_THREADS=ON`を指定します.
64 thread以下の計算しか行わない場合はこの変数の指定は不要です.

#### `-DHPX_WITH_MAX_CPU_COUNT`
`-DHPX_WITH_MAX_CPU_COUNT`はHPXで扱える最大CPU数を指定します.
defaultは64で論理coreの数以上にした方が良いようです.
論理coreの数が64以下の場合はこの変数の指定は不要です.

#### `-DHPX_WITH_PARCELPORT_MPI=ON`/`-DHPX_WITH_PARCELPORT_TCP=OFF`
通信にMPIを使う場合に指定するoptionです.
defalutは`-DHPX_WITH_PARCELPORT_MPI=DFF`/`-DHPX_WITH_PARCELPORT_TCP=ON`ですが遅いのでMPIを使った方が良いそうです.
MPIを使わない場合これらの変数の指定は不要です.

## buildの実行
設定が完了したらbuildを実行します.

```bash
cmake --build build --target install
```

以上です.
実際にHPXを動かしてみたい方は[HPXのhello world](https://hpx-docs.stellar-group.org/latest/html/quickstart.html#hello-world)などを見てください.