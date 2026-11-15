---
title: "テンソルコンパイラは何を見て何を決めるか"
emoji: "🧩"
type: "tech"
topics: ["compiler", "jax", "pytorch", "tvm", "tensornetwork"]
published: false
register: "keitai"
---

## はじめに

テンソルネットワーク計算をGPUで速くしたいとき、[JAX](https://docs.jax.dev/)の`jax.jit`、[PyTorch](https://pytorch.org/)の`torch.compile`、[Apache TVM](https://tvm.apache.org/)のような、テンソル計算向けのコンパイラが候補に挙がります。

テンソルネットワークは、複数のテンソルを共有する添字で結び、その縮約として計算を表す方法です。量子多体系では、巨大な状態ベクトルを小さなテンソルの組み合わせで近似するために使います。テンソル同士を結ぶ添字の長さをボンド次元と呼びます。ボンド次元は、特異値分解（SVD）で小さい特異値を切り捨てるたびに変わり得ます。

この計算を`jax.jit`で包むと、これまでに現れていないボンド次元が来るたびにコンパイルが走ります。JAXが下で使う[XLA](https://openxla.org/xla)が、配列の各次元の長さと要素型に特殊化したコードを作るためです（[JAXのドキュメント](https://docs.jax.dev/en/latest/debugging/slow_tracing_compilation.html)）。

本記事では、テンソルコンパイラを構成する技術について、何を受け取り、何を提供し、どんなときに使うべきで、どんなときに使いづらいかを整理します。初めに、LLVM IRとは別にテンソル用のIRが必要になる理由と、MLIRの位置づけを確認します。次に整理の軸を置き、JAX＋XLA、`torch.compile`、TVM、[Triton](https://triton-lang.org/)、[IREE](https://iree.dev/)を順に見ます。最後に、テンソルネットワーク計算へ当てはめます。

各技術の挙動は、2026年11月時点のドキュメントとソースコードで確認しています。

## なぜLLVM IRとは別のIRが必要なのか

### 中間表現とロワーリング

コンパイラは、ソースコードを直接機械語へ置き換えるのではなく、途中に解析・変換しやすい形式を置きます。これを中間表現、IR（Intermediate Representation）と呼びます。

[LLVM](https://llvm.org/)は、IR、その上の最適化、各種ハードウェア向けのコード生成器を提供するコンパイラ基盤です。C/C++のフロントエンドである[Clang](https://clang.llvm.org/)のほか、Rust、Julia、Swiftなどのコンパイラも、最終段でLLVMを使います。[LLVM IR](https://llvm.org/docs/LangRef.html)は、加算、メモリの読み書き、分岐、函数呼び出しといった操作でプログラムを表します。多次元配列は、アドレスの計算とポインターを介した読み書きになります。

抽象度の高い操作を、より具体的な操作へ変換することをロワーリング（lowering）と呼びます。たとえば、行列積をループへ、ループ内の計算をベクトル命令へ、という変換です。

### 低い層では失われる情報

ロワーリングすると、上の層で持っていた情報が失われます。

「行列積」という演算名が残っていれば、行列積ライブラリを呼ぶか、自前のカーネルを生成するかを比較できます。後続のバイアス加算やReLUまで1つのカーネルにまとめ、途中結果をメモリへ書き戻さずに済ませる変換も考えられます。こうして複数の演算をまとめることを融合（fusion）と呼びます。ところが、行列積をポインターの加算と読み書きへ展開した後では、元が行列積だったことを認識し直すために追加の解析が必要です。前後の演算との関係も復元しなければなりません。

[MLIRの論文](https://arxiv.org/abs/2002.11054)は、LLVM IRより高い抽象度で扱うべき問題が多いと述べ、例としてC++のソースレベルの解析をLLVM IR上で行う難しさを挙げています。同じ論文によれば、Swift、Rust、Julia、Fortranは言語固有の最適化のために独自のIRを持ち、機械学習のシステムも「MLグラフ」を同じ目的で持っています。

テンソル計算には、さらにハードウェア側の事情があります。NVIDIAのTensor Coreのような専用命令は、多次元の領域に対する行列積などをまとめて実行します。[TensorIRの論文](https://arxiv.org/abs/2207.04296)は、従来の機械学習コンパイラがスカラー演算を囲むループの変換を探索するもので、こうした命令を使うプログラムを自動では扱えていないと指摘し、テンソル計算の単位をIRに残す設計を提案しています。

そのため、テンソルコンパイラは少なくとも2つの層を持ちます。グラフの層では、行列積や要素ごとの演算を単位として、融合する範囲やライブラリに任せる演算を決めます。カーネルの層では、1つの計算をどう分割し、どのスレッドへ割り当て、どの命令で実行するかを決めます。

### MLIRは、専用IRを作る費用を下げる基盤

[MLIR](https://mlir.llvm.org/)は、それ自体がテンソル用のIRというわけではありません。論文のabstractは、目的をソフトウェアの断片化への対処と、ドメイン固有のコンパイラを作る費用の削減としています。各言語や機械学習のシステムがそれぞれ高水準のIRを作り、同じ種類の技術を作り直していた状況への対処です。

MLIRでは、演算や型とその規則をdialectという単位で定義します。複数のdialectを同じIRの中に共存させ、高い抽象度のdialectから低いdialectへ段階的にロワーリングします。テンソル計算に関わるdialectには、たとえば次のものがあります。

| dialect | 表すもの |
| --- | --- |
| [StableHLO](https://openxla.org/stablehlo) | 行列積、畳み込み、要素ごとの演算など、モデルに近いテンソル演算です。フレームワークとコンパイラの間の交換形式として使います。 |
| [Linalg](https://mlir.llvm.org/docs/Dialects/Linalg/) | 線形代数演算の反復領域、添字の対応、縮約軸です。融合やタイル分割の対象になります。 |
| [Vector](https://mlir.llvm.org/docs/Dialects/Vector/) | 多次元のベクトル演算です。対象ハードウェアのベクトル命令へ変換します。 |
| [LLVM dialect](https://mlir.llvm.org/docs/Dialects/LLVM/) | LLVM IRに対応する操作です。ここからLLVM IRへ変換し、LLVMのコード生成器へ渡します。 |

後で見る技術のうち、IREEはMLIRの上に作られ、Tritonは内部で[独自のMLIR dialect](https://triton-lang.org/main/dialects/dialects.html)を使い、XLAはStableHLOを入力として受け取ります。TVMのIRはMLIRのdialectではありません。

## 整理の軸

各技術の違いは、次の3つの軸で見ると説明しやすくなります。

### 計算をどう受け取るか

1つ目は、計算の受け取り方です。

トレースは、Pythonの函数を、具体的な値の代わりに形状や要素型だけを持つ抽象的な値で実行し、そこで行われた配列演算を記録する方式です。JAXと`torch.compile`がこの方式を使います。トレースでは、Pythonの`if`文などは、トレースしたときに通った側だけが記録されます。そのため、配列の値によって分岐する処理は、そのままではIRに取り込めません。

取り込みは、[ONNX](https://onnx.ai/)のファイルやStableHLOなど、エクスポート済みのモデルを読む方式です。TVMとIREEがこの方式を使います。

手書きは、カーネルそのものを専用の言語で書く方式です。Tritonがこれにあたります。

### 形状をいつ確定させるか

2つ目は、配列の形状をいつ確定させるかです。

形状が分かった時点で、その形状専用のコードを作ることを特殊化と呼びます。長さが分かれば、タイルの大きさや命令の選択を固定でき、生成コードを速くしやすくなります。その代わり、新しい形状が現れるたびにコンパイルが必要です。

コンパイルと探索にかかる時間を$T_c$、もとの1回の実行時間を$t_0$、特殊化した後の実行時間を$t_1$、同じコードを使う回数を$n$とすると、特殊化の費用を回収できる条件は

$$
T_c+n t_1<n t_0
\quad\Longleftrightarrow\quad
n>\frac{T_c}{t_0-t_1}
\qquad(t_0>t_1)
$$

です。たとえば$T_c=2$秒、$t_0=10$ミリ秒、$t_1=6$ミリ秒なら、500回を超えて同じ形状を実行しないと元が取れません。

もう1つの方法は、長さを`n`のような記号のまま扱い、1つのコードで複数の形状を処理する方法です。これを記号的な形状（symbolic shape）と呼びます。コンパイルは一度で済みますが、後で見るように、自動チューニングや外部ライブラリへの委譲が具体的な長さを前提にしている場合があります。

形状が変わる理由も区別しておく必要があります。呼び出しのたびに入力の長さが変わる場合と、計算結果の値によって出力の長さが決まる場合（データ依存の形状）では、扱える技術が異なります。たとえば、条件を満たす要素だけを取り出す演算の出力の長さは、入力の値を見るまで分かりません。

### どの演算がIRの外に出るか

3つ目は、コンパイラが中身を変換できる範囲です。

行列積をcuBLASのようなライブラリへ任せたり、SVDやQR分解をLAPACKやcuSOLVERの呼び出しにしたりすると、その演算はコンパイラにとって中身の見えない呼び出しになります。中身が見えないので、呼び出しの前後をまたぐ融合はできません。[XLAのGPU向けの解説](https://openxla.org/xla/gpu_architecture)も、cuBLASなどの呼び出しが複雑な融合を妨げることが多いと述べています。

## 各技術の整理

### JAX＋XLA

JAXは、Pythonの函数をトレースし、`grad`による自動微分や`vmap`によるバッチ化などの変換を組み合わせて、StableHLOへ変換します。XLAは、それを受け取ってグラフを最適化し、CPUやGPU向けのコードを生成します。

トレースに使う値は、形状と要素型を持ち、具体的な値を持ちません（[JAXのトレースの解説](https://docs.jax.dev/en/latest/tracing.html)）。そのため、`jax.jit`の内側で制御フローを左右できるのは、形状や要素型のような静的な属性だけです（[JITの解説](https://docs.jax.dev/en/latest/jit-compilation.html)）。`static_argnums`で指定した引数は、その値がキャッシュのキーに入り、値が変わると再コンパイルになります。

XLAは、配列の各次元の長さと要素型に特殊化したコードを作ります。そのため、新しい形状が来るたびにトレースとコンパイルがやり直しになります。さらに、`jax.jit`の内側では、出力と途中の配列がすべて静的な形状を持つ必要があります（[よくある落とし穴](https://docs.jax.dev/en/latest/notebooks/Common_Gotchas_in_JAX.html)）。たとえば非ゼロ要素の位置を返す[`jnp.nonzero`](https://docs.jax.dev/en/latest/_autosummary/jax.numpy.nonzero.html)は、出力の長さ`size`を静的に指定しないと`jax.jit`の内側で使えません。[`lax.while_loop`](https://docs.jax.dev/en/latest/_autosummary/jax.lax.while_loop.html)でループをまたいで受け渡す値も、反復を通して同じ形状と要素型を保つ必要があります。

再コンパイルの費用を減らす仕組みもあります。[永続コンパイルキャッシュ](https://docs.jax.dev/en/latest/persistent_compilation_cache.html)は、コンパイル結果をプロセスをまたいで再利用します。ただし、キャッシュのキーには最適化前のHLOが含まれ、既定ではコンパイルに1秒を超えたものなどに限って保存されます。初めて現れる形状のコンパイル費用は残ります。[`jax.export`の形状多相性](https://docs.jax.dev/en/latest/export/shape_poly.html)を使うと、複数の形状に対してトレースとロワーリングを一度で済ませられますが、コンパイルは具体的な形状ごとに行われます。

XLAで最も重要な最適化は融合で、GPUでは1つの融合が1つのカーネルになります（[XLA:GPUの解説](https://openxla.org/xla/gpu_architecture)）。行列積などにはcuBLASやcuDNNを呼び、行列積やsoftmaxを含む融合のコード生成には内部でTritonを使います。`jnp.linalg.svd`、`qr`、`eigh`は、CPUではLAPACK、GPUではcuSOLVERの函数を呼ぶカスタムコールになります（[`jax/_src/lax/linalg.py`](https://github.com/jax-ml/jax/blob/main/jax/_src/lax/linalg.py)）。

JAX＋XLAが向いているのは、同じ形状の計算を何度も繰り返し、自動微分やバッチ化を組み合わせたい場合です。形状の種類が多く、それぞれの実行回数が少ない計算や、データ依存の形状を含む計算では使いづらくなります。

### PyTorchの`torch.compile`

`torch.compile`は、TorchDynamo、AOTAutograd、TorchInductorの3つで構成されます。TorchDynamoは、CPythonの函数フレームの評価に介入する仕組み（[PEP 523](https://peps.python.org/pep-0523/)）を使い、Pythonのバイトコードを書き換えて、PyTorchの演算列を[FX](https://docs.pytorch.org/docs/stable/fx.html)のグラフとして取り出します（[Dynamoの概要](https://docs.pytorch.org/docs/2.15/user_guide/torch_compiler/torch.compiler_dynamo_overview.html)）。取り出したグラフには、それが有効である条件（ガード）が付き、すべての条件を満たすときだけコンパイル済みのコードを実行します。

JAXとの違いは、トレースできない処理に出会ったときの振る舞いです。値に依存する`if`文や一部の組み込み函数に出会うと、Dynamoはそこでグラフを分断し、その部分を通常のPythonとして実行します（graph break）。プログラム全体が一度にコンパイルできなくても動きますが、分断が多いと融合できる範囲が狭くなります。

形状の扱いも異なります（[動的形状の解説](https://docs.pytorch.org/docs/2.15/user_guide/torch_compiler/torch.compiler_dynamic_shapes.html)）。初回は全形状を静的と仮定してコンパイルし、形状が変わってガードに失敗すると、変わった次元を記号的な形状として再コンパイルします。この挙動をautomatic dynamicと呼びます。長さ0と1は記号にせず特殊化します。再コンパイルの回数には上限があり（`torch._dynamo.config.recompile_limit`、既定値8）、超えるとその函数はコンパイルせず通常のPyTorchで実行します（[トラブルシューティング](https://docs.pytorch.org/docs/2.15/user_guide/torch_compiler/torch.compiler_troubleshooting.html)）。データ依存の形状を返す`nonzero`や、テンソルからPythonの数値を取り出す`.item()`は、既定ではgraph breakになります（[`torch/_dynamo/config.py`](https://github.com/pytorch/pytorch/blob/main/torch/_dynamo/config.py)の`capture_dynamic_output_shape_ops`と`capture_scalar_outputs`）。

TorchInductorは、GPU向けにはTritonのカーネルを、CPU向けにはC++とOpenMPのコードを生成します。既定の設定では、行列積は生成せずPyTorch本体（ATen）の実装を呼びます。`torch.linalg.svd`や`qr`、`eigh`も、Inductorはカーネルを生成せずATenの実装を呼びます（[`torch/_inductor/lowering.py`](https://github.com/pytorch/pytorch/blob/main/torch/_inductor/lowering.py)）。

事前コンパイルには、[`torch.export`](https://docs.pytorch.org/docs/2.15/user_guide/torch_compiler/export.html)で計算グラフを取り出し、[AOTInductor](https://docs.pytorch.org/docs/2.15/user_guide/torch_compiler/torch.compiler_aot_inductor.html)で共有ライブラリにする経路があります。`torch.export`は、トレースできない処理に出会うとgraph breakではなくエラーにします。動的な次元は`torch.export.Dim`で明示します。

`torch.compile`が向いているのは、既存のPyTorchのコードを大きく書き換えずに速くしたい場合や、入力の長さがある程度変わる場合です。graph breakが多いコードや、データ依存の形状が計算の中心にあるコードでは、コンパイルできる範囲が小さくなります。

### TVM

TVMは、エクスポート済みのモデルを取り込み、グラフの層のRelaxと、カーネルの層のTensorIRで最適化して、さまざまなデバイス向けにコンパイルします。最新版はv0.27.0（2026年9月）で、以前のグラフIRであるRelayはv0.20.0で削除されました。モデルは、`torch.export`の結果、ONNX、TensorFlow Lite、StableHLOから取り込めます（[モデルの取り込み](https://tvm.apache.org/docs/how_to/tutorials/import_model.html)）。

Relaxは、記号的な形状を第一級に扱います（[Relaxの設計](https://tvm.apache.org/docs/deep_dive/relax/abstraction.html)）。`R.Tensor(("n", 784), "float32")`のように長さを記号で書き、演算や函数呼び出しをまたいで記号どうしの関係を追跡します。`match_cast`は実行時に形状を検査し、まだ値の決まっていない記号に値を与えます。TensorIRの函数も記号的な次元を持てるので、一度コンパイルしたカーネルで異なる形状を処理できます（[TensorIRの函数の作成](https://tvm.apache.org/docs/deep_dive/tensor_ir/tutorials/tir_creation.html)）。

カーネルの実行方法（スケジュール）を決める仕組みは2つあります（[DLightの解説](https://tvm.apache.org/docs/deep_dive/tensor_ir/tutorials/dlight_gpu_scheduling.html)）。MetaScheduleは、候補を探索して実測し、よいスケジュールを選びます。コンパイルには数分から数時間かかります。DLightは、行列積やリダクションなどの演算の種類ごとに用意された規則でスケジュールを決め、探索せずに数秒でコンパイルします。MetaScheduleの既定の後処理には、ループの範囲が定数でない候補を除外する検査（`DisallowDynamicLoop`）が入っているので、探索には具体的な形状が必要です（`src/s_tir/meta_schedule/postproc/postproc.cc`）。

行列積などをcuBLAS、CUTLASS、cuDNNへ任せることもできます（[外部ライブラリへの委譲](https://tvm.apache.org/docs/arch/external_library_dispatch.html)）。ただし、cuBLASへ任せる条件の1つは、行列積の縮約軸の長さが定数であることです（`python/tvm/relax/backend/cuda/cublas.py`）。SVDやQRの演算はTVM本体のソースに見当たらないので、使うなら外部の函数として登録し、`call_dps_packed`で呼ぶことになります。

TVMは事前コンパイルの方式で、`tvm.compile`で作った実行ファイルをRelaxの仮想マシンが読み込んで実行します（[Relax VM](https://tvm.apache.org/docs/arch/relax_vm.html)）。実行時にPythonをトレースする仕組みは持ちませんが、`torch.compile`のバックエンドとしてTVMを使う`relax_dynamo`があります。

TVMが向いているのは、モデルを多様なデバイスへ配備したい場合や、記号的な形状のまま1つの実行ファイルにまとめたい場合、カーネルのスケジュールを自分で調整したい場合です。形状が記号のままでは自動チューニングが使えず、cuBLASへの委譲も縮約軸の長さが定数の場合に限られます。

### Triton

Tritonは、GPUのカーネルを書くための言語とコンパイラです。プログラマーは、スレッド単位ではなく、データのまとまり（ブロック）単位の処理を書きます。ブロックの大きさは`tl.constexpr`としてコンパイル時の定数にします。メモリアクセスの結合（coalescing）、共有メモリの確保と同期、Tensor Coreを使う命令の選択などは、コンパイラが決めます（[Tritonの導入](https://triton-lang.org/main/programming-guide/chapter-1/introduction.html)）。NVIDIAのGPU向けには、TTIR、TTGIR、LLVM IR、PTXの順にロワーリングします。`torch.compile`やXLAのコード生成にも使われています。

`@triton.jit`は、初回の呼び出し時に引数を見て特殊化します。`tl.constexpr`の引数は値そのものに特殊化します。整数の引数は、値が1であること、16の倍数であること、32ビットに収まることの3点で分類し、その分類に特殊化します。ポインターは16バイト境界に揃っているかどうかで分類します（[`python/src/specialize.cc`](https://github.com/triton-lang/triton/blob/main/python/src/specialize.cc)）。長さが変わっても分類が同じならコンパイル済みのカーネルを再利用し、分類が変わると再コンパイルします。`triton.autotune`は、`key`に指定した引数の値が変わるたびに、用意したすべての設定でカーネルを動かして比較します。

Tritonが向いているのは、ライブラリにない融合カーネルを自分で書きたい場合です。どの演算をどう組み合わせるかはプログラマーが決めるので、グラフ全体を最適化する仕組みはありません。

### IREE

IREEは、MLIRの上に作られたコンパイラと実行環境です。StableHLOや[TOSA](https://mlir.llvm.org/docs/Dialects/TOSA/)を入力に取り、PyTorchのモデルは[iree-turbine](https://iree.dev/guides/ml-frameworks/pytorch/)を介して取り込みます。コンパイルは事前にホストで行い、VMFBという形式のモジュールを出力します。実行時は、IREEの仮想マシンが、ハードウェア抽象化層（HAL）を通じて各デバイスでモジュールを実行します。

IREEは動的な形状と制御フローを扱えます（[IREEのトップページ](https://iree.dev/)）。ただし、[使い方の指針](https://iree.dev/developers/usage-best-practices/)は、形状が静的な部分のほうがよく最適化できると述べています。動的な次元にするなら、バッチ番号のようにメモリ上の配置で外側にあたる（変化の遅い）次元のほうが、画像の縦横やチャネルのように内側にあたる次元より安全だとしています。

CUDA向けの実行環境は、CUDAのドライバーAPIだけを使います（[CUDA HALの設計](https://iree.dev/developers/design-docs/cuda-hal-driver/)）。外部のBLASのような函数を呼ぶ場合は[拡張の仕組み](https://iree.dev/reference/extensions/)を使います。IREEが独自に持つテンソル演算のdialect（LinalgExt）には、ソートやFFT、attentionなどはありますが、SVDやQRはありません。

IREEが向いているのは、実行環境を小さく保ったまま、多様なデバイスへ事前コンパイルしたモデルを配備したい場合です。内側の次元の長さが変わる計算や、分解を含む計算には向きません。

### まとめ

| 技術 | 受け取るもの | 形状の扱い | IRの外に出る演算 |
| --- | --- | --- | --- |
| JAX＋XLA | トレースしたPythonの函数です。 | 具体的な長さに特殊化します。データ依存の形状は使えません。 | SVD・QR・eighはLAPACK・cuSOLVERの呼び出しになります。行列積などはcuBLASを呼びます。 |
| `torch.compile` | バイトコードから取り出したグラフです。 | 初回は特殊化し、形状が変わると記号的な形状で再コンパイルします。データ依存の形状は既定ではgraph breakになります。 | 既定では行列積とSVD・QR・eighをATenの実装に任せます。 |
| TVM | エクスポート済みのモデルです。 | 記号的な形状を扱えます。自動チューニングには具体的な形状が必要です。 | cuBLASなどへ委譲できます。SVD・QRは外部函数として呼びます。 |
| Triton | 手書きのカーネルです。 | 整数の引数を1か、16の倍数かなどで分類して特殊化します。 | グラフを扱わないので対象外です。 |
| IREE | エクスポート済みのモデルです。 | 動的な形状を扱えますが、静的な部分のほうがよく最適化されます。 | LinalgExtにSVD・QRの演算はありません。 |

## テンソルネットワークに当てはめる

ここまでの軸で、テンソルネットワーク計算の性質を見ます。問題になるのは次の3つです。

### ボンド次元が実行中に変わる

SVDの切り捨てでは、残す特異値の個数を、特異値の値と許容誤差から決めます。これはデータ依存の形状です。

JAXでは、`jax.jit`の内側でこの切り捨てを行えません。切り捨てを`jax.jit`の外で行えば、新しいボンド次元が現れるたびに、それを使う縮約の再トレースと再コンパイルが走ります。`jax.jit`の内側に収めるには、ボンド次元の上限を固定し、切り捨てた部分を0で埋めた配列として扱うことになります。この場合、コンパイルは一度で済みますが、上限までの余分な計算が残ります。

`torch.compile`では、ボンド次元が一度変わった時点で、その次元を記号的な形状として再コンパイルし、以降はそのコードを使い回します。切り捨てる個数を`.item()`などで取り出す部分は、既定ではgraph breakになります。

TVMでは、ボンド次元を記号として持ったまま、1つの実行ファイルで異なるボンド次元を処理できます。ただし、そのカーネルはMetaScheduleでは探索できないので、DLightの規則によるスケジュールか、手で書いたスケジュールを使います。テンソルネットワークの縮約では多くの場合、縮約する添字そのものがボンド次元です。その長さが記号のままだと、cuBLASへ委譲する条件を満たしません。

IREEの指針でいえば、ボンド次元は縮約する行列の行や列の長さそのものなので、内側の次元にあたります。

Tritonで縮約のカーネルを書く場合は、ボンド次元が変わっても、Tritonの節で見た分類（1であること、16の倍数であることなど）が変わらなければ再コンパイルしません。`triton.autotune`の`key`にボンド次元を入れると、新しい値が来るたびに設定の比較が走ります。

### 対称性があると、ブロックの数と大きさがデータで決まる

保存量に対応する対称性を持つテンソルでは、[U(1)対称性を組み込む手法](https://arxiv.org/abs/1008.4774)のように、保存量の値ごとのブロックだけを持ち、ブロックどうしの縮約として計算します。ブロックの数と大きさは、状態とボンド次元の切り捨てによって変わります。

1回の縮約が、形状の異なる多数の小さな行列積に分かれるので、形状ごとに特殊化する方式では、ブロックの形状の種類だけコンパイルが必要になります。記号的な形状を使えばコンパイルは減らせますが、どのブロックどうしを縮約するかという対応自体はデータなので、それを回すループはコンパイラの外のPythonやランタイム側に残ります。

### 反復の中にQRやSVDが入る

グラフを扱う4つの技術のどれも、SVDやQRを自前のカーネルとして生成しません。JAXはLAPACKとcuSOLVERを、`torch.compile`はATenの実装を呼び、TVMでは外部の函数として登録します。IREEのLinalgExtには対応する演算がありません。コンパイラが最適化できるのは、分解と分解の間にある縮約や転置の部分です。

### 既成のライブラリを呼ぶ構成と比べる

テンソルコンパイラを使わず、形状を実行時の引数として受け取る既成のライブラリを呼ぶ構成もあります。CPUの縮約には[TBLIS](https://github.com/MatthewsResearchGroup/tblis/wiki)、行列積や分解には[LAPACK](https://netlib.org/lapack/)などのBLAS/LAPACK実装があります。NVIDIAのGPUでは、縮約に[cuTENSOR](https://docs.nvidia.com/cuda/cutensor/latest/just_in_time_compilation.html)（JITを無効にして既成のカーネルを使えます）、分解に[cuSOLVER](https://docs.nvidia.com/cuda/cusolver/)を使えます。[cuTensorNet](https://docs.nvidia.com/cuda/cuquantum/latest/cutensornet/overview.html)は、縮約順序の探索、メモリ制約に応じたスライシング、QR・SVDを使う分解をまとめて提供します。対称性まで含めて扱うライブラリには、[TensorKit.jl](https://quantumkithub.github.io/TensorKit.jl/latest/)などがあります。

これらは形状ごとのコンパイルを必要としないので、形状が頻繁に変わる計算では比較の基準になります。テンソルコンパイラを使う価値があるのは、ライブラリの呼び出しの間にある転置や要素ごとの演算を融合したい場合や、同じ形状の縮約を十分な回数繰り返し、特殊化の費用を回収できる場合です。

### 使い分け

ボンド次元を上限で固定し、同じ形状の縮約を何度も繰り返す計算では、JAXや`torch.compile`の特殊化が効きます。自動微分を組み合わせたい場合はJAXが候補になります。

ボンド次元が変わり続ける計算では、既成のライブラリを呼ぶ構成を基準にします。コンパイラを使うなら、記号的な形状でコードを使い回せる`torch.compile`のautomatic dynamicやTVMが候補です。ただし、その場合は自動チューニングやcuBLASへの委譲を使えないことがあります。

特定の縮約と、その前後の要素ごとの演算がボトルネックになっている場合は、Tritonでその部分だけ融合したカーネルを書く方法があります。
