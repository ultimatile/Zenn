---
title: "lazygitでカスタムキーマップに複雑な処理を仕込む"
emoji: "💤"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["git", "lazygit", "bash"]
published: false
---

## はじめに

[lazygit](https://github.com/jesseduffield/lazygit)は少ないキー操作で様々なGit操作を行えるターミナルUIツールです。
本稿ではlazygit自体の解説は割愛します。
[mozumasuさんの記事](<https://zenn.dev/mozumasu/articles/mozumasu-lazy-git#git%E7%AE%A1%E7%90%86%E3%82%92%E7%B0%A1%E5%8D%98%E3%81%AB-(lazygit)>)などを参照してください。

lazygitには`git add`、`git commit`、`git push`のような基本的なコマンドはプリセットされたキーマップは当然用意されていますが、カスタムキーマップを自分で割り当てることができます。
lazygitでは「カスタムコマンド」と呼ばれていますので、以降は「カスタムコマンド」と呼ぶことにします^[厳密に言うとcustom command keybindingと呼ばれていますが、長いので省略します。]。

### カスタムコマンドの設定

カスタムコマンドは以下のように`config.yml`中の`customCommands`キー下に設定を記載します。
`config.yml`を置くべきパスはOSごとに異なるので[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Config.md)で確認してください。

```yaml:config.yml
customCommands:
- key: "Y"
  context: "commits"
  command: "printf {{.SelectedCommit.Hash}} | head -c7 | pbcopy"
  description: "ショートコミットハッシュをクリップボードにコピー"
```

こう設定すると、コミットのリストが表示されているタブで`Y`キーを押すと、選択中のコミットのショートハッシュをクリップボードにコピーすることができます^[ちなみにフルハッシュはプリセットの`y`キーでコピーできます。]。

設定した各キーについて簡単に説明します。
必須キーは`context`と`command`です。
なぜか必須ではないですが、`key`でコマンドを実行するキーマップを指定します。

`command`の部分に実行するコマンドを記載します。

`context`はどのタブで実行するかを指定します。
よく利用するタブは、ステージングを行うファイルタブ、ブランチを管理するブランチタブ、コミットを確認するコミットタブなどです。
`context`はそれぞれ`files`、`localBranches`、`commits`が対応しています。
上述のキーマップはコミットを指定して実行しますが、これが差分ファイル一覧が表示されているファイルタブで実行されると意味不明になりますので、コミット一覧が表示されているコミットタブで実行されるように`context: "commits"`と指定しています。
これにより同じキーでもタブごとに異なるコマンドを割り当てることができます。
また`context: "global"`と指定すると、どのタブでも実行可能なコマンドになります。
したがって新たにキーマップを定義する際には、指定する`context`と`global`で定義済みのキーと衝突しないように注意する必要があります。
プリセットのキーマップは[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/keybindings/Keybindings_ja.md)で確認できます。

この例は単純ですが、より複雑な処理を行いたい場合、例えば`if`で分岐したいとか、`gh`で取得した値を使用したいということをやり始めると、難読ワンライナーになっていきます。
YAML記法で改行して書く方法は考えられますが、いずれにせよ可読性が低くなりがちです。

本記事ではこの問題を解決する方法について解説します。
アイデアは単純で`command`に`./copy-short-hash.sh`のように処理内容を書いたシェルスクリプトを指定して実行するだけです。
こうすることで複雑な処理もシェルスクリプトに切り出して書くことができます。

アイデアはこれだけですが、上記の例でも`{{...}}`で囲まれた独自の書き方が見えているように、lazygit特有のお作法がいくつかありますのでそれを説明するというのが本記事の内容となります。

### 参考資料

カスタムコマンドに関わる機能を網羅的に解説を行うわけではありませんので、カスタムコマンドの書き方に関する詳細は[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Custom_Command_Keybindings.md)を参照してください。

また、lazygitのwikiには[Custom Commands Compendium](https://github.com/jesseduffield/lazygit/wiki/Custom-Commands-Compendium)というページがあり、カスタムコマンドの例がいくつか紹介されています。

カスタムコマンドをどう設定すれば分からない場合は[deepwiki](https://deepwiki.com/jesseduffield/lazygit)などに相談するのも良いでしょう。

---

## シェルスクリプトを利用したカスタムコマンドの設定方法

以下では、実際に私が使用している、upstreamのプルリクエストをIDで指定してworktreeとしてチェックアウトするカスタムコマンドを例として用います。

### コマンドの設定

コマンドの設定は

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

です。

ポイントはやはり`command`の部分です。
まず実行するシェルスクリプトは絶対パスで指定します。
相対パスはlazygitの実行ディレクトリ、すなわちプロジェクトパスに依存するため、シェルスクリプトのパスを相対パスで指定できません。

基本的に実行するシェルスクリプトはlazygitの設定ファイルと同じディレクトリに置くと良いでしょう。
もちろん別のディレクトリでも問題ありません。
ここではdotfilesディレクトリ下にシンボリックリンクを貼っているので、シェルスクリプトそのものは本来の設定ファイルが置かれるディレクトリにありません。

次に、`{{index .PromptResponses 0}}`という部分ですが、これは`V`キーを実行したときに、コマンド実行前にユーザーが入力した値をコマンドで使用するためのものです。
このように*lazygitが提供するテンプレートを引数としてシェルスクリプトに渡す*ことが第2のポイントです。
具体的にどのようなテンプレートが使用できるかは[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Custom_Command_Keybindings.md#placeholder-values)を参照してください。

続いて、`output`を`log`にするか`terminal`にするかどうかも考慮する点だと思います。
`log`では、コマンドを実行するとlazygitを開いたまま画面の右下にあるコマンドログに出力が表示されます。
`terminal`にすると、コマンド実行前にlazygitの画面が一旦閉じて、シェルスクリプトの実行結果がターミナルに表示されます。
これは大雑把に言えば非同期処理か同期処理かの違いになります。
一旦lazygitを止めて処理すべき内容であれば`terminal`を選ぶと良いでしょう。
なお、`output`には他にも設定値がありますので、他の設定値が知りたい方は[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Custom_Command_Keybindings.md)を参照してください。

### シェルスクリプトの内容

実行している`pr-checkout-as-worktree.sh`は以下のような内容です。
具体的な中身については特に説明しませんが、`gh`コマンドなどを使用してチェックアウトするブランチや作業中のレポジトリ名を取得したいためコマンドが長くなったという例です。

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

シェバンの`#!/bin/bash`は必要です。
そして以下のように実行権限を付与する必要があります。

```bash
chmod +x "$HOME/dotfiles/lazygit/pr-checkout-as-worktree.sh"
```

これが面倒な場合は`command`の部分を

```yaml
command: "bash $HOME/dotfiles/lazygit/pr-checkout-as-worktree.sh {{index .PromptResponses 0}}"
```

のように書き換えることもできます。

最後になりますが、シェルは指定することをおすすめします。
lazygitは`$SHELL`環境変数を参照してコマンドを実行するシェルを決定するため、想定外のシェルで評価され予期せぬ動作となる可能性があるからです。

## 終わりに

正直特に難しいことはないのですが、lazygitのカスタムコマンドの雰囲気を伝えたかったのもあり、記事にしました。
カスタムコマンドの紹介記事としては説明をかなり省略しましたが、[公式ドキュメント](https://github.com/jesseduffield/lazygit/blob/master/docs/Custom_Command_Keybindings.md)がしっかり書かれているので、そちらを参照してください。
