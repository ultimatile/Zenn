---
title: "C++でゼロ除算"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["cpp"]
published: false
---

https://rsk0315.hatenablog.com/entry/2019/09/10/213859
に未定義動作について

>コンパイラが以下のような動作をすることが仕様で許されているというのがあります．
>- 未定義動作は起こらないと仮定してよい
>- 起こらないのだから，無視して最適化してよい

と書いてあります.
**ゼロ除算も配列境界外参照も起きるだろ💢**

| コンパイラ | 整数でのゼロ除算 |
| --- | --- |
| `g++` | `-Wdiv-by-zero` |
| `clang++` | `-Wdiv-by-zero` or `-Wdivision-by-zero`|
| `icpc` | `-div-by-zero` |

```:terminal
% g++-12 -v --help 2>/dev/null| grep -e "-Wdiv-by-zero" 
  -Wdiv-by-zero               Warn about compile-time integer division by zero.
```

```:terminal
% g++-12 zero-div.cpp 
% ./a.out 
zsh: floating point exception  ./a.out
```

# 整数の定数除算の確認
## Warningあり
### gcc
```:terminal
% g++-12 -Wdiv-by-zero zero-div.cpp
zero-div.cpp: In function 'int main()':
zero-div.cpp:2:10: warning: division by zero [-Wdiv-by-zero]
2 |         1/0;
  |         ~^~
```
### clang
```:terminal
% clang++ zero-div.cpp
zero-div.cpp:3:16: warning: division by zero is undefined [-Wdivision-by-zero]
        std::cout << 1/0 << std::endl; 
                      ^~
1 warning generated. 
```
    - icpc
  - Warningなし
    - gcc
    - clang
    - icpc
整数の変数除算の確認
  - gcc
  - clang
  - icpc
浮動小数点数の定数除算の確認
  - gcc
  - clang
  - icpc
浮動小数点数の変数除算の確認
  - gcc
  - clang
  - icpc


clang++はdefaultでoptionは有効

# 環境
Intel MacBook Pro (2017)
macOS Catalina 10.15.7

```
g++-12 (Homebrew GCC 12.2.0) 12.2.0
Apple clang version 12.0.0 (clang-1200.0.32.29)
icpc (ICC) 2021.5.0 20211109
```

https://github.com/cplusplus/draft

https://rsk0315.github.io/CXX/ub.html

https://twitter.com/onihusube9

https://stackoverflow.com/questions/42926763/the-behaviour-of-floating-point-division-by-zero