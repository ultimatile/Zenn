---
title: "数値計算におけるテストオラクル問題"
emoji: "🔢"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["テスト", "数値計算", "ソフトウェアテスト"]
published: false
---

## 参考リンク集（ドラフト）

### 日本語記事

- [「正解が分からない」アルゴリズムをどうテストするか - Zenn](https://zenn.dev/hacobell_dev/articles/48672302988d40)
  - テストオラクル問題の一般的な解説。Metamorphic Testing, Property-based Testing, Intramorphic Testingの3手法を紹介
- [機械学習システムのためのメタモルフィックテスティング入門 - Qiita](https://qiita.com/tokumoto/items/cd3d17cae3b099badaf6)
  - 機械学習文脈でのメタモルフィックテスト解説
- [機械学習の分野でも注目される、メタモルフィックテスティングとは何か - kzsuzuki](https://www.kzsuzuki.com/entry/MetamorphicTesting)
  - メタモルフィックテスティングの概念整理
- [テストオラクルとは何か - kzsuzuki](https://www.kzsuzuki.com/entry/2021/04/12/083000)
  - テストオラクルの概念解説
- [テストオラクルとは何か？概要や対象物について解説 - Q-media](https://q-media.jp/test-oracle/)
  - テストオラクルの基本解説
- [テストオラクルとは？効果的なソフトウェアテストへの活用方法 - Apidog](https://apidog.com/jp/blog/test-oracle-jp/)
  - テストオラクルの活用方法
- [テストオラクル -コードであってはならない-](http://softest.cocolog-nifty.com/blog/2007/02/__b57b.html)
  - テストオラクルに関する古典的な解説
- [Microsoft Cloud Numerics の数学関数をテストする - Microsoft Docs](https://learn.microsoft.com/ja-jp/archive/msdn-magazine/2012/october/numerics-testing-math-functions-in-microsoft-cloud-numerics)
  - 数値計算のテストに最も近い記事。数学的自己一貫性をテスト基盤として使う手法
- [メタモルフィックテスティングの2次元物理エンジンへの適用 (PDF)](https://www.ieice.org/publications/conference-FIT-DVDs/FIT2021/data/pdf/C-013.pdf)
  - 物理エンジン（数値シミュレーション）への適用事例
- [日立 メタモルフィックテスティング資料 (PDF)](https://www.jasst.jp/symposium/jasst19hokkaido/pdf/S3-1-2.pdf)
  - JaSST北海道2019での発表資料
- [「メタモルフィック・テスティングと要求工学」を読んだ - note](https://note.com/suhahide/n/n5591a68c5bc5)
  - メタモルフィックテスティングの読書メモ
- [メタモルフィックテスティングを解釈してみる - note](https://note.com/suhahide/n/nbf880dbf2130)
  - メタモルフィックテスティングの解釈
- [プロパティベーステストの概要とPythonでの実装例 - 千里霧中](https://goyoki.hatenablog.com/entry/2023/12/29/003739)
  - Pythonでのプロパティベーステスト実装例

### 英語文献（学術・サーベイ）

- [Metamorphic Testing: A Review of Challenges and Opportunities - ACM Computing Surveys](https://dl.acm.org/doi/10.1145/3143561)
  - メタモルフィックテストの包括的サーベイ（750本以上の論文をカバー）。数値計算分野への適用は全体の約4%
- [A Survey on Metamorphic Testing - ResearchGate](https://www.researchgate.net/publication/296477118_A_Survey_on_Metamorphic_Testing)
  - メタモルフィックテストの別のサーベイ論文
- [Discovering Metamorphic Relations for Scientific Software From User Forums - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8129917/)
  - 科学技術ソフトウェアに特化。ユーザーフォーラムからメタモルフィック関係を発見する研究
- [Hierarchical Metamorphic Relations for Testing Scientific Software (PDF)](https://homepages.uc.edu/~niunn/papers/SE4Science18.pdf)
  - 科学技術ソフトウェアのための階層的メタモルフィック関係
- [Metamorphic Testing - Wikipedia](https://en.wikipedia.org/wiki/Metamorphic_testing)
  - メタモルフィックテストの概要。1998年にT.Y. Chenにより提案
- [Metamorphic Testing for Cybersecurity - NIST (PDF)](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=920197)
  - NISTによるメタモルフィックテストのサイバーセキュリティへの応用

### プロパティベーステスト関連

- [『実践プロパティベーステスト ― PropErとErlang/Elixirではじめよう』 - ラムダノート](https://www.lambdanote.com/collections/proper-erlang-elixir)
  - 日本語書籍
- [HypothesisでProperty-Based Testingを始めてみた - DevelopersIO](https://dev.classmethod.jp/articles/pbt-hypothesis-python/)
  - PythonのHypothesisライブラリでの実践
- [プロパティベーステストをやってみよう - Qiita](https://qiita.com/kiwa-y/items/354744ef7393d07a8928)
  - TypeScriptでのプロパティベーステスト

### Invariant-Driven Development 関連

- IDDは独立した新手法というより、Design by Contract（不変条件の明示）とProperty-Based Testing（性質のテスト）を「不変量」というレンズで統合し、開発ライフサイクル全体に組み込む開発スタイル/マインドセット
- ただしDbCとPBTは本来レイヤーが異なる:
  - DbC: 不変条件を**仕様として記述**する。実行時assertやTDDの手書きテストで成立し、ファジングは必須でない
  - PBT: 性質を記述した上で**ランダム入力生成（ファジング）で反例を探索**する。入力生成が手法の本質
- IDDの主張の核心は「不変量を書け」であり、検証手段は意図的に抽象化されている:
  - ファザー（Echidna, Medusa等）、形式検証（Halmos, Certora等）、オンチェーンassert、ユニットテスト、手動レビュー、デプロイ後モニタリングを全て選択肢として列挙
  - 「単純な不変量や、ツールで検証するには複雑すぎる不変量には、ドキュメントとユニットテストが重要」と明記（Trail of Bits記事）
  - つまりファジングは必須ではなく、DbCとPBTを区別せず不変量の記述を上位概念として押し出す設計
- Trail of Bitsの文脈ではスマートコントラクトのセキュリティ監査が出自で、Echidna（ファザー）による不変量のPBT的検証が実装の中心
- [Introduction to properties-driven development - DEV Community](https://dev.to/meeshkan/introduction-to-properties-driven-development-547g)
  - PBTをTDDに適用する"properties-driven development"の解説。IDDと実質的に同じ発想
- [Design by contract - Wikipedia](https://en.wikipedia.org/wiki/Design_by_contract)
  - 事前条件・事後条件・不変条件を仕様として記述。Bertrand Meyer / Eiffel (1986)。IDDの思想的源流の一つ

#### 概念・手法

- [The call for invariant-driven development - Trail of Bits Blog (2025)](https://blog.trailofbits.com/2025/02/12/the-call-for-invariant-driven-development/)
  - Invariant-driven developmentの提唱記事。「バグとは強制されていない保証である」という視点。スマートコントラクト文脈だが、不変量を開発ライフサイクル全体に組み込む考え方は数値計算にも通じる
- [Introducing invariant development as a service - Trail of Bits Blog (2023)](https://blog.trailofbits.com/2023/10/05/introducing-invariant-development-as-a-service/)
  - Invariant developmentの実践サービス化。ファジング・形式手法・静的解析を組み合わせた不変量検証
- [Invariant Driven Development - Medium/Statuscode](https://medium.com/statuscode/invariant-driven-development-8231add95e33)
  - Invariant-driven developmentの概念解説。不変量（invariance）を第一級の関心事に昇格させる開発手法
- [Test Invariant - Martin Fowler's bliki](https://martinfowler.com/bliki/TestInvariant.html)
  - Design by ContractのinvariantをTDDに適用する考え方。クラスが常に満たすべき性質をテスト可能なメソッドとして定義
- [Invariant-based programming - Wikipedia](https://en.wikipedia.org/wiki/Invariant-based_programming)
  - 不変量ベースプログラミングの概要。実装前に仕様と不変量を記述する手法
- [ID3A - Invariant Driven Design, Development using Assert (書籍)](https://www.amazon.com/ID3A-Invariant-Driven-Design-Development-ebook/dp/B00A2ICUCG)
  - Assertを用いた不変量駆動の設計・開発に関する書籍

#### 不変量の自動発見・検証

- [Dynamically Discovering Likely Program Invariants (Daikon) (PDF)](https://homes.cs.washington.edu/~mernst/pubs/invariants-tse2001.pdf)
  - プログラムの実行トレースから不変量を自動発見するDaikonツールの論文
- [Daikon公式サイト](https://plse.cs.washington.edu/daikon/)
  - Daikon動的不変量検出器。C, C++, Java, Perl等に対応
- [The Daikon system for dynamic detection of likely invariants - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S016764230700161X)
  - Daikonの手法の詳細。テンプレートマッチング＋反例棄却による"likely invariant"の検出

#### 不変量検出の計算量的困難さ

- [Strong Invariants Are Hard: On the Hardness of Strongest Polynomial Invariants for (Probabilistic) Programs (POPL 2024)](https://dl.acm.org/doi/10.1145/3632872)
  - 多項式ループのstrongest polynomial invariant（最強多項式不変量＝あるプログラム点で成立する全多項式不変量の論理積）の計算がSkolem困難であることを証明。分岐付き確率ループでは計算不能。タイトルの"Strong"はダブルミーニング
  - [arXiv版](https://arxiv.org/abs/2307.10902)
- 不変量検出の困難さの階層:
  - アフィンループ（線形代入）→ 計算可能
  - 多項式ループ → Skolem困難（決定可能性自体が約100年未解決）
  - 分岐付き確率ループ → 計算不能
- Daikonのアプローチはこの困難さを回避している:
  1. 厳密な不変量の証明は行わない（soundnessを捨てる）
  2. あらかじめ用意したテンプレート（`x > 0`, `x = ay + b`等）で探索空間を有限に制限
  3. プログラムを実行してトレースを収集し、全トレースでテンプレートが成立するかをチェック
  4. 成立したものを"likely invariant"として報告（反例が観測されれば棄却）
- 数値計算の文脈では、物理的対称性（保存則等）が不変量のテンプレートを与えてくれるため、「何を検証すべきか」は人間が知っている場合が多い。検出の自動化より検証の自動化が実用的
