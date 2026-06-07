---
title: "スパコンでNix出来てNeovimが動いた話"
emoji: "❄️"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["nix", "nvim", "hpc"]
published: true
---

## はじめに

共同利用スパコンでNeovimを使いたかったのですが、普通には入りません。[Nix](https://nixos.org)で入れようとしたところ関門が連続しましたが、最終的に[nix-user-chroot](https://github.com/nix-community/nix-user-chroot)経由で動きました。その経緯の記録です。

### 背景: スパコンの開発環境とNix

共同利用スパコンでソフトウェアを使う典型的な仕組みが[environment module](https://modules.readthedocs.io/en/latest/)です。`module load`コマンドでコンパイラやライブラリのバージョンを選ぶと、`LD_LIBRARY_PATH`や`PATH`といったグローバルな環境変数が切り替わります。数値計算のスタックをプロジェクト単位で管理するために使用されています。

問題は、エディタのような汎用ツールまでこのグローバル環境に巻き込まれることです。nvimの依存をmoduleで用意すると、その`LD_LIBRARY_PATH`の差し替えが、本来動かしたい計算側のライブラリ解決を揺さぶります。逆に計算用のmoduleを読んだ状態では、nvimが別バージョンのライブラリを掴んで動かなくなります。「nvimを起動するためにmoduleを読み直す」のは筋が悪く、根本的にはenvironment moduleがグローバル環境を握っていることに行き当たります。

Nixはここを断ち切ります。各パッケージは依存を`/nix/store`以下のフルパスで固定します。ELFバイナリでは、RUNPATHが自分の依存（`/nix/store`内）だけを指します。そのため、moduleで環境を整えなくてもnvimが動きます。各ツールが自分の依存を閉じて持ち、moduleに手を触れずに動かせること、これがスパコンでNixを使う旨味です。

ただし、その`/nix/store`が後で効いてきます。Nixのストアには、ハッシュやRUNPATHに焼き込まれる論理パス（既定で`/nix/store`）と、実体を置く物理的な場所の二つの面があり、実体は`/nix/store`の外にも置けます。論理パスを`/nix/store`からずらすと`cache.nixos.org`のビルド済みパッケージとハッシュが合わず、すべてローカルビルドに落ちます。nvimを入れるだけなら、一度待てば済む話に見えるかもしれません。しかしNixを汎用のパッケージマネージャとして使い始めると、あらゆる依存をフルスクラッチで積み続けることになり、さすがに正気とは思えません。したがって論理ストアは`/nix/store`に固定しておくのが筋です。

前提として、スパコンは役割の異なる2種類のノードから構成されることが多いです。ログインノードはSSHで最初に入る共用の作業ノードで、多くのユーザーで共有します。計算ノードは[Slurm](https://slurm.schedmd.com/)などのジョブスケジューラ経由で確保し、実際の計算を流すノードです。これらの上で、次の制約がかかります。

- root権限が無い
- ログインノードで重い処理は禁止（共用のため）。ビルドも計算ノードで行うことが望ましい。
- 計算ノードからインターネットに出られない
- `/home`が[Lustre](https://www.lustre.org/)等の並列ファイルシステムへのシンボリックリンクになっている
- ディスク・inodeの制限が厳しい

実体は`/nix/store`の外に置ける一方、論理パスを`/nix/store`に保つには、その実体を実行時に`/nix/store`として見せる必要があります。この「`/nix`を用意する」一点が、root無し・シンボリックリンク・容量制限と正面衝突します。

### 選択肢

やりたいのは、ストアを`/nix/store`という正規パスで使えるようにすることです。`/nix`を実際に用意できるなら、それが一番素直です。普通のNixユーザーが通る道でもあります。ただ共同利用スパコンでは、管理者の協力（`/nix`を作ってもらう、共有ファイルシステムを`/nix`にマウントして全ノードで共有する、非特権ユーザー名前空間を有効化してもらう、など）が要り、普通通りません。できない場合は、別の場所のストアを`/nix/store`に見せかけるしかありません。その手段は、必要な権限の高い順に次の3つです。

1. ユーザー名前空間が自分で使える場合。[nix-user-chroot](https://github.com/nix-community/nix-user-chroot)で`~/.nix`を`/nix`にバインドマウントし、論理ストアを`/nix/store`に保ったまま素のNixを動かす[^revival]。
2. コンテナのエントリポイント。[Apptainer](https://apptainer.org/) / [SingularityCE](https://github.com/sylabs/singularity)（旧Singularity）は、管理者がsetuidで入れてくれているマウント名前空間の供給源として使える。`/nix/store`ごとイメージに焼けば計算ノードでも動く。
3. proot。[nix-portable](https://github.com/DavHau/nix-portable)はユーザー名前空間もrootも要らず、ptraceでパスを書き換える。ユーザー名前空間が無い環境でも動く反面、ビルドのような処理では壊れやすい。

実際には権限の低い方から試しました。まず素のNixで、`NIX_STORE_DIR`を使ってストアパスを`~/nix/store`に指定しようとしましたがパスの解決がうまくいきませんでした。今思うと後述の拡張属性剥がしの問題だったのかもしれません。だとすると、拡張属性を片付ければ非標準の論理ストアでも済んだ可能性はありますが、未検証です。次にnix-portableを試しましたが、私の環境では動きませんでした。コンテナ（SingularityCE）を試したところ無事に動いたものの、nvimを起動するたびにコンテナを起動するのは面倒です。最終的にnix-user-chrootで落ち着きました。以下ではnix-user-chroot経由でnvimをインストールします。

[^revival]: nix-user-chrootは2023年から2026年にかけてREADMEで「unmaintained、nix-portableを試せ」と案内されていましたが、[2026年3月にその記述が外れて再びメンテされています](https://github.com/nix-community/nix-user-chroot/commit/5e414dff108eb3e4f671c352c17ad5ad36dea868)。以前見たときは前者の状態で、選択肢から外していました。

## 実際にやったこと

:::message

以下は筆者の環境（共同利用スパコンで、ホームがLustreへのシンボリックリンク）での実例です。特にファイルシステム由来の関門2は環境に大きく左右されます。 Lustreを使っていない場合や、ホームをシンボリックリンクにしていない場合などでは、遭遇する関門や有効な回避策も変わってきます。関門2のような拡張属性の問題はLustre特有に見えますが、NFSなど他のファイルシステムでも起こり得ます。 その点はご了承ください。

:::

私の利用するスパコンではnix-user-chrootが使用できました。

### ユーザー名前空間が使えるか判定する

nix-user-chrootは非特権ユーザー名前空間を要求します。使えるかどうかは次で判定できます。

```bash
unshare --user --pid echo YES
```

`YES`が出れば使えます。`Operation not permitted`等で落ちれば無効で、この方法は使えません。その場合はproot（nix-portable）などを検討することになります。 無効化されているかはsysctlの`user.max_user_namespaces`（RHEL系）や`kernel.unprivileged_userns_clone`（Debian系）でも確認できます。

私の環境では`YES`が返り、少なくともnix-user-chrootに必要な範囲ではユーザー名前空間を使えました。

### nix-user-chrootをビルドする

配布バイナリが自分の環境で動くか怪しかったので、ソースからビルドしました。ビルドには[cargo](https://doc.rust-lang.org/cargo/)が要ります（cargo自体の導入は省略します）。

ここで「依存の取得はログインノード、ビルドは計算ノード」と分けます。計算ノードはネットに出られないので、ネットワークが要る依存ダウンロードはログインノードで済ませておきます。

まずログインノードでリポジトリをクローンし、依存を取得します。

```bash
# ログインノード（ネット可）
git clone https://github.com/nix-community/nix-user-chroot
cd nix-user-chroot
cargo fetch
```

`cargo fetch`でnix-user-chrootが依存するクレートもまとめてダウンロードされます。次に計算ノードに入ってビルドします。

```bash
# 計算ノード（ネット不可）
cargo build --release --offline
```

依存は取得済みなので`--offline`なしでもビルドできました。とはいえ、ネットに出ないことの保証として`--offline`を付けておくと行儀がよいでしょう。出来上がったバイナリは`target/release/nix-user-chroot`です。

:::message

以下で`nix-user-chroot`と書いているところは、以降このバイナリを指しており、フルパスを省略して書いてますので注意してください。

:::

### Nixをインストールする

用意したnix-user-chrootを使い、ストアにするディレクトリを作って、その中でNix公式インストーラを単一ユーザーモードで走らせます。

```bash
mkdir -m 0755 ~/.nix
nix-user-chroot ~/.nix bash -c "curl -L https://nixos.org/nix/install | bash"
```

ここから関門が3つ続きました。

### 関門1: LD_LIBRARY_PATH汚染でlibstdc++が合わない

最初はインストーラ内の`nix-store`がこう言って落ちました。

```
nix-store: /lustre/opt/.../gcc/13.2.0/lib64/libstdc++.so.6: version `CXXABI_1.3.15' not found
```

スパコンの[environment module](https://modules.readthedocs.io/en/latest/)が読み込んでいる古いGCCのlibstdc++を、`LD_LIBRARY_PATH`経由で掴んでしまうのが原因です。Nix配布バイナリのようにRUNPATHで依存ライブラリを指しているELFでは、`LD_LIBRARY_PATH`がRUNPATHより優先されるため、Nix自前の新しいlibstdc++が上書きされてしまいます。対処は2通りあり、そのコマンドだけ`LD_LIBRARY_PATH`を空にするか、`module purge`でモジュール環境をクリアします。

```bash
LD_LIBRARY_PATH= nix-user-chroot ~/.nix bash -c "curl -L https://nixos.org/nix/install | bash"
```

:::message alert

`module purge`のし忘れは共同利用スパコンでありがちですが、この`LD_LIBRARY_PATH`周りは、踏むと厄介な地雷です。システムと非互換なlibc / libstdc++を指したまま`LD_LIBRARY_PATH`を固定すると、システム側のコマンドがABI不一致で軒並み起動できなくなります。これを`.bashrc`などのシェル起動ファイルへ書き込むと、ログインのたびに環境が壊れます。修正用のエディタすら起動できず、通常のログインシェルからは手が出せなくなります。復旧は、壊れた起動ファイルを読み込まない経路から行います。`scp`や`sftp`で正常な起動ファイルを上書きする（ファイル転送はインタラクティブシェルの起動ファイルを読まないため、壊れた環境の影響を受けません）か、`ssh <host> -t 'bash --norc --noprofile'`でクリーンなシェルに入って直すとよいでしょう。

:::

### 関門2: Lustreの拡張属性が剥がせずビルドが死ぬ

次はこれでした。

```
error: removing extended attribute 'lustre.lov' from "...": Permission denied
```

私の環境のLustre上では、ストアに入るファイルにストライプ配置情報の拡張属性`lustre.lov`が付いており、これは非rootユーザーには削除できません。一方でNixは、ストアにパスを書き込むたびに正規化を行い、その一環で拡張属性を剥がそうとします。そこで`lustre.lov`の削除が`Permission denied`で失敗します。

nix.confの[`ignored-acls`](https://nix.dev/manual/nix/2.34/command-ref/conf-file.html#conf-ignored-acls)に`lustre.lov`を足すと、Nixはこの属性を削除しようとせず無視します。

```:~/.config/nix/nix.conf
ignored-acls = security.csm security.selinux system.nfs4_acl lustre.lov
```

デフォルトは`security.csm security.selinux system.nfs4_acl`で、NFSの`system.nfs4_acl`で同種の問題が出るのと同じ枠です。NARとしてシリアライズされる内容には拡張属性が入らないため、`lustre.lov`を無視してもNixは動きます。おかげでストアをLustre上のホームに置いたまま回避できました。

参考: <https://github.com/NixOS/nixpkgs/issues/29778>

### 関門3: flakeが使えない（libgit2がスレッドを作れず落ちる）

nvimを入れようと`nix profile`（flake）を使うと、クラッシュしました。

```
nix profile add nixpkgs#neovim
error (ignored): writing packfile: -1, unable to create thread
Segmentation fault
```

flake経路はnixpkgsをlibgit2ベースのGitキャッシュに取り込みます。`writing packfile`と`unable to create thread`というメッセージから、libgit2のpackfile生成中にスレッド作成へ失敗した症状と整合します。私の環境では、ログインノード側のプロセス・スレッド数上限やメモリ制限に当たった可能性が高いと見ています。

flakeを避けてチャンネル経由（`nix-env`）で入れると、この問題を踏みません。チャンネルはnixpkgsをtarballとして取得・展開するので、flakeのlibgit2によるGit入力の更新とは別経路です。
実際こちらは問題なく入りました。

```bash
nix-channel --update nixpkgs
nix-env -iA nixpkgs.neovim
```

これでnvimが入りました。

### 起動

nvimとその依存は`/nix/store`以下にあり、その`/nix`はnix-user-chrootが張る名前空間の中だけに存在します。そのためnvimは常にnix-user-chroot越しに起動します。毎回打つのは面倒なので、シェルにラッパーを置くと楽です。

```bash
nvim() { LD_LIBRARY_PATH= nix-user-chroot ~/.nix ~/.nix-profile/bin/nvim "$@"; }
```

- `LD_LIBRARY_PATH=`で空にしているのは保険。`LD_LIBRARY_PATH`はRUNPATHより先に探索されるため、moduleが同じSONAMEの非互換ライブラリを積んでいると`/nix/store`の正規の依存より先に掴まれ得る（関門1と同じ探索順の問題）。空にせず動く環境もあるが、その時の`LD_LIBRARY_PATH`の中身次第なので、付けておくのが安全。
- `nix-user-chroot`は前述のビルド済みバイナリ。PATHが通っていなければフルパスに読み替える。

## まとめ

ここまでの関門と回避策をまとめます。

| 関門                | 症状                                  | 回避                                |
| ------------------- | ------------------------------------- | ----------------------------------- |
| ユーザー名前空間    | 無効だとnix-user-chroot不可           | `unshare`で判定。有効なら使える     |
| LD_LIBRARY_PATH汚染 | `CXXABI not found`                    | `module purge` / `LD_LIBRARY_PATH=` |
| Lustre拡張属性      | `removexattr Permission denied`       | `ignored-acls`に`lustre.lov`        |
| flake/libgit2       | `unable to create thread` →クラッシュ | `nix-env`（チャンネル）で回避       |

これでようやくスパコンでNeovimが動きました。
