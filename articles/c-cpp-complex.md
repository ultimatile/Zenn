---
title: "C/C++複素数ライブラリの相互運用性とコンパイラ間実装差異の検証"
emoji: "🔢"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["c", "cpp"]
published: false
---

# はじめに

C/C++における複素数の扱いは、言語の仕様と実装により複数の形態が存在します。本記事では、これらの複素数型の互換性とライブラリ間での露出の違いについて検証し、実用的な使い分けについて述べます。

## 複素数型の分類

C/C++で利用可能な複素数型は以下の3種類に分類されます：

### 1. 組み込み複素数型(`_Complex`)

ISO C99で標準化された`_Complex`型はヘッダファイルのインクルードなしで利用可能です。
標準で定義されているのは`float _Complex`, `double _Complex`, `long double _Complex`です。
なお、`int _Complex`等の整数型複素数はISO標準外ですが、GCC/Clang両方でサポートされています^[ただし、typedefを用いて定義されている、`int8_t`などの`<stdint.h>`の整数型に関しては、`_Complex`がtypedefで定義された型と組み合わせられないため使用できません。]。

### 2. ISO C99 complex.h

`<complex.h>`をインクルードすることで利用可能になる標準的なC99複素数API。
`complex`型と虚数単位`I`、および`crealf()`, `cimagf()`等のアクセス関数を提供します。

### 3. ISO C++ std::complex

`<complex>`をincludeして使用する標準C++の複素数クラステンプレート。
C++14以降では虚数単位`i`リテラルも利用可能です（`using namespace std::complex_literals;`が必要）。

## 型変換規則

ISO C99では以下の型変換規則が定義されています：

- 異なる複素数型間の型変換が発生した場合、対応する実数型の型変換規則に従います。
- 実数型を複素数型に変換する場合は、変換される実数型の値を実部に持ち、虚部が0の複素数型になります。
- 複素数型を実数型に変換する場合は、虚部は無視され、実部を値として持つ対応する実数型に変換されます。

## 本記事の検証内容

以下では、これらの複素数型のコンパイラ・標準ライブラリ間での相互運用性と、実装依存の拡張機能について詳細に検証します。ここで`value_type`は具体的な型を指します。

| 言語  | include       | type                       | 虚数単位    | 実部         | 虚部         | 備考        |
| ----- | ------------- | -------------------------- | ----------- | ------------ | ------------ | ----------- |
| C/C++ | なし          | `value_type _Complex`      | -           | `__real__ c` | `__imag__ c` | 組み込み    |
| C     | `<complex.h>` | `value_type complex`       | `I`         | `creal(c)`   | `cimag(c)`   | ISO C99標準 |
| C++   | `<complex>`   | `std::complex<value_type>` | `i`(C++14~) | `c.real()`   | `c.imag()`   | ISO C++標準 |

## 検証結果とライブラリ間の差異

### 検証環境

- **GCC**: g++-15 (Homebrew GCC 15.1.0) + libstdc++
- **Clang**: Apple clang version 17.0.0 + libc++
- **プラットフォーム**: macOS (Darwin 24.6.0)

### 検証結果サマリー

| サンプルコード                   | GCC + libstdc++ | Clang + libc++ | 説明                              |
| -------------------------------- | --------------- | -------------- | --------------------------------- |
| `01_gnu_extension_ctor.cpp`      | ✅ 成功         | ❌ 失敗        | `_Complex` → `std::complex` 変換  |
| `02_crealf_no_header.cpp`        | ❌ 失敗         | ❌ 失敗        | `<complex.h>` なしでの`crealf`    |
| `03a_crealf_with_header_gcc.cpp` | ✅ 成功         | -              | `<complex.h>` での C99 API        |
| `03b_portable_clang.cpp`         | ✅ 成功         | ✅ 成功        | GNU拡張 `__real__`, `__imag__`    |
| `04_integer_complex.c`           | ✅ 成功         | ✅ 成功        | 整数型`_Complex`（GCC/Clang共通） |
| `07_integer_complex.cpp`         | ✅ 成功         | ✅ 成功        | C++での整数型`_Complex`           |

### ライブラリ実装の違い

#### 1. GNU拡張コンストラクタ (libstdc++ vs libc++)

**libstdc++ (GCC)**では、`std::complex<T>`に`_Complex T`型を受け取るコンストラクタが**GNU拡張として実装されている**：

```cpp
// GNU拡張コンストラクタのデモ（libstdc++のみ）
#include <iostream>
#include <complex>
#include <complex.h>

int main() {
    // _Complex型からstd::complexへの変換
    _Complex double z = 3.0 + 4.0 * I;

    std::cout << "Original _Complex: "
              << __real__(z) << " + " << __imag__(z) << "i" << std::endl;

    // GNU拡張コンストラクタ（libstdc++のみで成功）
    std::complex<double> sc(z);

    std::cout << "Converted std::complex: "
              << sc.real() << " + " << sc.imag() << "i" << std::endl;

    // 演算例
    std::complex<double> sc2(1.0, 2.0);
    auto result = sc + sc2;

    std::cout << "Addition result: "
              << result.real() << " + " << result.imag() << "i" << std::endl;

    return 0;
}

/* 出力例（GCC + libstdc++）:
Original _Complex: 3 + 4i
Converted std::complex: 3 + 4i
Addition result: 4 + 6i
*/
```

**libc++ (Clang)**では、このGNU拡張コンストラクタは**実装されていない**ため、以下のエラーが発生：

```
error: implicit conversion from '_Complex double' to 'double' is not permitted in C++
```

#### 2. C99 complex.h API の露出

**どちらの標準ライブラリでも**、`<complex.h>`をincludeしない限り`crealf()`, `cimagf()`等のC99 complex APIは利用できない：

```cpp
// ❌ どちらも失敗
float r = crealf(z);  // error: 'crealf' was not declared
```

`<complex.h>`をincludeした場合のみ利用可能：

```cpp
#include <complex.h>
// ✅ 成功
float r = crealf(z);
```

**注意**: Apple SDKでは、C++翻訳単位において`<complex.h>`をincludeしても`I`や`crealf`が公開されない実装が存在します。

#### 3. 非ISO拡張での実部・虚部アクセス

**コンパイラbuilt-in演算子（GCC/Clang共通サポート）**：

```cpp
// ポータブルなコンパイラbuilt-in演算子のデモ
#include <iostream>

int main() {
    // コンパイラbuilt-in演算子を使用
    _Complex float z;
    __real__(z) = 1.0f;  // ✅ コンパイラbuilt-in
    __imag__(z) = 2.0f;  // ✅ コンパイラbuilt-in

    std::cout << "Built-in access: "
              << __real__(z) << " + " << __imag__(z) << "i" << std::endl;

    // 基本演算
    _Complex float z2 = 3.0f + 4.0f * (__extension__ 1.0iF);
    _Complex float sum = z + z2;

    std::cout << "Addition: (" << __real__(z) << "+" << __imag__(z) << "i) + ("
              << __real__(z2) << "+" << __imag__(z2) << "i) = "
              << __real__(sum) << "+" << __imag__(sum) << "i" << std::endl;

    // サイズ情報
    std::cout << "sizeof(_Complex float): " << sizeof(_Complex float) << std::endl;

    return 0;
}

/* 出力例（GCC/Clang共通）:
Built-in access: 1 + 2i
Addition: (1+2i) + (3+4i) = 4+6i
sizeof(_Complex float): 8
*/
```

**注意**: `__real__`と`__imag__`は非ISO拡張であり、標準ライブラリではなくコンパイラレベルで実装されています。使用時は`-std=gnu++`（拡張有効）を推奨します。ISOモードでは警告が出る可能性があります。

#### 4. 整数型複素数の実装詳細

**GCC/Clang共通の特徴**:

```cpp
// 整数型複素数のデモ（GCC/Clang共通）
#include <iostream>
#include <complex>

int main() {
    // 整数型複素数の宣言と初期化
    int _Complex z_int;
    __real__(z_int) = 42;
    __imag__(z_int) = 24;

    // 異なる整数型での例
    char _Complex z_char;
    __real__(z_char) = 'A';  // 65
    __imag__(z_char) = 'B';  // 66

    unsigned int _Complex z_uint = 100 + 200 * (__extension__ 1.0iF);

    std::cout << "int _Complex: "
              << (int)__real__(z_int) << " + " << (int)__imag__(z_int) << "i" << std::endl;

    std::cout << "char _Complex: "
              << (int)__real__(z_char) << " + " << (int)__imag__(z_char) << "i" << std::endl;

    // std::complex<int>との比較
    std::complex<int> std_z(42, 24);
    std::cout << "std::complex<int>: "
              << std_z.real() << " + " << std_z.imag() << "i" << std::endl;

    // メモリサイズ比較
    std::cout << "sizeof(int _Complex): " << sizeof(int _Complex) << std::endl;
    std::cout << "sizeof(std::complex<int>): " << sizeof(std::complex<int>) << std::endl;

    // 基本演算
    int _Complex a = 1 + 2 * (__extension__ 1.0iF);
    int _Complex b = 3 + 4 * (__extension__ 1.0iF);
    int _Complex sum = a + b;

    std::cout << "Integer addition: ("
              << (int)__real__(a) << "+" << (int)__imag__(a) << "i) + ("
              << (int)__real__(b) << "+" << (int)__imag__(b) << "i) = "
              << (int)__real__(sum) << "+" << (int)__imag__(sum) << "i" << std::endl;

    return 0;
}

/* 出力例（GCC/Clang共通）:
int _Complex: 42 + 24i
char _Complex: 65 + 66i
std::complex<int>: 42 + 24i
sizeof(int _Complex): 8
sizeof(std::complex<int>): 8
Integer addition: (1+2i) + (3+4i) = 4+6i
*/
```

**実用例**:

```c
// 離散フーリエ変換での整数座標
int _Complex position;
__real__(position) = x_coord;
__imag__(position) = y_coord;

// ビット演算との組み合わせ
unsigned int _Complex pixel = rgb_value + alpha_value * (__extension__ 1.0iF);
```

### ポータビリティ戦略の選択

複素数の扱いにおいて、ポータビリティのレベルに応じて以下の戦略から選択できます：

#### 戦略A: 完全ポータブル（ISO標準準拠）

**C言語:**

```c
// C99 complex.h APIのデモ
#include <stdio.h>
#include <complex.h>
#include <math.h>

int main() {
    // C99標準の複素数
    float complex z1 = 1.0f + 2.0f * I;
    double complex z2 = 3.0 + 4.0 * I;

    printf("float complex: %.2f + %.2fi\n", crealf(z1), cimagf(z1));
    printf("double complex: %.2f + %.2fi\n", creal(z2), cimag(z2));

    // 基本演算
    float complex sum = z1 + (float complex)(1.0f + 1.0f * I);
    printf("Addition: %.2f + %.2fi\n", crealf(sum), cimagf(sum));

    // 数学関数
    float magnitude = cabsf(z1);
    float phase = cargf(z1);

    printf("Magnitude: %.4f\n", magnitude);
    printf("Phase: %.4f radians\n", phase);

    // 指数関数と共役複素数
    float complex exp_z = cexpf(z1);
    float complex conj_z = conjf(z1);

    printf("exp(%.2f + %.2fi) = %.4f + %.4fi\n",
           crealf(z1), cimagf(z1), crealf(exp_z), cimagf(exp_z));
    printf("conjugate: %.2f + %.2fi\n", crealf(conj_z), cimagf(conj_z));

    return 0;
}

/* 出力例:
float complex: 1.00 + 2.00i
double complex: 3.00 + 4.00i
Addition: 2.00 + 3.00i
Magnitude: 2.2361
Phase: 1.1071 radians
exp(1.00 + 2.00i) = -1.1312 + 2.4717i
conjugate: 1.00 + -2.00i
*/
```

**C++:**

```cpp
// 完全ポータブルな標準C++複素数
#include <iostream>
#include <complex>

int main() {
    // ISO標準C++の複素数
    std::complex<float> z1(1.0f, 2.0f);
    std::complex<double> z2(3.0, 4.0);

    std::cout << "std::complex<float>: "
              << z1.real() << " + " << z1.imag() << "i" << std::endl;

    // C++14 虚数リテラル
    using namespace std::complex_literals;
    auto z3 = 1.0f + 2.0if;

    std::cout << "C++14 literal: "
              << z3.real() << " + " << z3.imag() << "i" << std::endl;

    // 基本演算と数学関数
    auto sum = z1 + z3;
    auto magnitude = std::abs(z1);
    auto phase = std::arg(z1);

    std::cout << "Addition: " << sum.real() << " + " << sum.imag() << "i" << std::endl;
    std::cout << "Magnitude: " << magnitude << std::endl;
    std::cout << "Phase: " << phase << " radians" << std::endl;

    return 0;
}

/* 出力例:
std::complex<float>: 1 + 2i
C++14 literal: 1 + 2i
Addition: 2 + 4i
Magnitude: 2.23607
Phase: 1.10715 radians
*/
```

- ✅ 最高のポータビリティ
- ✅ 標準準拠
- ❌ C99の`<complex.h>`が必要

#### 戦略B: コンパイラbuilt-in依存

```cpp
_Complex float z;
__real__(z) = 1.0f;  // コンパイラbuilt-in
__imag__(z) = 2.0f;  // コンパイラbuilt-in
```

- ✅ `<complex.h>`不要
- ✅ GCC/Clang両対応
- ❌ 非ISO拡張（標準ではない）

#### 戦略C: libstdc++特化

```cpp
#include <complex>
#include <complex.h>
_Complex double z = 3.0 + 4.0 * I;
std::complex<double> sc(z);  // libstdc++のGNU拡張
```

- ✅ C/C++混在コードで便利
- ❌ libstdc++専用（libc++不可）
- ❌ 移植性が限定的

### 推奨アプローチ

**新規コードでの推奨順序:**

1. **ISO標準準拠**: `<complex.h>` + `crealf()`/`cimagf()` (C) または `std::complex` (C++)
2. **コンパイラbuilt-in**: `__real__`/`__imag__` (GCC/Clang)
3. **libstdc++限定**: `_Complex` → `std::complex`変換

## Linux環境での検証結果

glibc vs musl、および標準ライブラリの組み合わせによる複素数モジュール露出の違いを検証しました。

### Ubuntu 24.04 (glibc 2.39) での結果

**GCC 13.3.0 + libstdc++:**

- ✅ `01_gnu_extension_ctor.cpp`: 成功
- ❌ `02_crealf_no_header.cpp`: `crealf`未宣言で失敗
- ✅ `03a_crealf_with_header_gcc.cpp`: 成功

**Clang 18.1.3 + libstdc++:**

- ✅ `01_gnu_extension_ctor.cpp`: **成功** (libstdc++のGNU拡張)
- ❌ `02_crealf_no_header.cpp`: `crealf`未宣言で失敗
- ✅ `03b_portable_clang.cpp`: 成功

**Clang 18.1.3 + libc++:**

- ❌ `01_gnu_extension_ctor.cpp`: **失敗** (`_Complex` → `std::complex`変換不可)
- ❌ `02_crealf_no_header.cpp`: `crealf`未宣言で失敗
- ✅ `03b_portable_clang.cpp`: 成功

### Alpine 3.22 (musl 1.2.5) での結果

**GCC 14.2.0 + libstdc++:**

- ✅ `01_gnu_extension_ctor.cpp`: **成功** (出力: 3.0 4.0)
- ❌ `02_crealf_no_header.cpp`: `crealf`未宣言で失敗
- ✅ `03a_crealf_with_header_gcc.cpp`: **成功** (出力: 1.0 2.0)

**Clang 20.1.8 + libstdc++:**

- ✅ `01_gnu_extension_ctor.cpp`: **成功** (libstdc++のGNU拡張)
- ❌ `02_crealf_no_header.cpp`: `crealf`未宣言で失敗
- ✅ `03b_portable_clang.cpp`: 成功

**Clang 20.1.8 + libc++:**

- ❌ `01_gnu_extension_ctor.cpp`: **失敗** (`_Complex` → `std::complex`変換不可)
- ❌ `02_crealf_no_header.cpp`: `crealf`未宣言で失敗
- ✅ `03b_portable_clang.cpp`: 成功 (要libunwind)

### 重要な発見

#### 1. 標準ライブラリによる機能差

**libstdc++**: `_Complex` → `std::complex`のGNU拡張コンストラクタあり
**libc++**: このGNU拡張コンストラクタなし

検証結果:

- **GCC + libstdc++**: 全環境で`_Complex` → `std::complex`変換可能
- **Clang + libstdc++**: 全環境で`_Complex` → `std::complex`変換可能
- **Clang + libc++**: 全環境で`_Complex` → `std::complex`変換**不可**

#### 2. libstdc++のGNU拡張は環境間で一貫

**重要な発見**: libstdc++のGNU拡張コンストラクタ（`_Complex` → `std::complex`変換）は、**libstdc++を使用する全ての環境で利用可能**です：

- macOS: GCC + libstdc++
- Linux glibc: GCC + libstdc++, Clang + libstdc++
- Linux musl: GCC + libstdc++, Clang + libstdc++

この機能はlibstdc++固有の実装であり、libc++では利用できません。

#### 3. コンパイラbuilt-inは標準ライブラリ非依存

**`__real__`/`__imag__`** はコンパイラレベルのbuilt-in演算子のため、標準ライブラリの種類（libstdc++/libc++/musl）に依存せず、GCC/Clang両方で利用可能です。

### 環境別複素数機能対応表

| 環境        | コンパイラ | 標準ライブラリ | `_Complex`→`std::complex` | `__real__`/`__imag__` | ISO `<complex.h>`          | 整数型`_Complex` |
| ----------- | ---------- | -------------- | ------------------------- | --------------------- | -------------------------- | ---------------- |
| macOS       | Clang      | libc++         | ❌                        | ✅ (built-in)         | ⚠ (C++では非公開実装あり) | ✅ (GNU拡張)     |
| macOS       | GCC        | libstdc++      | ✅ (libstdc++)            | ✅ (built-in)         | ✅                         | ✅ (GNU拡張)     |
| Linux glibc | GCC        | libstdc++      | ✅ (libstdc++)            | ✅ (built-in)         | ✅                         | ✅ (GNU拡張)     |
| Linux glibc | Clang      | libstdc++      | ✅ (libstdc++)            | ✅ (built-in)         | ✅                         | ✅ (GNU拡張)     |
| Linux glibc | Clang      | libc++         | ❌                        | ✅ (built-in)         | ✅                         | ✅ (GNU拡張)     |
| Linux musl  | GCC        | libstdc++      | ✅ (libstdc++)            | ✅ (built-in)         | ✅                         | ✅ (GNU拡張)     |
| Linux musl  | Clang      | libstdc++      | ✅ (libstdc++)            | ✅ (built-in)         | ✅                         | ✅ (GNU拡張)     |
| Linux musl  | Clang      | libc++         | ❌                        | ✅ (built-in)         | ✅                         | ✅ (GNU拡張)     |

### 用途別推奨戦略

| 用途                   | 推奨戦略                                | 理由             |
| ---------------------- | --------------------------------------- | ---------------- |
| **最大ポータビリティ** | ISO標準 (`<complex.h>`, `std::complex`) | 全環境で動作     |
| **GCC/Clang環境**      | `__real__`/`__imag__`                   | ヘッダ不要、高速 |
| **libstdc++限定**      | `_Complex` → `std::complex`             | C/C++混在で便利  |

## 参考文献

<http://nalab.mind.meiji.ac.jp/~mk/labo/text/complex-c.pdf>
<https://cpprefjp.github.io/reference/complex/complex.html>
