---
title: "C++でC言語の複素数とC++の複素数を混ぜよう!!"
emoji: "🤪"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["c","cpp"]
published: false
---

# はじめに
皆さん複素数は使いますよね(迫真).
C++では`std::<complex>`をincludeすることで複素数を使うことができます.
Cでは`complex.h`をincludeして使える複素数と`complex.h`をincludeせずに使える複素数があるようです.
C++でCの複素数^[複素数体$\mathbb{C}$とC言語のCが紛らわしい感じがしますが本記事でCと言ったら常にC言語を指します.]を使う場合は`complex.h`をincludeしないといけません.
これらの複素数の型は同じではありませんが整合性はあるように設計されてはいるようです.
これらの間で四則演算しようものなら暗黙の型変換が発生してClangパイセンにブチギレられます.
`complex.h`をincludeして使えるようになる複素数の使い方がCとC++の互換性が微妙にないので記法を最初に整理してお互いの明示的な型変換について述べます.

以下では, C++においてincludeなしで使える複素数型をheaderless complexと呼ぶことにします.
Cの`<complex.h>`で定義される複素数型はC++では使えないのでこれ以上触れません.
このような事情があるので複素数型の変数をCの函数としてexternするには必然的にheaderless complexを用いる必要があります
C++で複素数型を
ISO C99で定義されているのは`float _Complex`, `double _Complex`, `long double _Complex`.
ISO C99では`int _Complex`等の整数型は定義されていないがGCCではサポートされている

- 異なる複素数型間の型変換が発生した場合, 対応する実数型の型変換規則に従う^[ISO C99でcorresponding real typeという用語が使われているので, 本記事でも対応する実数型と呼びます.].
e.g., `float _Complex + double _Complex = double _Complex`
- 実数型を複素数型に変換する場合は変換される実数型の値を実部に持ち,虚部が0の対応する複素数型になる.
e.g., `float a`→`float _Complex (a,0)`
- 複素数型を実数型に変換する場合は虚部は無視され, 実部を値として持つ対応する実数型に変換される.
e.g.,`float _Complex (a,b)`→`float a`

|言語|include|type|虚数単位|実部|虚部|
|---|---|---|---|---|---|
|C/C++|なし|`value_type _Complex`|`i`|`__real__ c`|`__imag__ c`|
|C|`<complex.h>`|`value_type complex`|`I`|`creal(c)`| `cimag(c)`|
|C++|`<complex>`|`std::complex<value_type>`|`i`(C++14~)|`c.real()`|`c.imag()`|

http://nalab.mind.meiji.ac.jp/~mk/labo/text/complex-c.pdf
https://cpprefjp.github.io/reference/complex/complex.html

