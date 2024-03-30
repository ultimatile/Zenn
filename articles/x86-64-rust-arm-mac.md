---
title: "ARM MacにRosetta 2でx86-64 Rust環境を用意する"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [rust, x86, macos, rosetta2]
published: true
---

M1 MacなどのARM MacでRosetta 2を利用してx86-64のRust環境を用意する方法を紹介します．

## やること
1. Rosetta 2の導入
2. Rosetta 2のterminalの起動
3. x86-64用のHomebrewのinstall
4. x86-64用のRustupのinstall
5. 環境変数の設定

既にaarch64のHomebrewをinstallしている方もx86-64のHomebrewをinstallすることに注意してください．

## 使用環境
Apple M2 Mac mini (2023)
macOS 14.3.1 (Sonoma)

## Rosetta 2のinstall
まずは以下のcommandでRosetta 2をinstallします．

```sh:Terminal
softwareupdate --install-rosetta
```

次にCommand Line Tools for Xcodeをinstallします．
```sh:Terminal
xcode-select --install
```
これはHomebrewのinstallに必要です.

:::message
RustのinstallにHomebrewは必須ではありません．
```sh:Terminal
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
を実行すると直接Rustupをinstallすることができます．
https://www.rust-lang.org/tools/install
:::

## Rosetta 2のterminalの起動
次に以下のcommandでRosetta 2のterminalを開きます．

```sh:Terminal
arch -x86_64 zsh
```

## x86-64 Homebrewのinstall
x86-64のHomebrewをinstallします．
```sh:Terminal
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## x86-64 Rustupのinstall
`rustup-init`をinstallします．
```sh:Terminal
brew install rustup-init
```

Rustをinstallするための環境変数を設定します．
`$HOME`はhome directoryです．

```sh:Terminal
export "CARGO_HOME=$HOME/x86_64/.cargo" 
export "RUSTUP_HOME=$HOME/x86_64/.rustup"
```

環境変数を設定せずにdefaultで`rustup-init`を実行すると`$HOME/.cargo`/`$HOME/.rustup`にinstallされます．
この場合，すでにaarch64のRust環境があると衝突しますので`$HOME/x86_64/`にinstallするように設定しています．
どこにinstallするかは衝突しなければよいだけなので他にお好みのinstall場所があれば適宜変更してください．その場合，以下の設定も適宜変更してください．

`rustup-init`を実行します．
以下のように表示が出ます．

```shell-session:Terminal
% rustup-init

Welcome to Rust!

This will download and install the official compiler for the Rust
programming language, and its package manager, Cargo.

Rustup metadata and toolchains will be installed into the Rustup
home directory, located at:

  /Users/USER/x86_64/.rustup

This can be modified with the RUSTUP_HOME environment variable.

The Cargo home directory is located at:

  /Users/USER/x86_64/.cargo

This can be modified with the CARGO_HOME environment variable.

The cargo, rustc, rustup and other commands will be added to
Cargo's bin directory, located at:

  /Users/USER/x86_64/.cargo/bin

This path will then be added to your PATH environment variable by
modifying the profile files located at:

  /Users/USER/.profile
  /Users/USER/.bash_profile
  /Users/USER/.zshenv

You can uninstall at any time with rustup self uninstall and
these changes will be reverted.

Current installation options:


   default host triple: x86_64-apple-darwin
     default toolchain: stable (default)
               profile: default
  modify PATH variable: yes

1) Proceed with installation (default)
2) Customize installation
3) Cancel installation
>
```

表示内容から，いくつか設定が正しいか確認することがあります．
まず最初の2つのPATHが`RUSTUP_HOME`/`RUSTUP_HOME`の設定です．
先ほど行ったようにx86-64用のdirectoryに設定されているか確認してください．

次に`default host triple`が`x86_64-apple-darwin`になっているか確認してください．
`aarch64-apple-darwin`になっている場合があり，これはaarch64用のrustup-initを呼び出していることが原因の可能性が高いです．
Homebrewでinstallした`rustup-init`にPATHが通っていないことが原因だと考えられますので，
現在のinstallを中止し，以下のcommandを実行したのち`rustup-init`を再度実行してください．

```sh:Terminal
eval "$(/usr/local/bin/brew shellenv)"
```

あるいは絶対PATHで`rustup-init`を実行しても良いです．

```sh:Terminal
/usr/local/bin/rustup-init
```

設定が正しいことが確認できたらinstallに進みます．

```shell-session:Terminal
1) Proceed with installation (default)
2) Customize installation
3) Cancel installation
>
```

dafaultのままinstallすると`.profile`/`.bash_profile`/`.zshenv`を書き換えてしまうので，その動作を抑制するために`2`を選択し，Custom installationを行います．
2と入力してEnterを押します．

```shell-session:Terminal
>2
```

以下のように表示されます．

```shell-session:Terminal
I'm going to ask you the value of each of these installation options.
You may simply press the Enter key to leave unchanged.
```

いくつか設定変更について聞かれますが，変更するのは4つ目なので3回Enterを押して3つ目までの設定は変更せずに進めます．

```shell-session:Terminal
Default host triple? [x86_64-apple-darwin]


Default toolchain? (stable/beta/nightly/none) [stable]


Profile (which tools and data to install)? (minimal/default/complete) [default]
```

4つ目の設定で`modify PATH variable`を`n`に変更します．
nを入力してEnterを押します．

```shell-session:Terminal
Modify PATH variable? (Y/n)
n
```

以下のような表示が出ます．

```shell-session:Terminal
Current installation options:


   default host triple: x86_64-apple-darwin
     default toolchain: stable
               profile: default
  modify PATH variable: no

1) Proceed with installation (default)
2) Customize installation
3) Cancel installation
```

`modify PATH variable: no`となっていれば問題ありません．

1を入力してEnterを押し，installを実行します．

色々表示されますが，最後の方に以下のような表示が出ればinstall完了です．

```shell-session:Terminal
Rust is installed now. Great!
```

## 環境変数の設定
続いて，環境変数等の設定を行います．
aarch64 terminalとRosetta terminalで呼び出すHomebrewとRustの環境変数を切り替えるよう設定します．

`$HOME/.zshrc`に以下のような設定を追加します．

```sh:$HOME/.zshrc
if [ $(uname -m) = "arm64" ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
    . "$HOME/.cargo/env"
elif [ $(uname -m) = "x86_64" ]; then
    eval "$(/usr/local/bin/brew shellenv)"
    . "$HOME/x86_64/.cargo/env"
    export RUSTUP_HOME="$HOME/x86_64/.rustup"
    export PS1="(x86_64) $PS1"
fi
```

以下何をやっているのか説明します．興味ない人は読み飛ばしてください．
- `$(uname -m)`で現在のarchitectureを取得しています．`if`でaarch64とx86-64を判別して処理を変更しています．
- `eval "$($HOMEBREW_REPOSITORY/bin/brew shellenv)"`でHomebrewの環境変数を設定しています．
  - `HOMEBREW_REPOSITORY`はdefaultで`/opt/homebrew`(aarch64)と`/usr/local`(x86-64)です．
- `. "$CARGO_HOME/env"`でCargoの環境変数を設定しています．
    - `CARGO_HOME`は`$HOME/.cargo`(aarch64)と`$HOME/x86_64/.cargo`(x86-64)です．
- x86-64のRust環境を使う場合は`RUSTUP_HOME`を`$HOME/x86_64/.rustup`に設定しています．
  - 設定しないとaarch64の`$HOME/.rustup`を参照してしまいます．
- `export PS1="(x86_64) $PS1"`はRosetta terminalを起動しているときに，terminalの左側に`(x86_64)`と表示されるようにしています．必須ではありません．

以上で終了です．お疲れ様でした．

これでRosetta terminalを実行してから，`cargo`などを実行することでx86-64のRust環境を利用することができます．

## おまけ：Rosetta terminalの起動用のalias設定
おまけですが，`$HOME/.zshrc`に以下の設定を追加すると`zx64`でRosetta terminalを呼び出すことができます．
`zarm`はRosetta terminalから通常のterminalに戻るために使います．

```sh:$HOME/.zprofile
# ARM terminal
alias zarm="arch -arm64 zsh"
# Rosetta terminal
alias zx64="arch -x86_64 zsh" 
```