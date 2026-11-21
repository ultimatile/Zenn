---
title: "cuQuantum（cuTensorNet）とNVHPC・cuTENSORのバージョン互換性早見表（随時更新）"
emoji: "🧩"
type: "tech"
topics: ["cuquantum", "nvhpc", "cuda", "gpu"]
published: true
register: almost
---

## これは何

[cuTensorNet](https://docs.nvidia.com/cuda/cuquantum/latest/cutensornet/index.html)は、NVIDIAの量子計算SDKである[cuQuantum](https://developer.nvidia.com/cuquantum-sdk)に含まれるテンソルネットワーク計算ライブラリです。 cuTensorNetは[cuTENSOR](https://developer.nvidia.com/cutensor)に依存しているため、[NVHPC](https://developer.nvidia.com/hpc-sdk)（NVIDIA HPC SDK）と組み合わせて使う場合には、NVHPCに同梱されているcuTENSORのバージョンがcuTensorNetの要求を満たしているかを確認する必要があります。 本記事では、公式ドキュメントに散らばっているバージョン互換性の情報を早見表としてまとめます。

出典は次の2つです。

- cuTensorNetの[リリースノート](https://docs.nvidia.com/cuda/cuquantum/latest/cutensornet/release-notes.html)
- [NVHPCのリリース一覧](https://developer.nvidia.com/hpc-sdk-releases)

## cuQuantum（cuTensorNet）の互換表

表の読み方は次のとおりです。

- CCはGPUのcompute capabilityを指す
- rec.はrecommended（推奨）の略
- N/Aは互換性のあるバージョンが（投稿時点で）存在しないことを意味する
- cuTENSOR列の`1.6.1+`のような表記は同一メジャーバージョン内での下限であり、たとえば`1.6.1+`と書かれていてもv2系とは互換性がないようなので注意

| cuQuantum | cuTensorNet |        CUDA         |    CC[^5]     |          NVHPC           |         cuTENSOR         |
| :-------: | :---------: | :-----------------: | :-----------: | :----------------------: | :----------------------: |
|   26.11   |   2.15.0    |       12, 13        | 7.5<=CC<=12.1 |          26.11+          |          2.8.0+          |
|   26.09   |   2.14.0    |       12, 13        | 7.5<=CC<=12.1 |          26.11+          |          2.8.0+          |
|   26.06   |   2.13.0    |       12, 13        | 7.5<=CC<=12.1 |          26.3+           |   2.5.0+ (2.7.0 rec.)    |
|  26.03.2  |   2.12.2    |       12, 13        | 7.5<=CC<=12.1 |        25.11+[^4]        |          2.3.1+          |
|  26.03.1  |   2.12.1    |       12, 13        | 7.5<=CC<=12.1 |        25.11+[^4]        |          2.3.1+          |
|   26.01   |   2.11.0    |       12, 13        | 7.5<=CC<=12.1 |        25.11+[^4]        |          2.3.1+          |
|   25.11   |   2.10.0    |       12, 13        | 7.5<=CC<=12.1 |        25.11+[^4]        |          2.3.1+          |
|   25.09   |    2.9.0    |       12, 13        | 7.5<=CC<=12.1 |        25.11+[^4]        |          2.3.1+          |
|   25.06   |    2.8.0    |       11, 12        | 7.0<=CC<=12.0 |          25.5+           |          2.2.0+          |
|   25.03   |    2.7.0    |       11, 12        | 7.0<=CC<=12.0 |          25.5+           |          2.2.0+          |
|   24.11   |    2.6.0    |       11, 12        | 7.0<=CC<=9.0  |          24.7+           |          2.0.2+          |
|   24.08   |    2.5.0    |       11, 12        | 7.0<=CC<=9.0  |          24.7+           |          2.0.2+          |
|   24.03   |    2.4.0    |       11, 12        | 7.0<=CC<=9.0  |          24.3+           |          2.0.1+          |
|   23.10   |    2.3.0    |       11, 12        | 7.0<=CC<=9.0  | 22.11+ (23.11+ rec.)[^1] | 1.6.1+ (1.7.0 rec.)[^1]  |
|  23.06.1  |    2.2.1    |       11, 12        | 7.0<=CC<=9.0  | 22.11+ (23.11+ rec.)[^1] | 1.6.1+ (1.7.0 rec.)[^1]  |
|   23.06   |    2.2.0    |       11, 12        | 7.0<=CC<=9.0  | 22.11+ (23.11+ rec.)[^1] | 1.6.1+ (1.7.0 rec.)[^1]  |
|   23.03   |    2.1.0    |       11, 12        | 7.0<=CC<=9.0  | 22.11+ (23.11+ rec.)[^1] | 1.6.1+ (1.7.0 rec.)[^1]  |
|   22.11   |    2.0.0    | 11 (11.8+ rec.)[^2] | 7.0<=CC<=9.0  | 22.11+ (23.1+ rec.)[^3]  | 1.6.1+ (1.6.2+ rec.)[^3] |
|  22.07.1  |    1.1.1    |         11          | 7.0<=CC<=8.7  |          22.3+           |          1.5.0+          |
|   22.07   |    1.1.0    |         11          | 7.0<=CC<=8.7  |          22.3+           |          1.5.0+          |
|   22.05   |    1.0.1    |         11          | 7.0<=CC<=8.7  |          22.3+           |          1.5.0+          |
|   22.03   |    1.0.0    |         11          | 7.0<=CC<=8.7  |          22.3+           |          1.5.0+          |
|   0.1.0   |    0.1.0    |        11.4+        | 7.0<=CC<=8.7  |          21.11+          |          1.4.0+          |
|    N/A    |    0.0.1    |        11.4+        | 7.0<=CC<=8.7  |          21.7+           |          1.3.3+          |

補足として、cuTensorNet 0.xはNVHPCが必須です。必要なNVHPCのバージョンは、v0.0.1なら21.7以上、v0.1.0なら21.11以上です。一方、cuTensorNet 1.0以降はNVHPCなしでも利用できます。

[^1]: パフォーマンス改善・バグ修正・CUDA Lazy Loading対応のためです。

[^2]: Hopper対応とバグ修正のためにCUDA 11.8以上が推奨されています。表のこれより上の行（より新しいバージョン）でも同様と思われます。

[^3]: パフォーマンス改善とバグ修正のためです。

[^4]: CUDA 12・13ともにCC>=7.0が必要です。後述の[nvhpc同梱cutensorバージョン](#nvhpc%E5%90%8C%E6%A2%B1%E3%81%AEcutensor%E3%83%90%E3%83%BC%E3%82%B8%E3%83%A7%E3%83%B3)の表を参照してください。

[^5]: CCの範囲はcuTENSOR由来の制約です。[cuTENSORの対応CC](#cutensorの対応cc)を参照してください。

## NVHPC同梱のcuTENSORバージョン

NVHPC 25.9以降に同梱されるcuTENSORのバージョンは、CUDAのバージョン、CPUアーキテクチャ、CCによって分かれる場合があります。使用する環境を下のタブで選んでください。

```html-embed
<fieldset class="versions">
  <legend class="visually-hidden">CUDAとCPUアーキテクチャ</legend>
  <input class="visually-hidden" type="radio" name="environment" id="cuda13" checked>
  <input class="visually-hidden" type="radio" name="environment" id="cuda12-arm">
  <input class="visually-hidden" type="radio" name="environment" id="cuda12-x86">
  <div class="choices">
    <label for="cuda13">CUDA 13</label>
    <label for="cuda12-arm">CUDA 12 <span>aarch64</span></label>
    <label for="cuda12-x86">CUDA 12 <span>x86_64</span></label>
  </div>

  <table class="panel x86" aria-label="CUDA 12・x86_64の同梱cuTENSOR">
    <colgroup span="1"></colgroup>
    <colgroup span="3"></colgroup>
    <thead>
      <tr><th scope="col" rowspan="2">NVHPC</th><th scope="colgroup" colspan="3">cuTENSOR（CC別）</th></tr>
      <tr><th scope="col">&lt; 7.0</th><th scope="col">= 7.0</th><th scope="col">&gt; 7.0</th></tr>
    </thead>
    <tbody>
      <tr><th scope="row">26.11</th><td>—</td><td>2.2.0</td><td>2.8.1</td></tr>
      <tr><th scope="row">26.9</th><td colspan="3">2.7.0（表下の補足参照）</td></tr>
      <tr><th scope="row">26.5</th><td>2.2.0</td><td colspan="2">2.6.0</td></tr>
      <tr><th scope="row">26.3</th><td>2.2.0</td><td colspan="2">2.6.0</td></tr>
      <tr><th scope="row">26.1</th><td>2.2.0</td><td colspan="2">2.4.1</td></tr>
      <tr><th scope="row">25.11</th><td>2.2.0</td><td colspan="2">2.3.1</td></tr>
      <tr><th scope="row">25.9</th><td>2.2.0</td><td colspan="2">2.3.0</td></tr>
    </tbody>
    <tfoot>
      <tr><td colspan="4">— はリリースノートに該当するCCの記載がないことを示します。</td></tr>
    </tfoot>
  </table>

  <table class="panel arm" aria-label="CUDA 12・aarch64の同梱cuTENSOR">
    <thead>
      <tr><th scope="col">NVHPC</th><th scope="col">CC &lt; 7.0</th><th scope="col">CC ≥ 7.0</th></tr>
    </thead>
    <tbody>
      <tr><th scope="row">26.11</th><td>2.2.0</td><td>2.8.1</td></tr>
      <tr><th scope="row">26.9</th><td>2.2.0</td><td>2.6.0</td></tr>
      <tr><th scope="row">26.5</th><td>2.2.0</td><td>2.6.0</td></tr>
      <tr><th scope="row">26.3</th><td>2.2.0</td><td>2.6.0</td></tr>
      <tr><th scope="row">26.1</th><td>2.2.0</td><td>2.4.1</td></tr>
      <tr><th scope="row">25.11</th><td>2.2.0</td><td>2.3.1</td></tr>
      <tr><th scope="row">25.9</th><td>2.2.0</td><td>2.3.0</td></tr>
    </tbody>
  </table>

  <table class="panel cuda13" aria-label="CUDA 13の同梱cuTENSOR">
    <thead>
      <tr><th scope="col">NVHPC</th><th scope="col">cuTENSOR</th></tr>
    </thead>
    <tbody>
      <tr><th scope="row">26.11</th><td>2.8.1</td></tr>
      <tr><th scope="row">26.9</th><td>2.7.0</td></tr>
      <tr><th scope="row">26.5</th><td>2.6.0</td></tr>
      <tr><th scope="row">26.3</th><td>2.6.0</td></tr>
      <tr><th scope="row">26.1</th><td>2.4.1</td></tr>
      <tr><th scope="row">25.11</th><td>2.3.1</td></tr>
      <tr><th scope="row">25.9</th><td>2.3.0</td></tr>
    </tbody>
  </table>
</fieldset>

<style>
  :root {
    --page: #fff;
    --text: #263548;
    --header: #f3f6fa;
    --line: #d1dae5;
    --selected: #e5f2ff;
    --accent: #005a9e;
  }
  :root[data-theme="dark"] {
    --page: #151b24;
    --text: #e4ebf4;
    --header: #202b39;
    --line: #3c4d61;
    --selected: #1b3651;
    --accent: #9bd1ff;
  }
  body {
    margin: 0;
    background: var(--page);
    color: var(--text);
    font: 14px/1.4 system-ui, sans-serif;
  }
  .versions {
    min-inline-size: 0;
    margin: 0;
    padding: 8px;
    border: 0;
  }
  .visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
    border: 0;
  }
  .choices {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 4px;
    margin-bottom: 8px;
  }
  .choices label {
    display: grid;
    align-content: center;
    min-height: 44px;
    padding: 0 4px;
    border: 1px solid var(--line);
    border-bottom: 3px solid var(--line);
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    text-align: center;
  }
  .choices span {
    font-size: 12px;
  }
  #cuda12-x86:checked ~ .choices [for="cuda12-x86"],
  #cuda12-arm:checked ~ .choices [for="cuda12-arm"],
  #cuda13:checked ~ .choices [for="cuda13"] {
    background: var(--selected);
    border-bottom-color: var(--accent);
    font-weight: 700;
  }
  #cuda12-x86:focus-visible ~ .choices [for="cuda12-x86"],
  #cuda12-arm:focus-visible ~ .choices [for="cuda12-arm"],
  #cuda13:focus-visible ~ .choices [for="cuda13"] {
    outline: 2px solid var(--accent);
    outline-offset: -3px;
  }
  .panel {
    display: none;
    width: 100%;
    border-collapse: collapse;
    text-align: center;
    font-variant-numeric: tabular-nums;
  }
  #cuda12-x86:checked ~ .x86,
  #cuda12-arm:checked ~ .arm,
  #cuda13:checked ~ .cuda13 {
    display: table;
  }
  .panel th, .panel td {
    padding: 4px 6px;
    border-bottom: 1px solid var(--line);
  }
  .panel thead {
    background: var(--header);
  }
  .x86 colgroup:first-child {
    width: 25%;
  }
  .x86 thead tr:last-child th {
    width: 25%;
  }
  .x86 th + th, .x86 thead tr:last-child th, .x86 td {
    border-left: 1px solid var(--line);
  }
  .x86 tfoot td {
    border: 0;
    text-align: left;
    font-size: 12px;
  }
</style>
```

:::details 補足（CUDA 12のx86_64向けNVHPC 26.9と26.11）
CUDA 12のx86_64向け`cuda-multi` RPMでは、標準のライブラリパスの`libcutensor.so.2`は26.9で2.7.0、26.11で2.8.1を指します。両方のRPMに2.2.0と2.6.0も別ディレクトリに同梱されています。表のCC条件はNVIDIAのリリースノートの記載に従っています（[26.9](https://docs.nvidia.com/hpc-sdk/archive/26.9/release-notes/index.html#release-component-versions)、[26.11](https://docs.nvidia.com/hpc-sdk/archive/26.11/release-notes/index.html#release-component-versions)）。

26.9で標準パスからcuTENSOR 2.7.0をロードした場合、対応下限はCC 7.5です。V100などのCC 7.0のGPUでは、cuTENSORの初期化に失敗する可能性があります（[2.7.0の対応表](https://docs.nvidia.com/cuda/cutensor/2.7.0/index.html#support)、[初期化時のGPU対応チェック](https://docs.nvidia.com/cuda/cutensor/2.7.0/release_notes.html#cutensor-v2-4-0)）。
:::

NVHPC 25.7以前は単一のcuTENSORが同梱されています。

|          NVHPC          | cuTENSOR |
| :---------------------- | :------: |
| 25.5, 25.7              |  2.2.0   |
| 25.3                    |  2.1.0   |
| 24.7, 24.9, 24.11, 25.1 |  2.0.2   |
| 24.3, 24.5              |  2.0.1   |
| 24.1                    |  2.0.0   |
| 23.5, 23.7, 23.9, 23.11 |  1.7.0   |
| 23.1, 23.3              |  1.6.2   |
| 22.11                   |  1.6.1   |
| 22.9                    |  1.6.0   |
| 22.3, 22.5, 22.7        |  1.5.0   |
| 21.11, 22.1, 22.2       |  1.4.0   |
| 21.7, 21.9              |  1.3.1   |

なお、NVHPC 21.x・22.xでは、Linux_aarch64とCUDA 10.2の組み合わせに対してcuTENSORは同梱されていません。

## cuTENSORの対応CC

| cuTENSOR                                                                                                                                                                                                                                       | 公式資料に明記されたCC                                                                                                     |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| [2.3.0](https://docs.nvidia.com/cuda/cutensor/2.3.0/index.html#support:~:text=Supported%20SM%20Architectures)〜[2.8.1](https://docs.nvidia.com/cuda/cutensor/2.8.1/index.html#support:~:text=Supported%20SM%20Architectures)                   | 7.5, 8.0, 8.9, 9.0, 10.0, 10.3, 12.0, 12.1                                                                                 |
| [2.2](https://docs.nvidia.com/cuda/cutensor/2.2.0/index.html#support:~:text=Supported%20SM%20Architectures)                                                                                                                                    | 7.0, 7.5, 8.0, 8.9, 9.0, 10.0, 12.0                                                                                        |
| [2.1](https://docs.nvidia.com/cuda/cutensor/2.1.0/index.html#support:~:text=Supported%20SM%20Architectures)[^6]                                                                                                                                | 6.0, 7.0, 7.5, 8.0, 8.9, 9.0, [10.0, 12.0](https://docs.nvidia.com/cuda/cutensor/2.2.0/release_notes.html#cutensor-v2-1-0) |
| [1.6.1](https://docs.nvidia.com/cuda/archive/11.8.0/cutensor/index.html#support:~:text=Supported%20SM%20Architectures)〜[2.0.2](https://docs.nvidia.com/cuda/cutensor/2.0.2/index.html#support:~:text=Supported%20SM%20Architectures)          | 6.0, 7.0, 7.5, 8.0, 8.9, 9.0                                                                                               |
| [1.3.3](https://docs.nvidia.com/cuda/archive/11.4.2/cutensor/index.html#support:~:text=Supported%20SM%20Architectures)〜[1.6.0](https://docs.nvidia.com/cuda/archive/11.7.1/cutensor/index.html#support:~:text=Supported%20SM%20Architectures) | 6.0, 7.0, 8.0                                                                                                              |

[^6]: 2.1.0のサポート一覧にはBlackwellのCCが記載されていません。2.1.0のリリースノートでは追加されたCCが`SM 10.0`と`SM 10.2`ですが、2.2.0に収録された同じ変更履歴では`SM 10.0`と`SM 12.0`になっています。この表では後者の表記を採用しています（[2.1.0のリリースノート](https://docs.nvidia.com/cuda/cutensor/2.1.0/release_notes.html#cutensor-v2-1-0)、[2.2.0に収録された変更履歴](https://docs.nvidia.com/cuda/cutensor/2.2.0/release_notes.html#cutensor-v2-1-0)）。
