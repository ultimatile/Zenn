---
title: "dev-dependency を path で指定したクレートは、壊れたまま cargo publish できてしまう"
emoji: "📦"
type: "tech"
topics: ["rust", "cargo"]
published: false
register: almost
---

:::message

## TL;DR

- dev-dependencyを`version`なしのpathだけで指定したクレートは、それを使うテスト・bench・exampleが公開されたパッケージでビルドできなくても、`cargo publish`が通る。libは壊れない。
- `cargo package`はそうしたdev-dependencyを警告なしに落とすが、それを使うターゲットの宣言はmanifestに残す。verifyがビルドするのはlibとbinだけなので、壊れたターゲットはリリースまでのどこでもコンパイルされない。
- 防ぐには、リリースの手順に自動チェックを組み込み、展開したパッケージの全ターゲットをビルドさせる。
- チェックを通すための直し方は、落ちたdev-dependencyの相手で決まる。兄弟クレートなら`version`を付ける。自己dev-dependencyは直せないので、それに頼るターゲットを`exclude`で外す。公開しないフィクスチャー用クレートは、使う側のクレートの中へ移す。
- 影響を受けるのは、`.crate`を展開してその中でビルドする場合に限られる。利用者のプロジェクトからは、依存先のdev-dependencyはそもそも使われない。

:::

## はじめに

[Rustでテストフィクスチャーを別クレートに切り出したら自クレートの単体テストが壊れた](https://zenn.dev/ultimatile/articles/rust-test-fixtures-cfg-test-dev-dep)では、フィクスチャーをクレート内に`#[cfg(any(test, feature = "test-fixtures"))] pub mod`で置き、自クレートの統合テストからは自己dev-dependencyでfeatureを有効にする方法を紹介しました。この自己dev-dependencyはpathだけで指定するので、crates.ioに公開したパッケージからは消えます。そのため公開されたパッケージでは、この統合テストがビルドできません。それでも`cargo publish`は通ります。

公開しないフィクスチャー用クレートや、兄弟クレートのテスト専用featureをpathだけのdev-dependencyで使う場合も同じです。手元のワークスペースで公開済みの`.crate`を展開してビルドすると、libは通るのに、単体テスト・統合テスト・bench・exampleのテストが`unresolved import`（`E0432` / `E0433`）でコンパイルできませんでした。exampleの本体がこうしたdev-dependencyを使っていれば、展開したパッケージでは`cargo build --examples`が`E0433`で落ちますが、その場合もverifyは通ります。

影響を受けるのは、`.crate`を展開してその中でビルドする場合です。[cargo#14685](https://github.com/rust-lang/cargo/issues/14685)では、その例としてDebianなどのディストリビューションが挙がっています。利用者が自分のプロジェクトから依存先を使うときは、cargoは依存先のdev-dependencyをそもそも使いません。git cloneしたリポジトリではpathの依存がそのまま解決されるので、こちらも問題は起きません。

確認した環境はcargo 1.100.0と[cargo-release](https://github.com/crate-ci/cargo-release) 1.1.2です。

## cargo publishが黙って通る理由

### pathだけのdev-dependencyは黙って落ちる

crates.ioに置かれたパッケージにとって、ワークスペース内のパスは意味を持ちません。`cargo package`は依存の`path`を取り除き、`version`の要求だけを残します。`version`のないpath依存の扱いは、通常の依存とdev-dependencyで違います。通常の依存なら、`cargo package`は`all dependencies must have a version requirement specified when packaging`というエラーで止まります。dev-dependencyは、警告もなくパッケージのmanifestから消えます。

次の3つの形のdev-dependencyは、どれもパッケージから消えます。

```toml:foo/Cargo.toml
[dev-dependencies]
# 公開しないフィクスチャー用クレート
fixtures = { path = "../fixtures" }
# 兄弟クレートのテスト専用 feature
bar = { path = "../bar", features = ["test-fixtures"] }
# 自分自身のテスト専用 feature（自己dev-dependency）
foo = { path = ".", features = ["test-fixtures"] }
```

依存が消えても、それを使うターゲットの宣言は消えません。パッケージの正規化された`Cargo.toml`は、`autotests = false`などを付けたうえで、`[[test]]`・`[[bench]]`・`[[example]]`を明示的に書き出すためです。こうしてパッケージには、依存を失ったターゲットが宣言されたまま残ります。

### verifyはlibとbinしかビルドしない

`cargo package`と`cargo publish`は、既定でパッケージを展開してビルドするverifyを行います。ただし、このビルドが選ぶターゲットは素の`cargo build`と同じで、libとbinだけです。cargoのソースでは、verifyを行う`run_verify`が`CompileFilter::Default`でビルドし、ビルド時の既定のターゲットは`is_bin() || is_lib()`で選ばれます。verifyにほかのターゲットまでビルドさせるオプションもありません。

テストまでverifyさせる提案はcargo#14685にあります。cargoチームはさらに設計が必要だとして、まずプラグインで試すことを勧めており、issueは2026年11月時点でopenのままです。

結果として、dev-dependencyが落ちて壊れたテスト・bench・exampleは、リリースまでの経路で一度もコンパイルされません。

## リリース前の自動チェック: 展開したパッケージの全ターゲットをビルドする

この問題の面倒をcargoが見てくれない以上、リリースの手順の中に自前でチェックを組み込むしかありません。cargo-releaseの`pre-release-hook`から、以下を実行するスクリプトを走らせます（[実装例](https://github.com/ultimatile/ariadnetor/blob/5fd12549e91e212bcde1491bed948db1134182ac/scripts/check-packaged-targets.sh)）。

1. `cargo package --workspace --no-verify`で全クレートの`.crate`を作る。
2. `target/package/packaged-targets/`に`tar -m`で展開する。
3. 展開した各パッケージで、兄弟を`--config 'patch.crates-io.<name>.path="..."'`で互いに指したうえで、次の3つのコマンドをdefaultと`--all-features`の両方で走らせる。

| コマンド                            | 確かめること                                             |
| ----------------------------------- | -------------------------------------------------------- |
| `cargo build --lib`                 | 利用者が実際に得るlibのビルド                          |
| `cargo build --all-targets`         | exampleを実行ファイルとしてビルドできるか               |
| `cargo test --all-targets --no-run` | テストハーネスをビルドできるか（exampleのテストを含む） |

1つ目は、残りの2つではdev-dependencyのfeature指定がlibにも及ぶため必要です。2つ目は、`cargo test --all-targets`がexampleをテストハーネスとしてしかビルドせず、example本体だけが壊れていても通ってしまうため必要です。`--all-features`でも走らせるのは、ファイル全体を`#![cfg(feature = "...")]`で囲んだ統合テストのようにfeatureで囲まれた部分が、defaultでは空のクレートとしてコンパイルされ、壊れていても見えないためです。

スクリプトを`scripts/check-packaged-targets.sh`として置き、`release.toml`から次のように呼びます。

```toml:release.toml
pre-release-hook = ["sh", "-c", "exec \"$WORKSPACE_ROOT/scripts/check-packaged-targets.sh\""]
```

フックはクレートごとに1回ずつ、commitとpublishの前に走ります。0以外で終われば、commitもpublishもされずにリリースが止まります。展開先・展開の仕方・兄弟の解決を上のようにしているのは、ほかの組み方では問題が起きるためです。詳しくは補遺に書きました。

## チェックを通すための直し方

チェックを入れると、すでに壊れているターゲットで落ちます。公開されたパッケージはcrates.ioから解決できる依存だけでビルドされるので、直し方は、落ちたdev-dependencyがその条件で解決できるかどうかで3通りに分かれます。

| dev-dependencyの相手              | パッケージでの解決                                         | 直し方                                                 |
| ---------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------ |
| 兄弟クレート                       | crates.ioから解決できる                                   | `version`を付ける                                     |
| 自分自身                           | crates.ioの自分とパッケージの自分が両方リンクされて壊れる | 自己dev-dependencyに頼るターゲットを`exclude`で外す |
| 公開しないフィクスチャー用クレート | 解決できない                                               | 使う側のクレートの中へ移す                             |

### 兄弟クレートにはversionを付ける

```toml:foo/Cargo.toml
[dev-dependencies]
bar = { path = "../bar", version = "0.1.0", features = ["test-fixtures"] }
```

`version`があればdev-dependencyはパッケージに残り、crates.ioから解決されます。`foo`が通常の依存でも`bar`を使っている場合、両者は1つの`bar`に統合され、`default`と`test-fixtures`の両方のfeatureが有効になります。cargo-releaseの`dependent-version = "upgrade"`を使っていれば、dev-dependencyのversion要求もリリースのたびに上がります。

### 自己dev-dependencyは直せないので、ターゲットを外す

自己dev-dependencyにも`version`は書けます。ワークスペースではビルドが通り、パッケージにも残ります。しかし展開したパッケージをcrates.ioに解決させると、crates.ioにある自分とパッケージ自身の2つがリンクされ、統合テストとbenchがすべて`E0464`（multiple candidates for rlib dependency）で落ちます。

そこで、自己dev-dependency経由でしかフィクスチャーに届かないターゲットは、`exclude`でパッケージから外します。

```toml:foo/Cargo.toml
[package]
exclude = ["/tests/", "/benches/"]
```

ターゲットのルートファイルを外すと、cargoはそのターゲットをmanifestから消し、`warning: ignoring test 'x' as 'tests/x.rs' is not included in the published package`のように知らせます。明示的に宣言した`[[bench]]`も同じ扱いです。

パターンはgitignoreと同じ形式なので、先頭に`/`を付けてパッケージのルートに固定します。`tests/`と書くと、`src/`の下にある単体テスト用のモジュールディレクトリ（`src/foo/tests/`など）にも一致し、libのテストビルドが`E0583`（file not found for module）で壊れます。

`exclude`で外せるのはターゲット単位です。`mod tests;`が参照するモジュールファイルを外しても`mod tests;`の宣言は残るので、そのターゲットのテストビルドが`E0583`になります。libの単体テストがフィクスチャーを使っている場合は、次の方法が必要です。

### 公開しないフィクスチャー用クレートは、使う側のクレートの中へ移す

公開しないフィクスチャー用クレートはcrates.ioに無いので、`version`を付けても解決できません。そこでフィクスチャーを、使う側のクレートの中へモジュールとして移します。

```rust:foo/src/lib.rs
#[cfg(any(test, feature = "test-fixtures"))]
pub mod test_fixtures;
```

```toml:foo/Cargo.toml
[features]
test-fixtures = ["bar/test-fixtures"]

[dev-dependencies]
# 統合テスト・bench・example のテスト用。パッケージでは落ちる
foo = { path = ".", features = ["test-fixtures"] }
```

libの単体テストは`cfg(test)`で`crate::test_fixtures`に届くので、パッケージ単体でもビルドできます。統合テストとbenchは、前節の`exclude`で外しています。

### exampleのテストだけがフィクスチャーを使う場合

exampleの本体はフィクスチャーを使わず、テストだけが使う場合は、テストモジュールをfeatureで囲みます。

```rust:foo/examples/demo/main.rs
#[cfg(all(test, feature = "test-fixtures"))]
mod tests;
```

ワークスペースでは自己dev-dependencyがfeatureを有効にするので、テストはこれまでどおり走ります。パッケージではfeatureが無効なのでテストモジュールが消え、example自体はビルドも実行もできます。`[[example]]`の`required-features`で同じことをしようとすると、パッケージではexample全体がスキップされ、`cargo run --example`もできなくなります。

## まとめ

`cargo package`は`version`のないpathだけのdev-dependencyを黙って落とし、それを使うターゲットの宣言は残します。verifyはlibとbinしかビルドしないので、そうしたdev-dependencyを持つクレートは、テスト・bench・exampleが壊れたままでも`cargo publish`が通ります。これを防ぐには、展開したパッケージの全ターゲットをビルドする自動チェックを、リリースの手順に組み込みます。チェックで失敗したら、兄弟クレートへのdev-dependencyには`version`を付け、自己dev-dependencyに頼るターゲットはルートに固定した`exclude`で外し、libの単体テストが使うフィクスチャーはクレートの中に`#[cfg(any(test, feature = "test-fixtures"))] pub mod`で置きます。

## 補遺: チェックを組むときの落とし穴

ここに挙げる問題は、どれもcargoのverifyなら内部の仕組みで起きずに済んでいるもので、チェックではそれを自前で避ける必要があります。

### 未公開の兄弟クレートが解決できない

`--execute`では、フックが走る時点でversionのbumpはディスクに書かれていますが、新しいversionはまだcrates.ioにありません。展開したパッケージをそのままビルドすると、`failed to select a version for the requirement bar = "^0.2.0"`のように解決の段階で失敗します。dry-runではbumpが書かれないので、要求は最後に公開したversionを指したままになり、ワークスペースより古いcrates.ioのコードに解決されてしまいます。

cargoのverifyは、`cargo package --workspace`のとき、未公開の兄弟を内部の`tmp-registry` overlayで解決しています。このoverlayは外からは使えません。cargo#14685でcargoチームのメンバーが、dependency confusion攻撃を避けるために意図して公開していないと説明しています。

代わりに、展開した各パッケージを`--config 'patch.crates-io.<name>.path="..."'`で互いに指します。patchが効くのはversion要求に合う場合だけですが、ワークスペースのpath依存のversion要求はもともと相手のversionに合っていないとビルドできないので、展開したパッケージにもそのまま合います。

### 展開先で親ワークスペースが見つかる

展開したパッケージをワークスペースの`target/`の下に置いてビルドすると、cargoは上のディレクトリをたどって元のワークスペースを見つけ、エラーにします。

```
error: current package believes it's in a workspace when it's not:
current:   .../ws/target/inpkg-probe/package/foo-0.1.0/Cargo.toml
workspace: .../ws/Cargo.toml
```

cargoのverifyは、展開したパッケージだけからなる一時的なワークスペース（`Workspace::ephemeral`）を作ってこれを避けています。コマンドラインからはこの仕組みを使えませんが、ワークスペースを探す`find_root_iter`には、`target/package`で終わるディレクトリに来たところで探索をやめる特例があります。展開先を`<ワークスペース>/target/package/<任意の名前>/`にすれば、manifestを書き換えずに各パッケージが自分自身のルートになります。上のエラーは、末尾が`target/package`でない`target/inpkg-probe/package`に置いたときのものです。展開したmanifestの末尾に空の`[workspace]`を足す方法でも同じ効果があります。

ただし`target/package/<name>-<version>/`は、cargoのverifyが毎回消して作り直す場所なので避けます。

### 展開先を毎回変えると、成果物が際限なく増える

毎回新しい`mktemp -d`のディレクトリに展開し、`--target-dir`だけを固定すると、走らせるたびに全クレートが新しい場所にビルドし直され、targetディレクトリが膨らみ続けます。

cargoはpathパッケージの成果物を、パスを含むハッシュで区別します。`SourceId::stable_hash`は、ワークスペースルートの下にあるpathソースを相対パスで、それ以外を絶対パスでハッシュします。展開した兄弟は、ビルドしているパッケージのルートの外にあるので、絶対パスがハッシュに入ります。そのため展開先が変わるたびに、別の成果物として作り直されます。

cargoのverifyは`target/package/<name>-<version>/`という固定の場所に展開するので、この問題は起きません。展開先を固定すれば、2回目以降はtargetディレクトリのサイズが増えなくなります。

### 固定した展開先にtarで展開すると、ビルドせずに合格する

`cargo package`は、`.crate`の各エントリのmtimeを固定の古い値にします。cargo 1.100.0で作った`.crate`では、全エントリが2006-07-24でした。普通の`tar xzf`はこのmtimeをそのまま復元します。固定した展開先に、変更したソースを展開し直すと、ソースのmtimeが前回の成果物より古いので、cargoは成果物が最新だと判断します。たとえば`compile_error!`を書き足したソースを`tar xzf`で展開し直しても、何もコンパイルせずに`Finished`で終わります。

cargoのverifyは、展開先を毎回消したうえで、mtimeを復元せずに展開します（`set_preserve_mtime(false)`）。チェックでも展開先を消してから、`tar -m`（mtimeを復元しない）で展開します。その代わり、展開のたびにmtimeが新しくなるので、展開したパッケージは毎回コンパイルし直されます。これはcargoのverifyと同じです。

### cargo-releaseから呼ぶときの注意

- フックはクレートのディレクトリで実行されるので、スクリプトはcargo-releaseが渡す`$WORKSPACE_ROOT`経由で呼ぶ（`release.toml`の例のとおり）。
- `--execute`ではフックの時点でbumpがまだcommitされていないので、`cargo package`に`--allow-dirty`を付ける必要がある。
