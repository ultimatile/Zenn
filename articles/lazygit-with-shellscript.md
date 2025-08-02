---
title: "lazygitでカスタムキーマップに複雑な処理を仕込む"
emoji: "💤"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["git", "lazygit", "bash"]
published: false
---

## はじめに

[lazygit](https://github.com/jesseduffield/lazygit)はGit操作を支援するターミナルUIツールです。
lazygitは少ないキー操作で様々なGit操作を行うことができます。
lazygitそのものについては[mozumasuさんの記事](<https://zenn.dev/mozumasu/articles/mozumasu-lazy-git#git%E7%AE%A1%E7%90%86%E3%82%92%E7%B0%A1%E5%8D%98%E3%81%AB-(lazygit)>)などを参照してください。

lazygitには`git add`、`git commit`、`git push`のような基本的なコマンドはプリセットされたキーマップは当然用意されていますが、カスタムキーマップを自分で割り当てることができます。

カスタムキーマップの設定は以下のようなYAMLファイルで指定します。
詳細は後ほど述べますが、ここでは本記事のモチベーションを説明するためのサンプルを示します。

```yaml:config.yml
customCommands:
- key: "Y"
  context: "commits"
  command: "printf {{.SelectedCommit.Hash}} | head -c7 | pbcopy"
  description: "ショートコミットハッシュをクリップボードにコピー"
```

こう設定すると、コミットのリストが表示されているタブで`Y`キーを押すと、選択中のコミットのショートハッシュをクリップボードにコピーすることができます^[ちなみにフルハッシュはプリセットの`y`キーでコピーできます。]。
`command`の部分に実行するコマンドを記載します。
この例は単純ですが、より複雑な処理を行いたい場合、例えば`if`で分岐したいとか、`gh`で取得した値を使用したいということをやり始めると、難読ワンライナーになっていきます。
YAML記法で改行して書く方法は考えられますが、いずれにせよ可読性が低くなりがちです。

本記事ではこの問題を解決する方法を解説します。
アイデアは単純で`command`に`./copy-short-hash.sh`のように処理内容を書いたシェルスクリプトを指定して実行するだけです。
こうすることで複雑な処理もシェルスリプトに切り出して書くことができます。

アイデアはこれだけですが、上記の例でも`{{...}}`で囲まれた独自の書き方が見えているように、lazygit特有のお作法がいくつかありますのでそれを説明するというのが本記事の内容となります。

### 参考資料

カスタムキーマップに関わる機能を網羅的に解説を行うわけではありませんので、カスタムキーマップの書き方に関する詳細は、[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Custom_Command_Keybindings.md)を参照してください。

また、lazygitのwikiには[Custom Commands Compendium](https://github.com/jesseduffield/lazygit/wiki/Custom-Commands-Compendium)というページがあり、カスタムキーマップの例がいくつか紹介されています。

カスタムキーマップをどう設定すれば分からない場合は[deepwiki](https://deepwiki.com/jesseduffield/lazygit)に相談するのも良いでしょう。

---

これまで独自のキー設定を「カスタムキーマップ」と呼んできましたが、公式には「カスタムコマンド」と呼ばれていますので、以降は「カスタムコマンド」と呼ぶことにします。

## シェルスクリプトを利用したカスタムコマンドの設定方法

以下では、実際に私が使用しているupstreamのプルリクエストを、そのIDで指定してworktreeとしてチェックアウトするカスタムコマンドを例として用います。

### コマンドの設定

コマンドの詳細は

```yaml:config.yml
- key: "V"
  prompts:
    - type: "input"
      title: "PR id (V):"
  command: "$HOME/dotfiles/lazygit/pr-checkout-as-worktree.sh {{index .PromptResponses 0}}"
  context: "global"
  loadingText: "checking out PR as worktree"
  description: "PR No.を指定してチェックアウト (worktree)"
  output: log
```

ポイントはやはり`command`の部分です。

まず実行するシェルスクリプトは絶対パスで指定しています。
これは相対パスはlazygitの実行ディレクトリに依存するためで、相対パスでスクリプトを指定するのは不可能だからです。
設定ファイルの`config.yml`を置くべき場所はOSごとに異なるので、[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Config.md)を参照してください。
基本的に実行するシェルスクリプトはlazygitの設定ファイルと同じディレクトリに置くと良いでしょう。
もちろん別のディレクトリでも問題ありません。
ここではdotfilesというディレクトリ下のファイルへのシンボリックリンクを貼っているので、シェルスクリプトそのものは本来の設定ファイルが置かれるディレクトリにありません。

次に、`{{index .PromptResponses 0}}`という部分ですが、これは`V`キーを実行したときに、コマンド実行前にユーザーが入力した値をコマンドで使用するためのものです。
このようにlazygitが提供するテンプレートを引数としてシェルスクリプトに渡すことが第2のポイントです。
具体的にどのようなテンプレートが使用できるかは[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Custom_Command_Keybindings.md#placeholder-values)を参照してください。

あとはコマンドとしてシェルスクリプトを実行するにあたり、`output`を`log`にするか`terminal`にするかどうかも考慮する点だと思います。
`log`にすると画面の右下にあるコマンドログに出力が表示されます。
`terminal`にするとlazygitの画面が閉じて、シェルスクリプトの実行結果がターミナルに表示されます。
これは大雑把に言えば非同期処理か同期処理かの違いになります。
一旦lazygitを止めて処理すべき内容であれば`terminal`を選ぶと良いでしょう。
なお、`output`には他にも設定値がありますので、[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Custom_Command_Keybindings.md)を参照してください。

### シェルスクリプトの内容

実行している`pr-checkout-as-worktree.sh`は以下のような内容です。
具体的な中身については特に説明しませんが、`gh`コマンドなどをチェックアウトするbranchや作業中のレポジトリ名を取得したいためコマンドが長くなった、という例です。

```bash
#!/bin/bash
set -euo pipefail
pr_id="$1"
branch=$(gh pr view "$pr_id" --json headRefName --jq .headRefName)
repo_name=$(basename "$(git rev-parse --show-toplevel)")
dir_name="${repo_name}-${branch//\//_}"
git fetch upstream "pull/${pr_id}/head:${branch}"
git worktree add "../${dir_name}" "$branch"
```

中身に関しては特に言うことはありませんが、シェバンの`#!/bin/bash`は必要です。
そして以下のように実行権限を付与する必要があります。

```bash
chmod +x "$HOME/dotfiles/lazygit/pr-checkout-as-worktree.sh"
```

これが面倒な場合は`command`の部分を

```yaml
command: "bash $HOME/dotfiles/lazygit/pr-checkout-as-worktree.sh {{index .PromptResponses 0}}"
```

のように書き換えることもできます。

最後のTIPSになりますが、シェルの指定は大事です。
なぜならlazygitは`$SHELL`環境変数を参照してシェルを決定するからです。
したがって、シェルを指定せずにコマンドを書いてしまうとあらゆるシェルで動作するような書き方をしなければならなくなります。
もちろん、古今東西あらゆるシェルで動作する必要はないですが、想定外のシェルで評価され予期せぬ動作となる可能性があるので、シェルを指定することをおすすめします。

## 終わりに

正直特に難しいことはないのですが、そもそもlazygitのカスタムコマンドの雰囲気を伝えたかったのもあり、記事にしました。
カスタムコマンドの紹介記事としては説明をかなり省略しましたが、[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Custom_Command_Keybindings.md)がしっかり書かれているので、そちらを参照してください。
