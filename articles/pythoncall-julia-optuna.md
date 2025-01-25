---
title: "JuliaでOptunaを使う"
emoji: "👾"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["python", "julia", "optuna"]
published: false
---

## はじめに

JuliaでOptunaを使う方法について紹介します．

同様の試みは
<https://myenigma.hatenablog.com/entry/2019/01/29/204714>
にありますが，こちらで紹介されている方法はPythonからJuliaを起動して値を受け取るような方法のため，値を取得するたびにJuliaを起動し直す余分な時間が発生します．

今回はPythonCall.jlを使って繰り返しJuliaを起動することなく，JuliaでOptunaを使う方法を紹介します．

PythonCall.jlはJuliaからPythonの函数などを呼び出すためのパッケージで，Optuna以外にも使用可能です．
本記事はPythonCall.jlの使用例の一つとして読むこともできます．

Pythonのパッケージ管理にはuvを使用していますが，PythonCall.jlに任せることもできます．

なお，各種ツールのインストールに関する説明は省略します．
以下で説明するコードを実行するにはJuliaとuvがインストールされている必要があります．
uvを使用しない場合は別途Pythonもインストールする必要があります．

## 使用環境

macOS 15.2
Mac mini (2023), Apple M2
Julia 1.11.3
Python 3.11.3
PythonCall.jl 0.9.24
Optuna 4.2.0

## 問題設定

前述の記事と同じ問題をOptunaで解いてみます．
問題としては以下の2変数函数のHimmelblau函数を最小化する問題です（$x,y \in \mathbb{R}$）．

$$ f(x, y) = (x^2 + y - 11)^2 + (x + y^2 - 7)^2 $$

最小値は4箇所で0になります．
詳細はWikipediaの記事などを参照してください．

## 実行準備

まず以下のように作業ディレクトリを作成します．
プロジェクト名は`optuna-jl`とします．

```shell-session
uv init optuna-jl
cd optuna-jl
```

続いて以下のコマンドを実行することでoptunaを依存関係に追加し，Pythonの仮想環境を用意します．

```shell-session
uv add optuna
uv sync # Pythonの仮想環境を作成
```

コマンド実行後プロジェクトのディレクトリに`.venv`ディレクトリが作成されます．`

## Pythonのコード

比較のためにPythonでのコードを示します．
上述のブログのコードを改変して使用しています．
`optuna.py`というファイル名で保存します．
optunaのコードの説明は他の記事等多数あると思いますので，ここでは割愛します．

```python:optuna.py
"""
https://myenigma.hatenablog.com/entry/2019/01/29/204714
original author: Atsushi Sakai
"""

import optuna


def himmelblau(x, y):
    return (x**2 + y - 11) ** 2 + (x + y**2 - 7) ** 2


def objective(trial):
    x = trial.suggest_float("x", -5, 5)
    y = trial.suggest_float("y", -5, 5)
    return himmelblau(x, y)


def main():
    study = optuna.create_study()
    study.optimize(objective, n_trials=1000)
    print(f"min: {study.best_value} at {study.best_params}")


if __name__ == "__main__":
    main()
```

### 実行

以下のコマンドで実行します．

```shell-session
uv run optuna.py
```

### 実行結果

```shell-session
# (めっちゃいっぱい出る)
[I 2025-01-26 04:33:34,594] Trial 999 finished with value: 0.0758888563447687 and parameters: {'x': 3.6225087377750724, 'y': -1.852452409575476}. Best is trial 787 with value: 0.0012883064501580882.
min: 0.0012883064501580882 at {'x': 3.5841488123848735, 'y': -1.8573979664983822}
```

のような出力が得られます．
最小値として得られたminの値が0に近い値になっていれば正解に近い値が得られています．
atの後に最小値として得られた値を取る$x,y$の値が表示されます．

## Juliaの実行準備

それではJuliaに話を移します．
`optuna-jl`ディレクトリで以下を実行します．

```shell-session
julia --project -e 'using Pkg; Pkg.add("PythonCall")'
```

これでPythonCall.jlがインストールされます．

## Juliaのコード

以下のようにJuliaのコードを作成します．
`optuna.jl`というファイル名で保存します．

```julia:optuna.jl
# 実行時に環境変数を設定しない場合は以下のコメントアウトを外す
# ENV["JULIA_CONDAPKG_BACKEND"] = "Null"

using PythonCall: pyimport

function himmelblau(x, y)
  return (x^2 + y - 11)^2 + (x + y^2 - 7)^2
end

function obejective(trial)
  x = trial.suggest_float("x", -5, 5)
  y = trial.suggest_float("y", -5, 5)
  return himmelblau(x, y)
end

function main()
  optuna = pyimport("optuna")
  study = optuna.create_study()
  study.optimize(obejective, n_trials=1000)
  println("min: $(study.best_value) at $(study.best_params)")
end
main()
```

`import optuna`と書く代わりに`optuna = pyimport("optuna")`と書く以外はPythonのコードとほぼ同じです．
PythonとJulia間のオブジェクトの変換はPythonCall.jlが自動的に行います．
コードの書き方によっては変換がうまくいかない場合がありますが，その場合は`pyconvert`函数を使用して明示的に変換することができます．

### 実行

以下のコマンドで実行します．なお，`--project`オプションはプロジェクトのディレクトリを現在のディレクトリに指定するために使用しています．

```shell-session
env JULIA_CONDAPKG_BACKEND="Null" uv run julia --project optuna.jl
```

`env JULIA_CONDAPKG_BACKEND="Null"`は環境変数の設定をしています．
これはPythonCall.jlのデフォルトのパッケージ管理ツールであるCondaPkg.jlを無効にするために必要です．

---

Juliaではコード中に環境変数を設定することができます．
上記コードの先頭にあるコメントアウトを外すことで環境変数を設定することができます．
この場合，実行コマンドは

```shell-session
uv run julia --project optuna.jl
```

となります．

#### uvを使用しない場合

また，環境変数に関する設定を消去してデフォルトのCondaPkg.jlを使用することもできます．
その場合はconda用のPythonパッケージに関する設定を記述する`CondaPkg.toml`ファイルを作成する必要があります．

実行コマンドは

```shell-session
julia --project optuna.jl
```

となります．

### 実行結果

Pythonのコードと同様の結果が得られれば成功です．
実行に時間がかかりすぎる場合は評価の回数を制御する`n_trials`の値を小さくしてください．
なお，Himmelblau函数の最小値0を取る場所は4箇所あるためPythonの場合と同じ場所になるとは限りません．
また，乱数を使用するため，Python版，Julia版ともに実行するたびに得られる最小値の位置が異なることがあります．
