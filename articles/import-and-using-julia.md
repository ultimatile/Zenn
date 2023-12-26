---
title: "Juliaのmodule/package間の名前の衝突の回避"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [julia]
published: false
---

##　はじめに
Juliaでpackageを用いる場合, 通常は`using`で読み込みます.
これは`using`で読み込まれたものを現在の名前空間に加えてしまうため^[名前空間が], 

## はじめに
Juliaで外部moduleにあるものを使う場合に`import`と`using`で読み込みます.

[公式document](https://docs.julialang.org/en/v1/manual/modules/)に全て書いてあると思いますが, できるだけ短く要点をまとめたい.

## `using`と`export`
`using`は`export`されたものを読み込みます.

具体例として次のような`module`を考えます.

```julia:REPL
julia> module Mymodule
       export value1
       value1 = 1
       value2 = 2
       end
Main.Mymodule
```

このとき, `using .Mymodule`をすると`export`された`value1`は読み込まれますが, `export`されていない`value2`は読み込まれません.

```julia:REPL
julia> using .Mymodule
julia> println(value1)
1
julia> println(value2)
ERROR: UndefVarError: value2 not defined
```

:::message
`using`では`export`されてないものは使えない.
:::

したがって, `export`されたものは`public/private`で言うところの`public`に相当します.

通常, `export`されてないものは`module`の利用者が使うものではなく, `module`内部でのみ使うことが意図されています.

しかし, `export`されてないものを`module`外部から使いたい場合があります.

そのときは`import`を使います.

## `import`による`export`されていないものの読み込み
上述の例から`value2`を読み込みたいとします.

以下の様にすると`value2`を読み込むことができます.

```julia:REPL
julia> import .Mymodule: value2
julia> println(value2)
2
```

あるいは

```julia:REPL
julia> import .Mymodule
julia> println(Mymodule.value2)
2
```

としても同じ結果が得られます.

それでは, どちらを使えば良いでしょうか?

最初のやり方の方が短い名前で呼び出せます.

しかし, どの`module`から`value2`が来たのか分かりません.

また, 他の`module`に`value2`が存在する場合, 名前が衝突します.

後者の問題について以下の具体例で確認します.
```julia:REPL
julia> module Mymodule1
       value = 1
       end
Main.Mymodule1
julia> import .Mymodule1: value
julia> module Mymodule2
       value = 2
       end
Main.Mymodule2
julia> import .Mymodule2: value
WARNING: ignoring conflicting import of Mymodule2.value into Main
julia> println(value)
1
```
`value`という変数を持つ2つの`module`を読み込むと名前が衝突し, 後から読み込んだ`import .Mymodule2: value`が無視されました.

したがって`value`の値は`Mymodule1`のものとなります.

名前の衝突は`using`でも起こります.

特に`using`では読み込まれるものがその場で分からないため, `import`より名前が衝突しやすいです.

以下では`import`を使って名前の衝突を回避する方法について述べます.

## `import`による名前の衝突の回避
### 回避方法1: `import module名`を使う
`import module名`で読み込むとその`module`内のものには`module名.要素名`でaccessすることになります.
したがって, 異なる`module`に同じ名前の要素があっても異なる名前でaccessができます.

```julia:REPL
julia> module Mymodule1
       value = 1
       end
Main.Mymodule1
julia> module Mymodule2
       value = 2
       end
Main.Mymodule2
julia> import .Mymodule1
julia> import .Mymodule2
julia> println(Mymodule1.value)
1
julia> println(Mymodule2.value)
2
```

```julia:REPL
```

## 参考文献
https://docs.julialang.org/en/v1/manual/modules/
https://qiita.com/cometscome_phys/items/5c98aef4c10a8a575f81