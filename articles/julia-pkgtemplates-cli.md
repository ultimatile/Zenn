---
title: "コマンドラインからJuliaパッケージテンプレートを生成するツールを作った"
emoji: "🟣"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [julia]
published: false
---

## はじめに

Juliaでパッケージを作成する際には、テストやライセンスなどを自動生成してくれる[PkgTemplates.jl](https://github.com/JuliaCI/PkgTemplates.jl)を使うことが多いです。
しかし、PkgTemplates.jlはJuliaのREPL上で実行するか、Juliaスクリプトを作成して実行する必要があります。
Juliaパッケージを作成する際に、毎回JuliaのREPLを起動したり、スクリプトを作成するのが個人的に面倒に感じていました。
スクリプトを作成する場合にも、そのスクリプトの管理が問題になります。
そこで、コマンドラインから簡単にパッケージテンプレートを生成できるツール[JuliaPkgTemplatesCLI](https://github.com/ultimatile/JuliaPkgTemplatesCLI)を作成しました。
以下JTCと略します。

## インストール

JTCはPkgTemplates.jlのPythonラッパーです。
uvを使ってGitHubのレポジトリから直接インストールできます。

### 依存関係

JTCはPythonと（当たり前ですが）Juliaが必要です。
またPkgTemplates.jlが呼び出されるデフォルト環境でインストールされている必要があります。

### GitHubレポジトリからインストール

```bash
uv tool install git+https://github.com/ultimatile/JuliaPkgTemplatesCLI.git
```

### インストール無しで試す

uvxコマンドを使えばインストールせずに試すことも可能です。

```bash
uvx --from git+https://github.com/ultimatile/JuliaPkgTemplatesCLI jtc create MyPackage.jl
```

## 使い方

### 基本的なパッケージ生成

最も基本的な使い方は

```bash
jtc create MyPackage.jl
```

です。これにより、カレントディレクトリに`MyPackage.jl`という名前のディレクトリが作成され、その中にPkgTemplates.jlによってパッケージテンプレートが生成されます。

:::message
注意点として、Juliaのプロジェクトは`MyPackage.jl`のように`.jl`で終わる名前にすることが一般的です。
しかし強制ではありませんので、JTCでは`.jl`を含まない名前でもパッケージ生成ができるようにしています。
そのため、明示的に`.jl`を付けたパッケージ名を指定する必要があります。
:::

以下のようにパッケージの設定を実行時引数でオプションを指定することも可能です：

```bash
jtc create MyPackage.jl --license Apache --formatter style=sciml
```

上記の例では、ライセンスをApache 2.0に設定し、Formatterプラグインのスタイルを`sciml`に設定しています。

## デフォルト値設定

JTCでは、`jtc config`コマンドでデフォルト値を設定できます。
これにより、普段使う毎回同じオプションを指定する手間を省けます。

```bash
jtc config --user "Your Name" --license MIT --formatter style=sciml
```

設定は(デフォルトでは)`~/.config/jtc/config.toml`にTOMLで保存されます。

また、

```bash
jtc config
```

とオプションなしで実行すると、現在のデフォルト設定を確認できます。

## プラグイン情報の確認

利用可能なプラグインとその設定オプションを確認できます：

```bash
# 全プラグインをリスト表示
jtc plugin-info

# 特定のプラグインの詳細を表示
jtc plugin-info Formatter
```

## シェル補完

現在はfish shellでのシェル補完をサポートしています：

```bash
echo 'jtc completion | source' > ~/.config/fish/completions/jtc.fish
```

# 主な特徴

## mise統合

JTCの最大の特徴の一つは、[mise](https://github.com/jdx/mise)とのタスク統合です。生成されたパッケージには、Pkg.jl関連のコマンド（`add`、`rm`、`instantiate`など）をmiseタスクとして実行できるファイルが自動で生成されます。

これにより、以下のようなワークフローが可能になります：

```bash
# パッケージ生成
jtc create MyPackage.jl

# miseタスクでパッケージ管理
cd MyPackage.jl
mise run add SomePackage
mise run test
mise run instantiate
```

## PkgTemplates.jlプラグインサポート

JTCは[PkgTemplates.jl](https://github.com/JuliaCI/PkgTemplates.jl)のすべてのプラグインをサポートしており、それぞれのプラグイン固有のオプションも設定できます：

- **CompatHelper**: 依存関係の自動更新
- **TagBot**: GitHubでの自動リリース
- **Documenter**: ドキュメント生成とデプロイ
- **Codecov**: コードカバレッジレポート
- **GitHubActions**: CI/CDワークフロー
- **ProjectFile**: パッケージメタデータ管理
- **Formatter**: JuliaFormatterでのコードフォーマット
- **Tests**: テストフレームワーク設定
- **Git**: Gitリポジトリの初期化

各プラグインの詳細な設定オプションは`jtc plugin-info`コマンドで確認できます。

## 柔軟な設定管理

XDG Base Directory標準に従った設定管理により、ユーザーごとのカスタマイズが簡単に行えます。設定ファイルはTOML形式で管理され、プラグイン固有の設定も含めて一元管理できます。

# まとめ

JTCは、Juliaパッケージの作成を効率化するコマンドラインツールです。PkgTemplates.jlの機能を活かしつつ、mise統合による現代的な開発ワークフローをサポートし、設定の管理も簡単に行えます。

特に以下のような場面で有用です：

- REPLを立ち上げずにサクッとパッケージを作成したい
- mise統合で統一されたタスク管理を行いたい
- 複数のプロジェクトで一貫した設定を使いたい
- シェル補完でコマンドを効率的に実行したい

> **注意**: JTCは現在ベータ版です。アクティブに開発が行われており、バグや破壊的変更が含まれる可能性があります。

<https://github.com/ultimatile/JuliaPkgTemplatesCLI>
