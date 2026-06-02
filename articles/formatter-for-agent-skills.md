---
title: "車輪の再発明なはずだと思いながらエージェントスキル用のフォーマッターを作った"
emoji: "🛞"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["claudecode", "agentskills"]
published: false
---

## モチベーション

エージェントスキルにフォーマッターを当てて整形したくなりました。

[エージェントスキル](https://agentskills.io/home)は、YAMLフロントマター+本文から成る`SKILL.md`というマークダウンファイルです。
たとえば私が管理している[`done-check`スキル](https://github.com/ultimatile/development-skills/blob/main/skills/done-check/SKILL.md)は、次のような構造をしています。

```markdown
---
name: done-check
description: Single-pass audit of the current diff against quality-list items before declaring a task complete or requesting external review.
---

# Done-Check

Post-hoc audit against the current diff.
```

ある日、`mdformat`というマークダウンフォーマッターをスキルファイルに適用したところ、フロントマターがマークダウンとして整形されてしまい、次のように壊れてしまいました。

```markdown
---

## name: done-check description: Single-pass audit of the current diff against quality-list items before declaring a task complete or requesting external review.

# Done-Check

Post-hoc audit against the current diff.
```

開きの`---`は水平線に、閉じの`---`は直前の数行をまとめてsetext見出しに変えられ、フロントマターとしての構造が完全に失われています。

フロントマター+本文マークダウンという構造は割と一般的であり、たとえば本記事の原稿や、JekyllやHugoなどの静的サイトジェネレーターの記事ファイルも同様の構造を持っています（こちらはTOMLでフロントマターが書かれていることもあります）。
このようなフロントマターを持つファイルにフォーマッターを当てるのは簡単で、単にフロントマターと本文を分割し、それぞれに適切なフォーマッターを当て、最後に両者を結合すれば良いだけです。
そのため、このようなフォーマッターは既に存在しているはずだと思ったのですが、見つけられなかったため、仕方なく自分で作ることにしました。
名前は`partfmt`です。

<https://github.com/ultimatile/partfmt>

## 実は車輪はあった: prettier

ここまで書いておいてですが、結論から言うと、この用途の車輪は既に存在していました。`prettier`です。

`prettier`のMarkdownフォーマッタは、YAMLフロントマターを壊しません。
それどころか、フロントマターのYAMLを整形までしてくれます。
試しに、わざと崩したフロントマター+本文を食わせてみます。

```markdown
---
name:    done-check
topics: ["a","b",  "c"]
nested:
    foo: 1
    bar:   2
---

#   Done-Check


Post-hoc   audit   against the current diff.
*  item one
*  item two
```

これを`prettier --parser markdown`に通すと、次のようになります。

```markdown
---
name: done-check
topics: ["a", "b", "c"]
nested:
  foo: 1
  bar: 2
---

# Done-Check

Post-hoc audit against the current diff.

- item one
- item two
```

開きと閉じの`---`はそのまま保たれ、フロントマター側はYAMLとしてインデントや配列の空白が正規化され、本文側はMarkdownとして整形されています。
`prettier`はフロントマターを認識し、フロントマターはYAMLとして、本文はMarkdownとして、それぞれ別々に整形しているわけです。
つまり`partfmt`がやろうとしていたことを、単体で既に実現しています。

したがって、`SKILL.md`のようなYAMLフロントマター+Markdown本文のファイルを整形したいだけなら、`prettier`一つで足り、`partfmt`は要りません。
車輪の再発明でした。
`prettier`の存在を知らずに作ってしまった、というのが正直なところです。

### それでも`partfmt`が要る場合

ただし、`prettier`では届かない場面が二つあります。

一つは、整形ルールをプロジェクトごとに調整したい場合です。
`prettier`は細かい設定ができないフォーマッタなので、独自の整形ルールを当てたいなら、`mdformat`のような設定可能なフォーマッタを使いたくなります。
ところが`mdformat`を単体でファイル全体に当てると、冒頭で見たとおりフロントマターが壊れます。
ここで`partfmt`が、本文を好きなフォーマッタに流しつつ、フロントマターを保護する役に立ちます。

もう一つは、TOMLフロントマター(`+++`)です。
`prettier`はTOMLフロントマターを保持はしますが、整形はしません。
TOMLフロントマターも整形したいなら、`partfmt`でTOML用フォーマッタ(`taplo`など)に流せばよいわけです。

## フォーマッターの実装

`partfmt`の実装はシンプルで、フロントマターと本文をパースして分割し、TOML設定ファイルで指定したフォーマッターコマンドをそれぞれ当て、それらを再結合して出力するだけです。
`partfmt`はフォーマッター実装を持ちません。
また、YAML/Markdownから構成されていることすら実は理解しません。
単に`---`(YAML)あるいは`+++`(TOML)で囲まれたフロントマターがあるかどうかを判定し、あればフロントマターフォーマッターへ流し、本文を本文フォーマッターに流します。
本当にそれだけです。
分割したフロントマターと本文のフォーマットはユーザーが指定したコマンドに任せ、`partfmt`は分割と再結合だけを行います。
そのため、外部依存はありません。

裏を返すと、`partfmt`が保証するのはフロントマターと本文の境界だけです。
本文の中身は指定されたフォーマッタに丸投げするので、たとえば本文フォーマッタが脚注や数式といったMarkdown方言を理解しなければ、本文側はそのフォーマッタによって壊れ得ます。
それを防ぐのは`partfmt`の役目ではありません。

また、設定がなければ`partfmt`は何も整形せず、入力をそのまま返します。
フロントマターを壊さないことが目的のツールなので、何を当てるか指定されるまでは何もしない、という安全側の挙動をデフォルトにしています。

## インストール

```sh
uv tool install partfmt
```

## 設定ファイルの書き方

前述のとおり、設定がなければ`partfmt`は何もしないので、何をどう当てるかを設定ファイルに書きます。
設定はリポジトリに置いた`partfmt.toml`（または`.partfmt.toml`）に書きます。
フロントマターと本文それぞれに対して、当てたいフォーマッターを`chain`として並べます。

冒頭で触れたスキルファイル（YAMLフロントマター+Markdown本文）に、フロントマターは`prettier`、本文は`mdformat`を当てる例は次のようになります。

```toml: partfmt.toml
[frontmatter]
chain = [{ run = ["prettier", "--parser", "yaml"] }]

[body]
chain = [{ run = ["mdformat", "-"] }]
```

Pythonプロジェクトであれば、`pyproject.toml`の`[tool.partfmt]`以下に同じ内容を書くこともできます。
`ruff`や`mypy`などが`[tool.*]`に設定を集約するのと同じ流儀で、設定ファイルを増やさずに済みます（その場合は各テーブルが`[tool.partfmt.frontmatter]`のように`tool.partfmt`接頭辞付きになります）。

各コマンドは標準入力を受け取って標準出力に書き出すフィルターとして呼ばれます。
そのため、`mdformat -`のように標準入力から読むためのフラグが必要なら、それも含めて`run`にそのまま並べます。
`chain`は配列なので複数並べれば順番に適用されます。

補足として、

- 設定するのは当てたい領域だけで十分です。たとえば本文だけ整形したいなら`body`のチェインだけ書けば、フロントマターはそのまま保たれます。
- 設定ファイルは実行ディレクトリから上位に向かって探索されるので、リポジトリのルートに置いておけばサブディレクトリのファイルにも効きます。
- フォーマッターが失敗したときの挙動は`on_error`で切り替えられます。デフォルトは`strict`（失敗時に中断）で、`best-effort`にするとその領域だけ元の内容を保ったまま処理を続けます。

## 実行方法

設定ができたら、サブコマンドにフォーマットしたいファイルを渡すだけです。
主なサブコマンドは次のとおりです。

- `format` … 整形結果を標準出力に出す（ファイルは変更しない）
- `write` … ファイルをその場で書き換える
- `check` … 差分が出れば終了コード1を返す（CIで整形漏れを弾くのに使える）
- `doctor` … 設定したフォーマッターがPATH上にあるか確認する

`partfmt`自身はフォーマッターを持たないので、設定したコマンドが入っているかを`doctor`で確認できるようにしてあります。

その他のサブコマンドやオプションは`partfmt --help`で確認してみてください。
