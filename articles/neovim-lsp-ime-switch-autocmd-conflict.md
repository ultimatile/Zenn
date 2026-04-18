---
title: "ブラウザで日本語入力中にIMEが勝手に切り替わると思ったらNeovimのLSPが原因だった"
emoji: "👻"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["neovim", "lsp", "ime"]
published: true
published_at: 2026-04-19 23:55
---

:::message
この記事は[Vim駅伝](https://vim-jp.org/ekiden/)の2026-04-20の記事です。
Vim駅伝は常に参加者を募集しています。詳しくは[こちらのページ](https://vim-jp.org/ekiden/about/)をご覧ください。
:::

## はじめに

Neovimで日本語入力する際、挿入モードで日本語入力に切り替え、ノーマルモードに戻ったら英字入力に戻す、というのはよくある運用です。
私は[macism](https://github.com/laishulu/macism)とNeovimのautocmd（特定のイベント発生時にコマンドを自動実行する仕組み）を使って「挿入モードを抜けたら自動で英字入力に戻す」設定をしていました。
さらに、取りこぼしを減らすためにイベントを大量に追加した結果、**Neovim以外のアプリで日本語を入力している最中に勝手に英字入力に切り替わる**という怪奇現象に遭遇しました。

## 問題のあった設定

以下が当時のautocmd設定です。

```lua
local ime_switch_events = {
  "InsertLeave",
  "WinEnter",
  "FocusGained",
  "VimEnter",
  "VimResume",
  "CmdlineLeave",
  "TabEnter",
  "TabLeave",
  "BufEnter",
  "BufLeave",
  "BufNew",
  "CursorMoved",
}
vim.api.nvim_create_autocmd(ime_switch_events, {
  callback = switch_ime_to_english,
  group = vim.api.nvim_create_augroup("IMESwitcher", { clear = true }),
})
```

`switch_ime_to_english`の中身は`macism com.apple.keylayout.ABC`を実行してIMEを英字モードに切り替えるだけの関数です。

## 症状

ブラウザやSlackなど、ターミナル外のアプリで日本語を入力している最中に、突然IMEが英字モードに切り替わるという現象が起きていました。Neovimには一切触れていないにも関わらずです。

発生条件を調べてみると、**NeovimでPythonファイルを開いている状態**で再現しやすいことがわかりました。

## 原因：LSPのバックグラウンド処理がBuf系イベントを発火させる

鍵はLSPにありました。

私はPythonのLSPとして[Pyright](https://github.com/microsoft/pyright)を使用しており、Pyrightはフォーカスの有無に関わらずバックグラウンドでNeovimのLSPクライアントと通信を行っています。ただし、Pyrightや他のLSPサーバー自体がNeovimのautocmdイベントを直接発火させているわけではありません。

実際にイベントを発火させているのは**Neovim組み込みのLSPクライアント**です。LSPサーバーからの応答を処理する過程で何らかのバッファ操作が行われ、その**副作用**として`BufEnter`、`BufLeave`、`BufNew`などのautocmdイベントが発火しているものと考えられます。

具体的にどの処理がイベントを発火させているかまでは追跡していませんが、ユーザーがNeovimを操作していなくても、LSPサーバーとクライアント間の通信に起因して`macism`が実行され、**IMEが英字モードに切り替わっていた**というのが原因でした。

## 対処法：発火イベントを絞る

バックグラウンドで発火しうるイベントを除外し、ユーザー操作でのみ発火するイベントに限定しました。

```lua
local ime_switch_events = {
  "InsertLeave",
  "CmdlineLeave",
  "VimEnter",
  "VimResume",
}
vim.api.nvim_create_autocmd(ime_switch_events, {
  callback = switch_ime_to_english,
  group = vim.api.nvim_create_augroup("IMESwitcher", { clear = true }),
})
```

## まとめ

- `macism`をautocmdで呼ぶ際は**どのイベントで発火するか**に細心の注意が必要
- LSPサーバー自体はNeovimのイベントを知らないが、**Neovim組み込みLSPクライアント**がサーバーの応答を処理する過程でバッファ操作を行い、autocmdイベントが副作用として発火すると考えられる
- IME切り替え用のイベントは`InsertLeave`、`CmdlineLeave`、`VimEnter`、`VimResume`に絞るのが安全
- 気がついてみるとアホみたいな話でしたが、LSPクライアントがバックグラウンドでバッファ操作をしているという事実を知らないと原因にたどり着けない、地味に厄介な問題でした
