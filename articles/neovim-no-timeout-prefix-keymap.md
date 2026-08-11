---
title: "NeovimのタイムアウトしないZプレフィックス風キーマップの設定"
emoji: "⌨️"
type: "tech"
topics: ["neovim", "lua"]
published: false
register: almost
---

## ZZやZQは「タイムアウトしない」

Vim/Neovimの`ZZ`と`ZQ`コマンドをご存じでしょうか。あまり知られていないキーですが、`ZZ`は`:wq`（保存して終了）、`ZQ`は`:q!`（保存せず終了）とほぼ同じことができます。私は`:q`を打とうとして`q:`（コマンドラインウィンドウ）が暴発し、よくパニックになるので、そもそも`:`を打たずに済む`ZZ`/`ZQ`を`:q`系より好んで使っています。

この`ZZ`/`ZQ`は普通のキーマップとは異なる性質があります。普通の複数キーのキーマップでは、プレフィックスを押したあと次のキーまでに時間を空けすぎると発火しません。たとえば「`Q`のあとに`S`で全バッファ保存」のような2キーのキーマップを作っても、`Q`を押して一拍置いてから`S`を押すと、`QS`として発火しません。これは[`timeoutlen`](https://neovim.io/doc/user/options.html#'timeoutlen')という設定で管理されており、設定された値以上の時間を空けるとタイムアウトします（デフォルトは1000ミリ秒です）。

一方、`ZZ`/`ZQ`にはこの制約がありません。`Z`を押してしばらく放置してから`Z`を押しても、ちゃんと「保存して終了」が実行されます。これは`ZZ`や`ZQ`はキーマップではなく、Vim組み込みのノーマルモードコマンドだからです。組み込みコマンドは`timeoutlen`の対象外なので、次のキーを無期限に待てます。

タイムアウトしないキーマップを作るにはどうすればいいでしょうか？素直な発想としては`timeoutlen`を0にしてしまう方法や、[`notimeout`](https://neovim.io/doc/user/options.html#'timeout')を有効化（`timeout`を無効化）するという方法が考えられます。ただしいずれもグローバルな設定で、すべてのマッピングのタイムアウトを無効化してしまいます。ほかのマッピングの挙動まで巻き込んでしまうため、「特定のプレフィックスだけ`ZZ`のように振る舞ってほしい」という目的には適していません。本記事では、`timeoutlen`や`timeout`をいじらずに、特定のプレフィックスだけタイムアウトさせない方法を扱います。やり方は2通りあり、内部の原理は共通です。ひとつは、プラグインを使わず、`getcharstr()`で`ZZ`風のプレフィックスを自分で実装する方法。もうひとつは、キーの一覧メニューも欲しいので[which-key.nvim](https://github.com/folke/which-key.nvim)を使い、同じ処理をwhich-keyに任せて手動実装を省く方法です。以下ではまず前者を作って仕組みを掴み、それがそのままwhich-keyの内部動作でもある（＝which-keyを使うなら手動実装は要らない）ことを確認していきます。

## 手動で`Z`プレフィックスを再現する

素直な発想だと、`QS`や`QW`のようなキーマップを[`vim.keymap.set()`](<https://neovim.io/doc/user/lua.html#vim.keymap.set()>)で定義したくなります。しかし前述のとおりこのままでは`timeoutlen`待ちが発生します。そこで、`Q`1つだけを「押された瞬間に次のキーを待ち続ける函数」に割り当てます。

```lua
vim.keymap.set("n", "Q", function()
  --次の1キーを無期限に待つ
  local ok, char = pcall(vim.fn.getcharstr)
  if not ok then
    return -- <C-c>などで中断されたら何もしない
  end
  local key = vim.fn.keytrans(char)

  local actions = {
    S = function()
      vim.cmd("wa")
    end, --全バッファ保存
    W = function()
      vim.cmd("xa")
    end, --保存して全終了
    Z = function()
      vim.cmd("qa!")
    end, --保存せず全終了
  }

  local action = actions[key]
  if action then
    action()
  end
end, { desc = "Q-prefix" })
```

各アクションでは[`vim.cmd()`](<https://neovim.io/doc/user/lua.html#vim.cmd()>)を使って、`wa`などのExコマンドを実行しています。函数の中で[`getcharstr()`](https://neovim.io/doc/user/builtin.html#getcharstr%28%29)が次のキーを無期限に待ちます。これが`ZZ`の「`Z`のあとを無期限に待つ」挙動そのものになります。次のキーの取得に`getchar()`ではなく`getcharstr()`を使い、さらに[`keytrans()`](https://neovim.io/doc/user/builtin.html#keytrans%28%29)を通しているのは、`<Esc>`のような特殊キーを`"<Esc>"`という素直な文字列として扱うためです。`getchar()`が返す生の数値やバイト列を直接扱うより、分岐や表示が安定します。[`pcall()`](https://www.lua.org/manual/5.1/manual.html#pdf-pcall)で囲んでいるのは、`<C-c>`による中断（`getcharstr()`が例外を投げる）を握りつぶして静かにキャンセルするためです。

:::message
`Q`を上書きすることには副作用があります。Neovimの組み込みの`Q`は、VimのExモードではなく直前に記録したマクロ（レジスタ）を再生するコマンドに変わっています（`:help Q`）。今回のように`Q`を別の用途に使うなら、この組み込みの`Q`は捨てることになります。
:::

## which-keyでメニューを出したい

手動版でも目的の挙動そのものは手に入っています。ただ、コマンドが増えてくると「`Q`を押したら何が選べるのか」を一覧したくなります。これを担うのが[which-key.nvim](https://github.com/folke/which-key.nvim)で、サブコマンドの一覧をポップアップ表示するプラグインです。

ここからは、手動版に代わってwhich-keyを使う場合の書き方です。which-keyを導入するなら、さきほどの手動ディスパッチ（`Q`函数の中で`getcharstr`を回すコード）はwhich-keyが内部に持っているので不要です。代わりに`QS`などを普通のキーマップとして定義し、`Q`をグループとして登録します。設定場所はNeovim構成によって異なるため、まず必要な定義だけを抜き出すと次のようになります。

```lua
require("which-key").add({ { "Q", group = "Q-Commands" } })

vim.keymap.set("n", "QS", function()
  vim.cmd("wa")
end, { desc = "Write all buffers" })
vim.keymap.set("n", "QW", function()
  vim.cmd("xa")
end, { desc = "Write & quit all buffers" })
vim.keymap.set("n", "QZ", function()
  vim.cmd("qa!")
end, { desc = "Force quit all buffers" })
```

ただし、これだけでは動きません。`Q`を押してもメニューが出ず、それどころかエラーが出ます。

```
E354: Invalid register name: '^@'
```

これは2つの事実が重なって起きています。

ひとつめは、which-keyの`<auto>`（既定のトリガー設定）が、単キーの大文字について`Z`だけを自動でトリガー登録するという点です。任意の単キーを勝手に乗っ取らないための安全策で、`Q`は自動登録の対象になりません（[which-key.nvim v3.17.0の実装](https://github.com/folke/which-key.nvim/blob/fcbf4eea17cb299c02557d576f0d568878e354a4/lua/which-key/buf.lua#L19-L38)）。このためwhich-keyは`Q`に反応しません。これは`Z`以外の大文字単キーでも同様です。

ふたつめは、さきほどの組み込みの`Q`です。which-keyが`Q`を拾わないので、`Q`押下は素通りして組み込みの「直前のマクロを再生」が発火します。一度もマクロを記録していなければ、再生対象のレジスタが空（`^@`）なので`E354`になる、というわけです。これは`Q`キー特有の問題です。

## `Q`を明示的にトリガー登録する

解決策は、`Q`を`<auto>`に任せず、`opts.triggers`に明示することです。明示トリガーには、さきほどの自動登録における単キー制限が適用されません（[which-key.nvim v3.17.0の自動・明示トリガー処理](https://github.com/folke/which-key.nvim/blob/fcbf4eea17cb299c02557d576f0d568878e354a4/lua/which-key/buf.lua#L69-L90)）。

つまり、`opts.triggers`に`Q`を明示的に足せばよいということになります。以下はLazyVim向けの完全な設定例です。LazyVimがユーザー定義のプラグイン設定として読み込む`lua/plugins/which-key.lua`に、実際のキーマップ、グループ名、トリガー設定をまとめます。

```lua:lua/plugins/which-key.lua
return {
  "folke/which-key.nvim",
  keys = {
    { "QS", "<cmd>wa<cr>", desc = "Write all buffers" },
    { "QW", "<cmd>xa<cr>", desc = "Write & quit all buffers" },
    { "QZ", "<cmd>qa!<cr>", desc = "Force quit all buffers" },
  },
  opts = {
    spec = {
      { "Q", group = "Q-Commands" },
    },
    triggers = {
      { "<auto>", mode = "nxso" },
      { "Q", mode = "n" },
    },
  },
}
```

これで`Q`がwhich-keyのトリガーになり、押すとメニューが出て、`QS`などが選べるようになります。明示トリガーの`Q`キーマップ自体が組み込みの`Q`を上書きするので、マクロ再生の誤発火も同時に解消されます。`<auto>`は既定値をそのまま残し、それだけでは登録されない`Q`を明示トリガーとして追加しています。

## which-keyは内部で何をしているのか

以下では、なぜwhich-keyだと「タイムアウトしないプレフィックス」になるのかを内部の動きから確認します。ここが分かると、手動の`getcharstr`版とwhich-key版が内部的には同じことをしている点、そしてwhich-keyを使うなら手動のディスパッチをまるごと委譲できる点が見えてきます。

トリガーとなるキーには、次のようなキーマップが追加されます。

@[github](https://github.com/folke/which-key.nvim/blob/fcbf4eea17cb299c02557d576f0d568878e354a4/lua/which-key/triggers.lua#L39-L52)

このトリガー用キーマップは、`Q`が押されると本来のコマンドではなく、which-keyの入力処理を開始します。手動版では`Q`単体しか定義しなかったので、`Q`で始まる長いマッピングは存在せず、`timeoutlen`待ちはそもそも起きませんでした。which-key版は`QS`などを実際のマッピングとして持つぶん`Q`がそれらのプレフィックスになりますが、トリガーには[`nowait`](https://neovim.io/doc/user/map.html#:map-nowait)が指定されています。そのためNeovimは`QS`などのより長いマッピングを`timeoutlen`のあいだ待たず、`Q`を押した時点でwhich-keyの入力処理を開始します。

トリガーが発火すると、which-keyは自身の入力処理へ移ります。その中心にあるのは、手動版と同じ`getcharstr()`によるブロッキング入力です（[which-key.nvim v3.17.0の実装](https://github.com/folke/which-key.nvim/blob/fcbf4eea17cb299c02557d576f0d568878e354a4/lua/which-key/state.lua#L242-L275)）。実際のコードにはポップアップの描画、スクロール、キャンセル、モード変更などの処理も含まれますが、「次のキーを無期限に待ち、入力に対応する処理へ進む」という基本構造は手動版と変わりません。つまりwhich-keyは、受け身のポップアップ表示器ではなく、プレフィックスキーの入力処理を自分で担うプラグインです。

which-keyを使うなら`getcharstr()`のループを自分で書く必要はありません。無期限待ちの部分はwhich-keyに委譲し、手元には`QS`などの中身の定義と、`Q`をトリガー登録する設定だけを残せばよいことになります。

なお、which-keyが`timeoutlen`をまるごと無視しているわけではありません。あるキーがそれ単体で完結するコマンドであり、かつより長い入力のプレフィックスでもある、という曖昧なケースでは、which-keyは`timeoutlen`を参照して「いま実行するか、より長い入力を待つか」を決めます（[which-key.nvim v3.17.0の実装](https://github.com/folke/which-key.nvim/blob/fcbf4eea17cb299c02557d576f0d568878e354a4/lua/which-key/state.lua#L183-L215)）。これはVim本来の曖昧なマッピング解決を、which-keyのループ内で再現したものです。ところが今回の`Q`は、それ単体では何も実行しない純粋なプレフィックスです。そのため、「`Q`をいま実行するか、より長い入力を待つか」という曖昧性がなく、`timeoutlen`を使った判定も発生しません。`Q`を押したあとの入力待ちはwhich-keyの`getcharstr()`が担うので、`QS`などはキーの間隔を空けても実行できます。

## 謝辞

本記事の内容は[mityu](https://zenn.dev/mityu)さんと[kuu](https://zenn.dev/kuu)さんから教えていただいた内容が基になっています。ありがとうございました。
