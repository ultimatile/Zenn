---
title: "ARM MacにRosseta2でx86_64 Rust環境を用意する"
emoji: "🦀"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [rust, x86, macos, rosetta2]
published: false
---

M1 MacなどのARM MacでRosetta 2を利用してx86-64のRust環境を用意する方法を紹介します．
x86_64

## やること
1. Rosetta 2の導入
   1. Command Line Tools for Xcodeのinstall 
   2. `zprofile`/`zshrc`の設定
2. Rosetta 2 terminalでx86-64のRust(Cargo)をinstallする

既にaarch64のHomebrewをinstallしている方もx86_64のHomebrewをinstallすることに注意してください．

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

RustのinstallにHomebrewは必須ではありません．
```sh:Terminal
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
を実行すると直接Rustupをinstallすることができます．
https://www.rust-lang.org/tools/install

次に以下のcommandでRosetta 2のterminalを開きます．

```sh:Terminal
arch -x86_64 zsh
```

x86-64のHomebrewをinstallします．
```sh:Terminal
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

`rustup-init`をinstallします．
```sh:Terminal
brew install rustup-init
```

Rustをinstallするための環境変数を設定します．
```sh:Terminal
export "CARGO_HOME=$HOME/x86_64/.cargo" 
export "RUSTUP_HOME=$HOME/x86_64/.rustup"
```

環境変数を設定せずに`rustup-init`を実行すると，`$HOME/.cargo`/`$HOME/.rustup`にinstallされるので，すでにaarch64のRust環境があると衝突しますので`$HOME/x86_64/`にinstallするように設定しています．
どこにinstallするかは衝突しなければ自由なのでお好みのinstall場所に変更してください．

```shell-session:Terminal
% rustup-init

Welcome to Rust!

This will download and install the official compiler for the Rust
programming language, and its package manager, Cargo.

Rustup metadata and toolchains will be installed into the Rustup
home directory, located at:

  /Users/ultimatile/x86_64/.rustup

This can be modified with the RUSTUP_HOME environment variable.

The Cargo home directory is located at:

  /Users/ultimatile/x86_64/.cargo

This can be modified with the CARGO_HOME environment variable.

The cargo, rustc, rustup and other commands will be added to
Cargo's bin directory, located at:

  /Users/ultimatile/x86_64/.cargo/bin

This path will then be added to your PATH environment variable by
modifying the profile files located at:

  /Users/ultimatile/.profile
  /Users/ultimatile/.bash_profile
  /Users/ultimatile/.zshenv

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
>2

I'm going to ask you the value of each of these installation options.
You may simply press the Enter key to leave unchanged.

Default host triple? [x86_64-apple-darwin]


Default toolchain? (stable/beta/nightly/none) [stable]


Profile (which tools and data to install)? (minimal/default/complete) [default]


Modify PATH variable? (Y/n)
n


Current installation options:


   default host triple: x86_64-apple-darwin
     default toolchain: stable
               profile: default
  modify PATH variable: no

1) Proceed with installation (default)
2) Customize installation
3) Cancel installation

```