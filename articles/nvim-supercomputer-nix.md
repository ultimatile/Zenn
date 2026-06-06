---
title: "スパコンでNix出来てNeovimが動いた話"
emoji: "❄"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["nix", "nvim", "hpc"]
published: false
---

共同利用スパコンでNeovimを使いたかったのですが、普通には入りません。[Nix](https://nixos.org)で入れようとしたところ関門が連続しましたが、最終的に[nix-user-chroot](https://github.com/nix-community/nix-user-chroot)経由で動きました。その経緯の記録です。

## 背景: スパコンの開発環境とNixの相性の悪さ

共同利用スパコンには制約が多くあります。

- root権限が無い
- ログインノードで重い処理は禁止（共用のため）
- 計算ノードからインターネットに出られない
- `/home`が[Lustre](https://www.lustre.org/)等の並列ファイルシステムへのシンボリックリンクになっている
- ディスク・inodeの制限が厳しい

一方でNixは、パッケージを`/nix/store`以下に置くことを強く前提にします。ストアパスのハッシュにはストアディレクトリの場所そのものが含まれるため、ストアを`/nix/store`以外に置くと公式バイナリキャッシュ（`cache.nixos.org`）のビルド済みパッケージが一切ヒットしなくなり、すべてローカルビルドに落ちます。つまり「`/nix/store`を使えること」がNixの旨味の前提であり、ここがroot無し・シンボリックリンク・容量制限と正面衝突します。

## 選択肢

やりたいのは、ストアを`/nix/store`という正規パスで使えるようにすることです。
`/nix`を実際に用意できるなら、それが一番素直です。
普通のNixユーザーが通る道でもあります。
ただ共同利用スパコンでは、管理者の協力（`/nix`を作ってもらう、共有ファイルシステムを`/nix`にマウントして全ノードで共有する、非特権ユーザー名前空間を有効化してもらう、など）が要り、普通通りません。
できない場合は、別の場所のストアを`/nix/store`に見せかけるしかありません。
その手段は、必要な権限の高い順に次の3つです。

1. ユーザー名前空間が自分で使える場合。[nix-user-chroot](https://github.com/nix-community/nix-user-chroot)で`~/.nix`を`/nix`にバインドマウントし、論理ストアを`/nix/store`に保ったまま素のNixを動かす[^revival]。
2. コンテナのエントリポイント。[Apptainer](https://apptainer.org/) / [SingularityCE](https://github.com/sylabs/singularity)（旧Singularity）は、管理者がsetuidで入れてくれているマウント名前空間の供給源として使える。`/nix/store`ごとイメージに焼けば計算ノードでも動く。
3. proot。[nix-portable](https://github.com/DavHau/nix-portable)はユーザー名前空間もrootも要らず、ptraceでパスを書き換える。ユーザー名前空間が無い環境でも動く反面、ビルドのような処理では壊れやすい。

実際には権限の低い方から試しました。
まず素のNixで、`NIX_STORE_DIR`を使ってストアを`~/nix/store`に移そうとしました。
しかし背景で述べたストアパス問題（ストアパスがずれてバイナリキャッシュが効かなくなる）に阻まれました。
次にnix-portableを試しましたが、私の環境では動きませんでした。
コンテナ（SingularityCE）は動いたものの、nvimを起動するたびにコンテナを`run`するのが面倒でした。
最終的にnix-user-chrootで落ち着きました。
これがこの記事の解です。

[^revival]: nix-user-chrootは2023年から2026年にかけてREADMEで「unmaintained、nix-portableを試せ」と案内されていましたが、[2026年3月にその記述が外れて再びメンテされています](https://github.com/nix-community/nix-user-chroot/commit/5e414dff108eb3e4f671c352c17ad5ad36dea868)。以前見たときは前者の状態で、選択肢から外していました。

## 実践例

:::message

以下は筆者の環境（共同利用スパコンで、ホームがLustreへのシンボリックリンク）での実例です。
特にファイルシステム由来の関門2は環境に大きく左右されます。
Lustreを使っていない場合や、ホームをシンボリックリンクにしていない場合などでは、遭遇する関門や有効な回避策も変わってきます。
関門2のような拡張属性の問題はLustre特有に見えますが、NFSなど他のファイルシステムでも起こり得ます。
その点はご了承ください。

:::

私の利用するスパコンではnix-user-chrootが使用できました。

### ユーザー名前空間が使えるか判定する

nix-user-chrootは非特権ユーザー名前空間を要求します。
使えるかどうかは次で判定できます。

```bash
unshare --user --pid echo YES
```

`YES`が出れば使えます。
`Operation not permitted`等で落ちれば無効で、その場合はproot（nix-portable）を使うことになります。
無効化されているかはsysctlの`user.max_user_namespaces`（RHEL系）や`kernel.unprivileged_userns_clone`（Debian系）でも確認できます。

私の環境では`YES`が返り、ユーザー名前空間は制限なく使えました。

### nix-user-chrootをビルドする

配布バイナリが自分の環境で動くか怪しかったので、ソースからビルドしました。
ビルドには[cargo](https://doc.rust-lang.org/cargo/)が要ります（cargo自体の導入は省略します）。

ここで「依存の取得はログインノード、ビルドは計算ノード」と分けます。
計算ノードはネットに出られないので、ネットワークが要る依存ダウンロードはログインノードで済ませておきます。

まずログインノードでリポジトリをクローンし、依存を取得します。

```bash
# ログインノード（ネット可）
git clone https://github.com/nix-community/nix-user-chroot
cd nix-user-chroot
cargo fetch
```

`cargo fetch`でnix-user-chrootが依存するクレートもまとめてダウンロードされます。
次に計算ノードに入ってビルドします。

```bash
# 計算ノード（ネット不可）
cargo build --release --offline
```

依存は取得済みなので`--offline`なしでもビルドできました。
とはいえ、ネットに出ないことの保証として`--offline`を付けておくと行儀がよいでしょう。
出来上がったバイナリは`target/release/nix-user-chroot`です。

### Nixをインストールする

用意したnix-user-chrootを使い、ストアにするディレクトリを作って、その中でNix公式インストーラを単一ユーザーモードで走らせます。

```bash
mkdir -m 0755 ~/.nix
./nix-user-chroot ~/.nix bash -c "curl -L https://nixos.org/nix/install | bash"
```

ここから関門が3つ続きました。

### 関門1: LD_LIBRARY_PATH汚染でlibstdc++が合わない

最初はインストーラ内の`nix-store`がこう言って落ちました。

```
nix-store: /lustre/opt/.../gcc/13.2.0/lib64/libstdc++.so.6: version `CXXABI_1.3.15' not found
```

スパコンのmoduleが読み込んでいる古いGCCのlibstdc++を、`LD_LIBRARY_PATH`経由で掴んでしまうのが原因です。
`LD_LIBRARY_PATH`はELFのRUNPATHより優先されるため、Nix自前の新しいlibstdc++が上書きされてしまいます。
対処は2通りあり、どちらか一方で十分です。
そのコマンドだけ`LD_LIBRARY_PATH`を空にするか、`module purge`でモジュール環境をクリアします。

```bash
LD_LIBRARY_PATH= ./nix-user-chroot ~/.nix bash -c "curl -L https://nixos.org/nix/install | bash"
```

:::message alert

`module purge`のし忘れは共同利用スパコンでありがちです。
この`LD_LIBRARY_PATH`周りは、踏むと厄介な地雷です。
システムと非互換なlibc / libstdc++を指したまま`LD_LIBRARY_PATH`を固定すると、システム側のコマンドがABI不一致で軒並み起動できなくなります。
これを`.bashrc`などのシェル起動ファイルへ書き込むと、ログインのたびに環境が壊れます。
修正用のエディタすら起動できず、通常のログインシェルからは手が出せなくなります。
復旧は、壊れた起動ファイルを読み込まない経路から行います。
`scp`や`sftp`で正常な起動ファイルを上書きする（ファイル転送はインタラクティブシェルの起動ファイルを読まないため、壊れた環境の影響を受けません）か、`sshホスト-t 'bash --norc --noprofile'`でクリーンなシェルに入って直すとよいでしょう。

:::

### 関門2: Lustreの拡張属性が剥がせずビルドが死ぬ

次はこれでした。

```
error: removing extended attribute 'lustre.lov' from "...": Permission denied
```

Lustreは全ファイルにストライプ配置情報の拡張属性`lustre.lov`を付けますが、これは非rootユーザーには削除できません。
一方でNixは、ストアにパスを書き込むたびに正規化を行い、その一環で拡張属性をすべて剥がそうとします。
そこで`lustre.lov`の削除が`Permission denied`で失敗します。

nix.confの`ignored-acls`に`lustre.lov`を足すと、Nixはこの属性を削除しようとせず無視します。

```:~/.config/nix/nix.conf
ignored-acls = security.csm security.selinux system.nfs4_acl lustre.lov
```

デフォルトは`security.csm security.selinux system.nfs4_acl`で、NFSの`system.nfs4_acl`で同種の問題が出るのと同じ枠です。
ストアパスのハッシュ計算（NAR）は拡張属性を含まないため、`lustre.lov`を残してもストアパスやキャッシュ互換性に影響しません。
おかげでストアをLustre上のホームに置いたまま回避できました。

### 関門3: flakeが使えない（libgit2がスレッドを作れず落ちる）

nvimを入れようと`nix profile`（flake）を使うと、クラッシュしました。

```
nix profile add nixpkgs#neovim
error (ignored): writing packfile: -1, unable to create thread
Segmentation fault
```

flake経路はnixpkgsをlibgit2ベースのGitキャッシュに取り込み、その際にパックファイル書き込みや`revCount`計算をCPUコア数ぶんのスレッドで行います。
ログインノードのユーザーごとのスレッド・プロセス上限にぶつかって`pthread_create`が失敗し、その失敗をうまく処理できずにSIGSEGVへ至ります。

flakeを避けてチャンネル経由（`nix-env`）で入れると、libgit2のGitキャッシュを通らないためこの問題を踏みません。

```bash
nix-channel --update nixpkgs
nix-env -iA nixpkgs.neovim
```

これでnvimが入りました。
flakeをどうしても使いたい場合は、`ulimit -u`をハード上限まで上げるか、`shallow`指定で`revCount`のスレッドを避けることで対処できます。

### 起動

nvimとその依存は`/nix/store`以下にあり、その`/nix`はnix-user-chrootが張る名前空間の中だけに存在します。
そのためnvimは常にnix-user-chroot越しに起動します。
毎回打つのは面倒なので、シェルにラッパーを置くと楽です。

```bash
nvim() { LD_LIBRARY_PATH= ~/path/to/nix-user-chroot ~/.nix ~/.nix-profile/bin/nvim "$@"; }
```

`LD_LIBRARY_PATH`を空にしているのは関門1と同じ理由で、nvimの依存が古いシステムライブラリを掴むのを防ぐためです。

## まとめ

ここまでの関門と回避策をまとめます。

| 関門                | 症状                                  | 回避                                |
| ------------------- | ------------------------------------- | ----------------------------------- |
| ユーザー名前空間    | 無効だとnix-user-chroot不可           | `unshare`で判定。有効なら使える     |
| LD_LIBRARY_PATH汚染 | `CXXABI not found`                    | `module purge` / `LD_LIBRARY_PATH=` |
| Lustre拡張属性      | `removexattr Permission denied`       | `ignored-acls`に`lustre.lov`        |
| flake/libgit2       | `unable to create thread` →クラッシュ | `nix-env`（チャンネル）で回避       |

ユーザー名前空間が有効で、`ignored-acls`でLustreをなだめ、flakeを避ければ、共同利用スパコンの永続ホーム上で素のNixが動いてNeovimが入ります。
逆にユーザー名前空間が無効なスパコンではnix-user-chrootが使えないため、nix-portable（proot）やコンテナを検討することになります。
