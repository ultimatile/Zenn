---
title: "Juliaのmetaprogrammingはmemory leakする?"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["julia"]
published: false
---


# 終わりに

この問題に関連するissueやdiscourseの投稿を見るとcore開発者の方達はこの問題は認識しているようですが解決する見込みはないようです.
https://github.com/JuliaLang/julia/issues/14495
https://discourse.julialang.org/t/is-mem-of-compiled-evaled-functions-garbage-collected/2231