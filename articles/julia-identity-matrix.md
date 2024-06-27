---
title: "Juliaでの単位行列の作り方"
emoji: "👾"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [julia, 線形代数]
published: true
---

Numpyの`eye`などに慣れていると面食らうかもしれませんが，Juliaでは`eye`は定義されておらず^[Julia 0.7で非推奨となり，Julia 1.0で取り除かれました．]，単位行列を作るには標準library`LinearAlgebra`の`I`を用います．

:::message
以下の話を実行するために，まずは

```julia:
using LinearAlgebra
```

が必要です．
:::

## 簡単なやり方

一番簡単な書き方は

```julia
n = 4
1.0I(n)
```

で，要素が`Float64`型の`n`$\times$`n`単位行列となります．
厳密には`n`$\times$`n` `Diagonal{Float64, Vector{Float64}}`型です．
以下同様に`n`は非負整数とします^[`n`が`0`の場合もerrorとはならず要素数0の配列が定義されます．]．

要素を整数型(`Int64`)にしたければ

```julia
1I(n)
```

です．

また，複素数型(`ComplexF64`)にしたければ

```julia
(1.0+0.0im)I(n)
```

です．

なお，

```julia:
I(n)
```

にした場合は要素は真偽型となり，対角要素が`true`，非対角要素が`false`になります．

以上の書き方はJulia 1.2以降で有効です．
それ以前のversionを使っている場合は以下で紹介する方法を使ってください．

## 他のやり方

これ以外の型を指定したい場合，例えば`Float32`型の単位行列を作りたい場合は

```julia:
Matrix{Float32}(I, n, n)
```

を使うと良いです．
前述の方法では`Matrix`型ではなく`Diagonal`型となるため，`Matrix`型でなければ都合が悪い場合もこちらを使います．

また`I`の他の使い方として`A`を`Matrix`, `a`を数値型として

```julia:
A + a * I
```

という書き方でAの対角要素のみに`a`を加算するというような対角shiftを書くことができます．

## 実装など細かい話

`I`は`LinearAlgebra.UniformScaling`という単位行列(の定数倍)を表現する構造体によって以下のように定義されています．

```julia:
struct UniformScaling{T<:Number}
    λ::T
end
```

```julia:
const I = UniformScaling(true)
```

ここで，`λ`は単位行列の定数倍を表すための定数$\lambda$で，$I$を単位行列として$\lambda I$を表現しています．
単位行列の定数倍を表すのに愚直に密行列を用いると$n^2$の要素数を必要としますが，実際は次元と定数のみが必要であることからこのようになっています．

`Array`と`UniformScaling`との`+`のような2項演算などが定義されており，`A + a * I`のような書き方が可能になっています．
`+`の他に`A - a * I`なども使えます．
他にどのような演算などが定義されているかは[uniformscaling.jlのsource code](https://github.com/JuliaLang/julia/blob/master/stdlib/LinearAlgebra/src/uniformscaling.jl)
から確認することができます．

## 参考文献

https://docs.julialang.org/en/v1/stdlib/LinearAlgebra/#LinearAlgebra.UniformScaling-Tuple{Integer}

https://discourse.julialang.org/t/why-eye-has-been-deprecated/12824
