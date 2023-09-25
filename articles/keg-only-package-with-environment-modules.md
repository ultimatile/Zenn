---
title: "環境変数などの設定が必要なHomebrew packageをEnvironment Modulesで管理する"
type: "tech" # tech: 技術記事 / idea: アイデア
emoji: "🍺"
topics: [homebrew, environmentmodules, mac]
published: true
---

## はじめに
macOSでHomebrewを使っている方はpackageを追加した際に以下のような表示を見たことがあるのではないでしょうか?

```:terminal
llvm is keg-only, which means it was not symlinked into /opt/homebrew,
because macOS already provides this software and installing another version in
parallel can cause all kinds of trouble.
```

書いてある通りですが, macOSや他のformulaが提供しているsoftwareと競合するpackageをHomebrewでinstallしようとするとsymbolic linkは作成されません.

そのため, keg-onlyのpackageを使用するには手動で環境変数などの設定を行う必要があります
^[なお, keg-onlyというのは直訳すると「樽だけ」となります.
Homebrew(自家酒造)ではCellar(地下貯蔵室) directoryでpackageが管理されているため, keg-only(樽だけ)というのはCellar内に留めて外に出さないということなのだと思います.
~~知らんがな~~.].
どうやって設定を行えば良いかというと基本的にpackageをinstallした際に表示されるmessageに書いてあります.
例えば, llvmの場合は以下のようになっています
llvmはC(++) compilerの[LLVM Clang](https://github.com/llvm/llvm-project)のことです.
正確にはllvmを入れるとLLVM Clang以外も色々入る気がしますが, ややこしいので以下ではLLVM Clangという呼び方をします.

```:terminal
To use the bundled libc++ please add the following LDFLAGS:
  LDFLAGS="-L/opt/homebrew/opt/llvm/lib/c++ -Wl,-rpath,/opt/homebrew/opt/llvm/lib/c++"

llvm is keg-only, ... # 上記のmessageのため省略

If you need to have llvm first in your PATH, run:
  echo 'export PATH="/opt/homebrew/opt/llvm/bin:$PATH"' >> ~/.zshrc

For compilers to find llvm you may need to set:
  export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
  export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"
```

まとめると環境変数`PATH`, `LDFLAGS`, `CPPFLAGS`を設定せよということです.

基本的に書いてあるcommandをterminalで実行すれば動きますが, 上記commandには2つ問題点があります.

1つ目は`PATH`変数の設定です.
上記のmessageの該当部分は

```:terminal
If you need to have llvm first in your PATH, run:
  echo 'export PATH="/opt/homebrew/opt/llvm/bin:$PATH"' >> ~/.zshrc
```

で, `.zshrc`で`PATH`変数を設定するように書かれています.
このcommandを実行するとterminalの起動時に自動的にLLVM Clangが使用可能になります.
この方法の問題は, macOSに入っているApple Clang^[正確にはXcodeかCommand Line Tools for Xcodeを入れる必要がありますが, Homebrewを入れる際に必要なので入っているはずです.]が見つからなくなることです.
自分でApple Clangを使いたい場合や, 他のpackageなどがApple Clangを前提としている場合は不具合が発生する可能性があります.

2つ目は環境変数などを毎回設定するのが面倒ということです.
上記のcommandを覚えたり, どこかに記録しておかないといけません.
また, 上記のmessageはinstallした際にしか表示されないので1度忘れると再確認するのも面倒です.

これらの問題を解決するために, [Environment Modules](http://modules.sourceforge.net/)を用いて環境変数などの設定を管理します.
Environment Modulesは環境変数などを管理するためのpackageで, 共同利用スパコンでよく使われています.
Environment Modulesを導入することで
```zsh:terminal
module load llvm
```
というcommandを実行するだけで`PATH`, `CPPFLAGS`, `LDFLAGS`が設定されるようになります.

また, 
```zsh:terminal
module unload llvm
```
で元に戻すことができ, Apple Clangとの使い分けも容易になります.

この後は
- Environment Modulesでpackageを管理するための`modulefile`の作成
- Environment Modules packageの導入

という流れになります.
今回はllvm (LLVM Clang)を例にして説明します.
内容としては通常のEnvironment Modulesの導入と大差はありませんが, Homebrew+Environment Modulesの設定の具体例として参考にしていただければと思います.
keg-only packageの管理方法として他に良い方法があれば教えていただきたいです.

## `modulefile`の作成
まずはEnvironment Modulesで各packageを管理するための`modulefile`を作成します.

`modulefile`を置いておくdirectoryを決めてください.
ここでは`MODULEFILE_PATH`とします.
`MODULEFILE_PATH`に`modulefiles`というdirectoryを作成して, `llvm`という設定fileを以下のように作成します.

```tcl:/MODULEFILE_PATH/modulefiles/llvm
#%Module

conflict llvm

# set PATH
prepend-path PATH /opt/homebrew/opt/llvm/bin

# set CPPFLAGS
if { [info exists ::env(CPPFLAGS)] } {
    setenv CPPFLAGS "-I/opt/homebrew/opt/llvm/include $::env(CPPFLAGS)"
} else {
    setenv CPPFLAGS "-I/opt/homebrew/opt/llvm/include"
}

# set LDFLAGS
if { [info exists ::env(LDFLAGS)] } {
    #setenv LDFLAGS "-L/opt/homebrew/opt/llvm/lib $::env(LDFLAGS)"
    # To use the bundled libc++
    setenv LDFLAGS "-L/opt/homebrew/opt/llvm/lib -L/opt/homebrew/opt/llvm/lib/c++ -Wl,-rpath,/opt/homebrew/opt/llvm/lib/c++ $::env(LDFLAGS)"
} else {
    #setenv LDFLAGS "-L/opt/homebrew/opt/llvm/lib"
    # To use the bundled libc++
    setenv LDFLAGS "-L/opt/homebrew/opt/llvm/lib -L/opt/homebrew/opt/llvm/lib/c++ -Wl,-rpath,/opt/homebrew/opt/llvm/lib/c++"
}
```

:::message
Homebrewのinstall directoryを変更している場合は`/opt/homebrew`の部分を適宜読み替えてください.
:::

`modulefile`はTcl言語で記述されます.
詳細については述べませんが簡単に記載内容について説明します.
- `modulefile`のfile名は任意です. ここでは`llvm`としていますがversion名など他の名前でも問題ありません. 実際に使用する際には`module load llvm`というように`modulefile`のfile名を指定するため, 命名規則を明確にしておいた方が良いでしょう.
- `#%Module`は`modulefile`の先頭に必ず書く必要があります.
- `conflict llvm`は同時にloadできないmoduleを指定するための設定です
^[これは, 例えばLLVM Clangの異なる複数のversionを管理する場合に, 異なるversionのLLVM Clangを同時にloadすることができないようにするというような使い方をします.
ここでは`modulefile`のfile名と同じ名前を`conflict`で指定しているので少し紛らわしいですが, `conflict`で指定する名前は`modulefile`のfile名とは関係なく, `conflict`で指定した名前で衝突判定が行われます.].
- `PATH`は`prepend-path`で設定します. `prepend-path`は現在の`PATH`変数の先頭に追加します.
- `append-path`で現在の`PATH`の末尾に追加することもできます.
- 環境変数は`setenv`で設定します.
- `setenv`は`prepend-path`や`append-path`と異なり, 現在の環境変数を上書きします.
そのため, 環境変数が既に設定されているか否かを判定し, 動作を変えるようにしています.
- `LDFLAGS`の設定が少し複雑なのは, LLVMの標準library`libc++`を使う設定をしているためです. Apple Clangにbundleされた`libc++`を使用して問題ない場合はcomment outしている部分の設定を代わりに使ってください.

他のpackageについても同様に`modulefile`を作成することでEnvironment Modulesで管理できるようになります.

## Environment Modulesの導入
Environment Modulesを導入します.
Homebrewで入ります:

```zsh:terminal
brew install modules
```

次に, `module` commandを使用するために`.zshrc`に以下を追記します^[bashなど, 他の環境を使っている方は適宜読み替えてください. `source` commandの内容も変わるはずなので, Environment Modulesをinstallした際に表示されるmessageを確認してください].
`MODULEFILE_PATH`は`modulefiles`を置くdirectoryのpathを記載してください.
また, Homebrewのinstall directoryを変更している場合は`/opt/homebrew`を変更した場所にしてください.
1行目に関してはEnvironment Modulesをinstallした際に出てくるmessageに書いてあるcommandを参照した方が確実です.

```zsh:.zshrc
source /opt/homebrew/opt/modules/init/zsh
module use /MODULEFILE_PATH/modulefiles
```

追加したらterminalを再起動するか
`exec $SHELL`を実行して設定を反映させます.

`module` commandが使えるか確認します.

```zsh:terminal
module --version
Modules Release 5.3.1 (2023-06-27) #出力結果
```

これでEnvironment Modulesの導入は完了です.
先に記載した通り,
```sh:terminal
module load llvm
```
でLLVM Clangが使えるようになります.
`module` commandの詳しい使い方は[公式document](https://modules.readthedocs.io/en/latest/modulefile.html)などを参照してください.

## 参考文献
https://modules.readthedocs.io/en/latest/modulefile.html
https://x.momo86.net/article/36#config
https://qiita.com/Ag_smith/items/f268ad27165a60aecd35