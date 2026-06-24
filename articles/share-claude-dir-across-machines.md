---
title: "~/.claudeを複数マシンで共有するときの落とし穴（iCloud同期とmemoryのパスキー）"
emoji: "🔗"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["claudecode", "macos", "dotfiles", "icloud"]
published: false
register: joutai
---

## TL;DR

- `~/.claude`を丸ごとシンボリックリンク（symlink）でiCloudに逃がすのは勧めない。このディレクトリには「設定」と「ランタイム状態」が同居しており、後者をiCloudに置くと同期競合で壊れる。
- より本質的な理由は別にある。`projects/`配下はプロジェクトの絶対パスでキー化されるため、マシン間でユーザー名が違うとmemoryもセッション履歴も別ディレクトリに分岐し、共有したつもりが共有されない。
- 設定（`CLAUDE.md`・`settings.json`・`skills/`など）はdotfiles＋gitで共有する。memoryを共有したいなら対象を絞ってsymlinkするか、パスキー自体を揃える。高頻度で書き換わる状態ファイルは共有対象に入れない。

## 前提

複数マシンでClaude Codeの設定とmemoryを共有したい。素朴に思いつくのは、iCloud Driveのルートに`.claude`を置き、各マシンの`~/.claude`からsymlinkで参照して一本化する方法である。しかし、この素朴な同期は期待どおりには動かない。symlinkの機構そのものが悪いのではなく、`~/.claude`に性質の異なるものが同居していることに由来して、内容の整合性が2系統で崩れる。

以下、2台のマシン（ユーザー名`user1` / `user2`）を例に、何が起きるか、そして正しいやり方を示す。

## `~/.claude`には2種類のものが同居している

まず`~/.claude`の中身を眺めると、性質の異なる2系統が混ざっていることが分かる。

設定（マシン非依存で、共有したいもの）に当たるのは次のあたりである。

- `CLAUDE.md`（グローバル指示）
- `settings.json`
- `skills/`・`plugins/`・`commands/`・`agents/`
- `hooks/`

一方、ランタイム状態（マシンローカルで、共有してはいけないもの）が大量にある。

- `history.jsonl`（数MB規模で頻繁に追記される）
- `sessions/`・`session-env/`・`shell-snapshots/`
- `file-history/`
- `projects/`（後述。セッション履歴とmemoryの実体）
- `cache/`・`paste-cache/`・`*-cache.json`・`telemetry/`・`.last-cleanup`

共有したいのは前者だけなのに、丸ごとsymlinkすると後者まで巻き込む。ここから2つの問題が出る。

## 問題1: iCloudの同期競合で状態ファイルが壊れる

iCloud Driveは結果整合・遅延同期のストレージである。2台でClaude Codeを動かす（あるいはファイルを開いたままにする）と、`history.jsonl`や`sessions/`配下のような頻繁に書き換わるファイルに対して、iCloudが次のような壊し方をしてくる。

- 同時書き込みに対して`〜のコピー(競合)`という競合コピーを量産する
- 容量節約のためファイルをdatalessなプレースホルダに退避し、読み出し時にダウンロード待ちやエラーを起こす
- 部分同期の途中状態を掴んでJSONLが途中で切れる

状態ファイルはこうして壊れる。設定ファイルは変更頻度が低いので競合しにくいが、状態ファイルは追記が激しいので競合の常襲地帯になる。

## 問題2: `projects/`は絶対パスでキー化される（影響が大きい）

memoryを共有したいなら、こちらのほうが本質的な障害になる。Claude Codeはプロジェクトごとのセッション履歴とmemoryを`projects/<エンコードした絶対パス>/`の下に置く。エンコードは作業ディレクトリの絶対パスを変形したもので、ここに**ユーザー名がそのまま入る**。

たとえば同じ`insights`というプロジェクトでも、マシンが違えばキーが変わる。

- `user2`のマシン→ `projects/-Users-user2-insights/`
- `user1`のマシン→ `projects/-Users-user1-insights/`

memoryは`projects/<エンコードした絶対パス>/memory/`に書かれるので、同じ`.claude`をsymlinkで共有しても、各マシンは自分のユーザー名ごとに別々のサブディレクトリに書く。結果として、片方で書いたmemoryをもう片方が読むことはない。セッション履歴も同じ理屈で分岐する。共有したつもりで、実体は分かれたままになる。

macOSではホームディレクトリのパスにユーザー名が必ず含まれるので、`~/dotfiles`のようなホーム配下を使う限り、このユーザー名はキーから消せない。

## おまけの罠: 絶対パスのsymlinkは別マシンで壊れる

もう1つ、共有対象の中にsymlinkが含まれる場合の罠がある。iCloud側の`.claude`を見ると、`CLAUDE.md`・`hooks`・`settings.json`自体が`/Users/user1/dotfiles/.claude/...`への絶対パスsymlinkになっていた。これは`user1`のマシンで張られたものなので、`user2`のマシンから参照すると解決先が存在せず、dangling（リンク切れ）になる。

設定をsymlinkで配る場合、リンクのターゲットを特定ユーザーの絶対パスで固定してはいけない。各マシンの`$HOME`を基準に、インストール時に張り直す必要がある。

## 対策

役割を「設定（共有したい）」と「ランタイム状態（共有してはいけない）」に分けて扱うのが要点になる。

### 設定はdotfiles＋gitで共有する

`CLAUDE.md`・`settings.json`・`hooks/`・`skills/`などは、iCloudではなくdotfilesリポジトリに置いてgitで共有する。各マシンでcloneし、symlinkはインストール時に各マシンの`$HOME/dotfiles`を基準に張り直す（[GNU Stow](https://www.gnu.org/software/stow/)や[chezmoi](https://www.chezmoi.io/)などのdotfiles管理ツール、あるいはセットアップスクリプト）。ターゲットを`/Users/<特定ユーザー>`で固定しないことが、前節のdangling回避になる。

### memoryを共有したいなら対象を絞る

memoryを複数マシンで一本化したい場合、ディレクトリ全体ではなくmemoryだけを狙う。やり方は2通りある。

1. **個別symlink**: 各マシンで`projects/<エンコードしたパス>/memory/`を、共有ストア（gitリポジトリ推奨、iCloudでも可）の同一フォルダにsymlinkする。プロジェクトごとに張る必要はあるが、パスキーの分岐を回避して中身を一本化できる。memory機能は渡されたパスにファイルを書くだけなので、symlinkで問題なく機能する。
2. **パスキーを揃える**: プロジェクトのコードをユーザー名非依存の共通パスに置く。macOSなら`/Users/Shared/`が両マシンで同名かつ書き込み可能なので、ここにリポジトリを置けばキーが一致し、memoryもセッション履歴も自然に統合される。ホーム配下を使う限りユーザー名がキーに混入するので、真に統合したいならこの方法が素直である。

#### どのmemoryを共有するか（種別で絞る）

共有対象を決める前に、memoryには「マシンに依存しないもの」と「チェックアウトに紐づくもの」が混ざっていることを踏まえたい。Claude Codeのmemoryは各ファイルのフロントマターに種別を持つ。専用のキーは`metadata.type`である。

```markdown
---
name: <slug>
description: <一行要約>
metadata:
  type: user | feedback | project | reference
---
```

種別ごとの性質は次のとおり。

- `user`（自分の属性・専門・好み）・`feedback`（進め方への指示や修正と、その理由）・`reference`（外部リソースへのポインタ。URL・ダッシュボード・チケット）は、**マシンに依存しない**。全マシンで一本化する価値が高い。
- `project`（進行中の作業・目標・制約）は、**本文に絶対パスを含みやすく**、チェックアウトに結合する。素朴に共有すると、別マシンではパスがずれて意味をなさない。

したがって、まず`user`・`feedback`・`reference`を共有対象にし、`project`はローカルに残す（共有したいなら`~`相対にパスを書き換えてから入れる）のが安全である。

なお、memoryには自分の属性や作業内容といった私的な情報が入る。共有ストアは**publicなdotfilesリポジトリには置かず、必ずprivateなリポジトリに分ける**こと。

### 状態ファイルは共有しない

`history.jsonl`・`sessions/`・`session-env/`・`shell-snapshots/`・`file-history/`・`cache/`系・`telemetry/`などは、iCloudや共有ストアには置かない。各マシンローカルに残す。

## 実装例: home-managerで配線する

筆者の環境は[home-manager](https://github.com/nix-community/home-manager)（Nix）なので、これでsymlinkを各マシンの`$HOME`基準に張る。Stow・chezmoi・セットアップスクリプトでも考え方は同じで、要点は3つである。

- **symlinkのターゲットを`$HOME`から組み立て、ユーザー名をハードコードしない**。これで前述のdangling（別マシンでのリンク切れ）を防ぐ。home-managerなら`config.home.homeDirectory`を使う。
- **memoryは`mkOutOfStoreSymlink`で実体へ直接symlinkする**。memoryはセッション中に書き込まれるので、Nix store経由（読み取り専用のコピー）ではなく、書き込める実体を指す必要がある。chezmoiならsymlink属性、Stowならそのまま実体を指すので同じ性質が得られる。
- **publicなdotfilesと、privateなmemoryストアを分ける**。設定はpublicな`dotfiles`配下、memoryは別のprivateリポジトリ（例: `memories`）配下に置き、各マシンの`$HOME`にcloneする。

```nix
{ config, lib, ... }:
let
  home = config.home.homeDirectory;
  link = config.lib.file.mkOutOfStoreSymlink;

  dotfiles = "${home}/dotfiles";   # public: 設定
  store    = "${home}/memories";   # private: memory

  # 絶対パスをClaude Codeのprojectsキーへエンコードする。
  # 区切りや記号を - に潰す（厳密な規則は手元の projects/ を見て確認すること）。
  toKey = path: lib.replaceStrings [ "/" "." " " "~" ] [ "-" "-" "-" "-" ] path;
  linkMemory = rel:
    let key = toKey "${home}/${rel}";
    in {
      name = ".claude/projects/${key}/memory";
      value.source = link "${store}/${rel}";
    };

  # memoryを共有したいプロジェクトを $HOME 相対で列挙する。
  sharedProjects = [
    "ghq/github.com/<you>/<repo>"
    # ...
  ];
in {
  home.file = lib.listToAttrs (map linkMemory sharedProjects) // {
    # 設定レイヤー（編集を即反映したいので out-of-store symlink）
    ".claude/CLAUDE.md".source     = link "${dotfiles}/.claude/CLAUDE.md";
    ".claude/settings.json".source = link "${dotfiles}/.claude/settings.json";
    ".claude/hooks".source         = link "${dotfiles}/.claude/hooks";
  };
}
```

`projects/<key>/`の下にはセッション履歴も同居するが、home-managerが管理するのは`memory`の葉だけなので、兄弟の状態ファイルには干渉しない。キーはユーザー名を含めて`$HOME`から生成されるため、マシンが違ってもそのマシンの正しいキーに解決される。`metadata.type`が`project`のものはこの配線に乗せず、`user`/`feedback`/`reference`だけを共有ストアに入れる運用にする。

設定そのものに他人に見せたくない情報（`hooks`の中身など）を含むなら、`.claude`ごとprivateに切り出し、上記の`dotfiles`を指す部分をそのprivateリポジトリに置き換えてもよい。

### 2台目への持ち込み（マージ）

複数マシンで運用を始めるときは、片方を「正」にしてからもう片方を合流させる。

1. メインマシンで上記の配線をし、privateなmemoryストアを用意して、既存のmemoryをストアへ移動してpushする。
2. 2台目では、**symlinkを張る前に**そのマシンの既存`projects/<key>/memory/`をストアへマージする。symlinkは「リンク先で実体を上書き」ではなく「実体を隠す」挙動なので、先にローカルのmemoryをストアへ取り込まないと、2台目固有のmemoryが見えなくなる。
3. マージしてpushしたら、2台目でhome-managerを適用する。これで両マシンが同じストアを指す。

## まとめ

|対象|例|扱い|
|---|---|---|
|設定| `CLAUDE.md`・`settings.json`・`skills/`・`hooks/` | dotfiles＋gitで共有。symlinkは各`$HOME`基準で張り直す|
| memory | `projects/<path>/memory/` |対象を絞ってsymlink、またはパスキーを揃えて統合|
|状態| `history.jsonl`・`sessions/`・各種cache |共有しない（ローカルに残す）|

symlinkの機構自体は問題ないが、`~/.claude`を丸ごとiCloudに同期すると内容の整合性が2系統で崩れる。iCloudの同期競合と、`projects/`の絶対パスキーによるmemoryの分岐である。したがって丸ごと同期は避け、設定はdotfilesで共有し、memoryは対象を絞って共有する。状態ファイルは各マシンローカルに残す。
