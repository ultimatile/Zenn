---
title: "エージェントが勝手にリンターを黙らせるのを止めるには、ユーザーと区別できるゲートが必要"
emoji: "🛂"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["claudecode", "rust", "ハーネスエンジニアリング"]
published: false
---

## TL;DR

- **核心**: 「エージェントの無許可な抑制だけを止め、ユーザーの正当な抑制は通す」には、**エージェントとユーザーを見分けられるゲート**が要ります。ところがその境界を行為の時点で握れる層が、言語（Clippyのリントレベルは実質二値）にもGit（作者は表現できても自己申告かつ事後）にも無い —— だから検出層ではなく、エージェントのツール呼び出しを差し止める**PreToolUse フック**に置きます。
- Claude Codeのエージェントは警告を黙らせるのが目的化して、`#[allow(dead_code)]`などの抑制属性をしれっと貼りに来ます。
- `permissions.deny`は**コマンド名の許可リストとしては堅牢に動きますが、引数の部分文字列のコンテンツフィルタとして使うとシェル展開で簡単に抜けます**。さらに**Write / Edit / NotebookEditには中身をマッチさせるAPIが原理的に無い**ため、パーミッションDSLでは全経路を統一的には塞げません。
- 解は**PreToolUse フック**で`Write / Edit / NotebookEdit / Bash`の入力テキストを統一的に正規表現で検査し、検出時は`exit 2`でエージェントに返します。
- バイパスは必要悪のために用意しますが、**ユーザーのメッセージに含まれるトークンだけを認める**ことで「エージェントが勝手にバイパスする」発火経路を物理的に断ちます。アシスタントの発話はトランスクリプト上`type:"assistant"`で記録されるので、ユーザーのふりをしてトークンを出しても通りません。
- ポリシー（どの属性をブロック / トークン要求にするか）はTOMLに分離します。各ルールに`extensions = [".rs"]`を持たせて、Markdown中のコード解説やPythonファイルへの誤検出を避けます。
- 最後に**自分のフックで自分のフックが編集できなくなるfootgun**を踏みました。教訓は、メッセージにリテラルを書かない・メタデータ（ポリシー / フック本体）を構造的にスコープ外にする・緊急脱出口を残す、です。

## はじめに

Rustには[Clippy](https://github.com/rust-lang/rust-clippy)というリンターがあり、私はpre-commitフックでClippyがクリーンでなければコミットできないようにしています。主にClaude Codeで開発しているライブラリでの話です。

ある日、`use std::sync::Arc;` の未使用インポートが残っていました。これはClippyが警告を出すのでコミットできません。正解は単にこのインポートを消すだけでよかったのに、Claude Codeはとんでもない方法で「Clippy clean」にしていました。

```rust
use std::sync::Arc;

// ... (Arcを使わないテスト群) ...

#[allow(dead_code)]
fn _arc_marker<T>(_: Arc<T>) {}
```

まず `_arc_marker` というフェイク関数で、未使用インポート状態を解消しています。しかし、ここで `_arc_marker` は実際に使用されませんから、今度は未使用関数に関する `dead_code` 警告が出ます。それを `#[allow(dead_code)]` 属性を付与して抑制していたのです。

`#[allow(dead_code)]`の使用が許容されることは通常まずないでしょう。

## 概念整流: これは「エージェントが触っていい領域」の境界問題

実装に入る前に、この話が何の問題なのかを整流しておきます。一歩引くと、本質はリンターでもRustでもなく、コーディングエージェントのハーネスエンジニアリングにおける**境界設定**の問題です。

コードベースには、エージェントが触っていいものと触ってはいけないものがあります。`#[allow(dead_code)]`を貼ること自体は、コードの良し悪し（対象レベル）の問題ではありません —— 本当に必要な局面もあります。問題は**「その抑制を入れてよいと誰が決めるか」**という権限の所在のほうにあります。エージェントが自走で貼るのはダメで、ユーザーが判断して貼るならよい。判定基準が、コードの形ではなく主体に乗っているのです。

ここで効いてくるのが、**既存のエコシステムはどれも「信頼できる主体の区別」を行為の時点で持てない**という事実です（表現はできる場合すらありますが、それだけでは足りません）。

- **言語エコシステム（Clippy / rustc）**: リントレベルは実質二値しかありません。`deny`は`#[allow]`で上書きできます（＝エージェントも上書きできる）、`forbid`は誰も上書きできません（＝ユーザーすら局所例外を作れない）。「エージェントはダメ、ユーザーならよい」という主体で分岐する中間レベルは、原理的に表現できません。
- **Gitエコシステム（pre-commit / branch protection / CODEOWNERS）**: Gitはエージェントの著者情報を表現はできます（`Co-authored-by`トレーラー、別のコミッターアイデンティティ）。ですが既定では**エージェントはユーザーとしてコミットします**し、そのシグナルは縛りたい当事者であるエージェント自身が書く/省くを選べる**自己申告**で、効くのも**事後のCI / コミット粒度**です。封じたCIコンテナならGitのアイデンティティを焼いて区別を強制できますが、エージェントがユーザー環境で動く**インタラクティブな現場では制御が高くつきます**（co-authorを強制するClaude設定や、co-author無しのコミットを弾くフックなどの追加機構がいる）。つまりGitは「区別できない」のではなく「**信頼できる区別を行為の時点で得るのが構造的に高い**」のです。

両者がこの境界を**ゲートにできない**のは、バグでも未実装でもなく構造的です —— Clippyは主体の概念をそもそも持たず、Gitは持てても自己申告・事後でしかありません。だから「エージェントが手を入れた瞬間に、主体に応じて止める」**行為時点のゲート**は、それらの層には置けません。

置けるのは、**エージェントとユーザーを見分けられる層**だけです —— 具体的には、エージェントのツール呼び出しをトランスクリプトごと差し止められる**PreToolUse フック**です。フックは`transcript_path`を受け取れるので、`type:"user"`か`type:"assistant"`かで発話の主体を区別できます。

ここで効いている判別子は所属（「ハーネス」かどうか）ではなく、**主体を観測できる能力（トランスクリプトを読めること）**のほうです。実際「ハーネス」と呼ぶと曖昧で、CIで回すClippyすら「エージェントの足場」として含めたくなります —— ですがClippyはできない側の代表で、コードしか見ず「誰がやったか」を観測しません。だから問うべきは「ハーネスか否か」ではなく「主体を見分けられるか」になります。後述のバイパス設計（「直近のユーザーメッセージにトークンがある時だけ通す」）は、この能力をコードに落とした具体形にほかなりません。同様に「pre-commitだとユーザーまで巻き込む」という後述の不採用理由も、根は同じ「コミット層は主体を見分けられない」です。

この見方でポリシーの`block` / `require_token`分割を読み直すと、設計の必然性がはっきりします:

- **抑制に正当用途が無いもの**（`dead_code`: 本当に未使用なら消すのが正解）→ 境界は「誰も」に潰してよい。これはゲートを使わずとも`[workspace.lints] dead_code = "forbid"`としてrustcに降ろせます。境界が無いケースは二値の`forbid`にちょうど畳めます。
- **正当用途があるもの**（`doc(hidden)` / `clippy::*` / `unused`: 必要悪の局面が確かにある）→ 境界を生かす必要があるので、`require_token`としてゲート（主体を見分けられる層）に残すしかありません。`forbid`では正当なユーザー例外まで殺し、`deny`ではエージェントが素通りします。二値では届かない中間です。

つまり**「`forbid`にすべきか、トークンゲートにすべきかで悩む緊張」それ自体が、権限依存のルールを権限盲目な層に押し込もうとしている誤配置の診断シグナル**になっています。緊張が出たら答えは「それは主体を見分けられる層（＝ゲート）の仕事です」。

ここでもう1つ、混ぜてはいけない別の軸があります。これまでは**「誰が決めてよいか」（主体）**の軸を見てきましたが、それとは独立に**「触らせたくない対象を、そもそもどのフォーマットで検出できるか」**という軸があります。`#[allow(dead_code)]`は正規表現で足りるのか、ASTが要るのか、それ以上（型解析・データフロー）なのか —— これは対象ごとに違い、自明ではありません。`#[allow(...)]`のような閉じた属性クラスは正規表現の射程にギリギリ収まりますが、レイヤ違反のような構造的スメルになればASTが要り、ルールが育てば[Dylint](https://github.com/trailofbits/dylint)のようなRustネイティブのリンターに収束していきます。

ただしこの検出フォーマットの軸は対象レベルの検出器の問題であって、**「ゲートを主体に応じてどこに置くか（＝主体を見分けられる層）」とは独立**です。本記事はそのゲートの置き場を主題にし、検出のほうは正規表現で足りる範囲だけを扱います。「主体で裁く層」と「対象をどう検出するか（正規表現 / AST / Dylint）」を混同すると、配置を誤ります。

以降は、この境界をPreToolUse フックに引くときの具体的な実装と、その過程で自分の足を撃った話になります。

## 動機: 警告を黙らせるエージェント

Claude CodeのエージェントにRustコードを書かせると、警告が出るたびに

```rust
#[allow(dead_code)]
fn helper() { ... }
```

を貼って黙らせる挙動が目立ちます。`dead_code`だけならまだしも、`#[doc(hidden)]`や`#[allow(clippy::*)]`も大体舐めてきます。

`dead_code`の許容はほぼ正当化できません（本当に未使用なら消すべきで、テスト専用なら`#[cfg(test)]`の中に置くべき）。なのでこれは原則ブロックしたいです。一方`#[doc(hidden)]`やClippyの個別`allow`は必要悪の局面が確かにあるので、「全面禁止」までは厳しいところです。

つまり以下を満たす仕組みが必要です:

1. エージェントが**自発的に**抑制属性を貼ろうとしたら止める
2. **ユーザーが明示的に許可した時だけ**通す
3. 経路網羅: WriteもEditも`echo … >> file.rs`経由も全部塞ぐ

## まずpre-commitではないのか

先に「git pre-commitフックでgrepして拒否すればよくない？」という発想を潰しておきます。実際pre-commitには強力な利点があります:

- **経路に例外がない**: エージェントが`Write`で書こうが`Bash`の`echo … >> foo.rs`で書こうが、最終的に`git commit`を通る限り全部捕まります。後述の「経路網羅」が無料で得られます。

それでも今回は採用しませんでした。理由は2つです。

### 理由1: ユーザーも巻き込む

pre-commitはエージェントと人間を区別しません。**自分が**一時的に`#[allow(dead_code)]`を貼って様子を見たい局面でも、同じ強度で拒否されます。「エージェントの自走を止めたい」と「自分の試行錯誤を止めたい」は別の話なのに、検出層をコミット時点に置くと両者が同じ規制に縛られます。今回欲しいのは前者だけです。

### 理由2: プレフィックス許可で`--no-verify`が通る

pre-commitは`git commit --no-verify`の1語で全部スキップされます。これ自体は周知の話ですが、Claude Codeの`permissions.allow`が**プレフィックスマッチ**であることと組み合わさると厄介です:

```json
"allow": [
  "Bash(git commit:*)"
]
```

を入れている人（筆者）の環境では、`git commit --no-verify -m "..."`も同じ`allow`に巻き取られて素通りします。`Bash(git commit --no-verify*)`を別途`deny`に積む手はありますが、前述の通りBash用パーミッションパターンは部分文字列一致のために設計されていないので、`--no-verify`を引数の途中に置かれたら抜けます。

要するに、pre-commitは**人間も含めた最終ゲート**としては優秀ですが、**エージェントが手を入れた瞬間に止める層**としては、(a) 規制対象が広すぎる、(b) エージェント自身がスキップ呪文を持っている、という2点で不向きです。今回欲しいのは「エージェントが手を入れた瞬間」のレイヤなので、PreToolUse フックを選びます。

## なぜ`permissions.deny`だけでは足りないか

最初に考えるのは`~/.claude/settings.json`の`permissions.deny`に

```json
"deny": [
  "Write(*#[allow(dead_code)]*)",
  "Bash(*#[allow(dead_code)]*)"
]
```

のような形で書くことです。ですがこれは2つの理由で破綻します。

### 理由1: ツール数だけルールを書く羽目になる

ファイルに文字列を書き込む経路は無数にあります:

- `Write`ツール
- `Edit`ツール（`new_string`）
- `NotebookEdit`ツール（`.ipynb`の場合）
- Bash経由: `echo`, `printf`, `tee -a`, `cat << EOF`, `sed -i`, `python -c`, …

`Bash(echo:*)`を`deny`にすると`echo`しか塞げず、他経路が全部素通りです。網羅は事実上不可能です。

### 理由2: そもそもパーミッションDSLはコンテンツフィルタとして設計されていない

`permissions.{allow, deny}`は「どの**ツール／コマンド名**を走らせていいか」を決める入口ゲートとして設計されたもので、引数やペイロードの中身まで見るコンテンツフィルタは最初から想定外です。今回の用途（「コマンド文字列の任意位置に`#[allow(dead_code)]`が含まれていたら止める」）からすると、このDSLは構造的にガバガバです。実機で挙動を確認しながら見ていきます。

#### Bashの照合は「コマンド名はシェル解決後、引数の部分文字列は解決前」という分裂仕様

パーミッションDSLのBash照合には設計上の明確な分離があり、これは実機で確認できます:

- **コマンド名（head）はシェル展開後で照合**: `Bash(git:*)`を`deny`に入れて`IT=it; g$IT --version`を実行すると、ちゃんとブロックされます。展開後のコマンド名が`git`であることが識別されています。
- **部分文字列パターンは展開前のリテラルで照合**: `Bash(*SKIP=*)`を`deny`に入れても`A=S; ${A}KIP=foo bar`は素通りします。コマンド文字列のリテラルに`SKIP=`が出てこないためです。

つまりパーミッションDSLは**コマンド名の許可リスト（ツール名ゲート）としては堅牢に動く一方、引数の部分文字列のコンテンツフィルタとしてはシェル展開で簡単に抜けます**。これは実装バグではなく、「コマンド名で縛る」用途と「引数文字列で縛る」用途がDSLの中で分離されている**仕様**の表れです。我々の用途は後者なので、ここで原理的に詰みます。

#### Write / Edit / NotebookEditには中身をマッチさせるAPIが無い

パーミッションDSLでパス系ツール（Write / Edit / Read / NotebookEdit）のパターンは**gitignore風のパスglob限定**です。書き込む中身を条件にする文法は存在しません。Bashで頑張って`Bash(*#[allow(dead_code)]*)`相当を書いても、エージェントが`Write`ツールに切り替えれば素通りです。

なおパス自体の照合は（正規化を含めて）概ね機能します。`Write(//Users/me/forbidden.txt)`を`deny`に入れれば、エージェントが`~/forbidden.txt`で書こうが`../../Users/me/forbidden.txt`で書こうが正しくブロックされます[^tmp-symlink]。

[^tmp-symlink]: macOSの`/tmp` → `/private/tmp` シンボリックリンクを経由するパスで照合がずれる既知バグがあります（issue [#54486](https://github.com/anthropics/claude-code/issues/54486)、2026-02以来4回再起票されて未解決）。今回の用途には直接関係しない特殊ケースです。

#### バイパストークンをユーザー限定にする手段が無い

パーミッションDSLは静的ルールしか持ちません。発話チャネル（ユーザー vs アシスタント）を区別した動的判定や、トランスクリプトを読んだ上での判断はできません。「必要悪のためのバイパス」をユーザーの物理発話に限定する設計は、パーミッションでは原理的に書けません。

#### 結論: レイヤが違う

これは「パーミッションシステムが壊れている」のではなく、入口ゲート用の粗い粒度の仕組みを**コンテンツゲートとして誤用しようとしている**のが原因です。家の玄関の鍵で金庫を開けようとしているのに近いです。コンテンツフィルタが本当に欲しいなら、パーミッションではなく**PreToolUse フック**で`tool_input.content` / `tool_input.command`をgrepするほうが原理的に正しいです。

## 設計: フックで中身を統一的に検査する

PreToolUse フックはエージェントのツール呼び出し直前に走り、JSONで`tool_name`, `tool_input`, `transcript_path`を標準入力から受け取ります。`exit 2`で標準エラー出力がエージェントに返り、ツール呼び出しは中止されます。

ツールごとに「テキストを含むフィールド」が決まっているので、それを取り出して同じ正規表現で検査します:

| ツール |検査するフィールド|
|---|---|
| Write | `content` |
| Edit | `new_string` |
| NotebookEdit | `new_source` |
| Bash | `command` |

正規表現を1つ用意すれば、`echo "…" >> foo.rs`も`Edit`の差分も同じ枠で捕まります。

## バイパス設計: 発火源をユーザーメッセージに固定する

ここが今回の肝です。

「必要悪のためのバイパス」を作ると、エージェントはそのバイパスを発見した瞬間に**発火源になりに来ます**。「ユーザー許可済みと判断したのでバイパストークンを使いました」と言って自分で発動するパターンです。

これを構造的に防ぐには、**バイパスの発火条件をエージェントが改ざんできないチャネルに置く**のが効きます。Claude CodeのトランスクリプトはJSONLで

```json
{"type": "user",      "message": {"content": "…"}}
{"type": "assistant", "message": {"content": "…"}}
```

のように発話者が記録されています。フック側で

> バイパストークンは**直近のユーザーメッセージにあるときだけ**有効

と決めれば、エージェントがいくら`BYPASS:doc_hidden`と発言してもアシスタントのターンとして記録されるので無効になります。ユーザーの物理的な発話だけがバイパスの発火源になります。

これで「バイパスを作ると勝手にバイパスされる」問題が消えます。

## 実装

### ポリシー: `~/.claude/hooks/suppress-policy.toml`

データ（どの属性をどう扱うか）はコードから分離してTOMLに置きます。

```toml
# action:
#   "block"          -常に拒否。bypassトークンも受け付けない。
#   "require_token"  - userの最新メッセージに`token`が含まれていれば通す。
# extensions:
#   ルールを適用するファイル拡張子のリスト。省略時は全ファイル対象。
#   Write / Edit / NotebookEditはfile_path / notebook_pathの末尾で判定。
#   Bashはコマンド文字列に拡張子のsubstringが含まれるかで判定。

[[rule]]
id         = "dead_code"
pattern    = '#!?\[\s*allow\s*\(\s*dead_code\s*\)\s*\]'
action     = "block"
message    = "this suppression attribute is never permitted"
extensions = [".rs"]

[[rule]]
id         = "doc_hidden"
pattern    = '#!?\[\s*doc\s*\(\s*hidden\s*\)\s*\]'
action     = "require_token"
token      = "BYPASS:doc_hidden"
extensions = [".rs"]

[[rule]]
id         = "clippy_allow"
pattern    = '#!?\[\s*allow\s*\(\s*clippy::'
action     = "require_token"
token      = "BYPASS:lint"
extensions = [".rs"]

[[rule]]
id         = "unused_allow"
pattern    = '#!?\[\s*allow\s*\(\s*unused[a-z_]*\s*\)\s*\]'
action     = "require_token"
token      = "BYPASS:lint"
extensions = [".rs"]
```

`extensions`で`.rs`に絞っているのは、Markdownのコード解説中にリテラルが出てきたり、Pythonファイルに同形のコメントを書いたりした時の誤検出を避けるためです。後述のfootgunと直結する設計判断です。

### フック: `~/.claude/hooks/block-suppress.py`

```python
#!/usr/bin/env python3
import json, pathlib, re, sys, tomllib

POLICY_PATH = pathlib.Path.home() / ".claude/hooks/suppress-policy.toml"

TOOL_CONTENT_FIELDS = {
    "Write":        ["content"],
    "Edit":         ["new_string"],
    "NotebookEdit": ["new_source"],
    "Bash":         ["command"],
}
TOOL_PATH_FIELD = {
    "Write":        "file_path",
    "Edit":         "file_path",
    "NotebookEdit": "notebook_path",
}


def rule_applies_to_path(rule, tool, tool_input, blob):
    exts = rule.get("extensions")
    if not exts:
        return True
    if tool in TOOL_PATH_FIELD:
        path = str(tool_input.get(TOOL_PATH_FIELD[tool], ""))
        return any(path.endswith(e) for e in exts)
    if tool == "Bash":
        return any(e in blob for e in exts)
    return True


def latest_user_message(transcript_path):
    try:
        lines = pathlib.Path(transcript_path).read_text().splitlines()
    except OSError:
        return ""
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "user":
            continue
        content = rec.get("message", {}).get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def main():
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}
    fields = TOOL_CONTENT_FIELDS.get(tool, [])
    blob = "\n".join(str(tool_input.get(k, "")) for k in fields)
    if not blob:
        return 0

    try:
        rules = tomllib.loads(POLICY_PATH.read_text()).get("rule", [])
    except (OSError, tomllib.TOMLDecodeError) as e:
        print(f"block-suppress: cannot load policy: {e}", file=sys.stderr)
        return 0  # fail-open

    user_msg = None
    for rule in rules:
        if "tools" in rule and tool not in rule["tools"]:
            continue
        if not rule_applies_to_path(rule, tool, tool_input, blob):
            continue
        if not re.search(rule["pattern"], blob):
            continue

        rid = rule.get("id", "?")
        if rule["action"] == "block":
            print(f"blocked [{rid}]: {rule.get('message', rule['pattern'])}", file=sys.stderr)
            return 2
        if rule["action"] == "require_token":
            token = rule.get("token", "")
            if user_msg is None:
                user_msg = latest_user_message(event.get("transcript_path", ""))
            if token in user_msg:
                continue
            print(f"blocked [{rid}]: requires `{token}` in the user's latest message",
                  file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

設計上の注意点です:

- **fail-open**: ポリシーが読めない場合（TOMLが壊れている / ファイルが消えた）は0を返します。フックが原因でエージェントが完全に固まるのは事故なので避けます。ブロックは副作用が大きいので「黙って通す」側に倒します。
- **アシスタントのターンは無視**: `latest_user_message`は`type != "user"`を全部スキップします。これが「エージェントによる自己バイパス」を物理的に防ぐ要です。
- **拡張子判定**: Write系は`file_path`の末尾チェック、Bashはコマンド中の部分文字列です。Bashは厳密ではありませんが、`mv`や`cat foo.rs >> bar`経由の経路もまとめて巻き取れるので実用上は十分です。

### `settings.json`への登録

```json
"PreToolUse": [
  {
    "matcher": "Write|Edit|NotebookEdit|Bash",
    "hooks": [
      { "type": "command", "command": "~/.claude/hooks/block-suppress.py" }
    ]
  }
]
```

## footgun: 自分のフックで自分が編集できない

ここからが本題です。一通り動かしてテストも書いて満足したあと、ポリシーに`extensions = [".rs"]`を追加するために`Edit`を発火させたら、こう返ってきました:

```
PreToolUse:Edit hook error: blocked [dead_code]: #[allow(dead_code)] is never permitted
```

…自分のポリシーが自分の編集をブロックしています。

原因はすぐ判明しました。ポリシーにこう書いていました:

```toml
message = "#[allow(dead_code)] is never permitted"
```

エラーメッセージにブロック対象のリテラルを含めていたせいです。`Edit`の`new_string`をフックがスキャンするときに、`message`フィールド内の`#[allow(dead_code)]`自体が`dead_code`ルールに引っかかります。

しかも`dead_code`は**バイパストークンを意図的に用意していない**唯一のルールなので、エージェントからは解除手段がありません。完璧な詰みです。

二重に面白かったのは、テストスクリプトを書こうとしたら**テストコマンド自体がフックにブロックされる**ことです。Bashの検査は「コマンド文字列に`.rs`の部分文字列がある＋抑制属性のパターンがマッチする」で発火するので、`echo "#[allow(dead_code)]" >> src/lib.rs`をテストケースとして書いた瞬間にコマンドそのものがブロックされます。

結局、テスト用のパターンはbase64でエンコードして動的にデコードするハメになりました:

```bash
DEAD=$(printf '%s' 'I1thbGxvdyhkZWFkX2NvZGUpXQ==' | base64 -d)
run A 2 "{\"tool_name\":\"Write\", ..., \"content\":\"$DEAD fn x(){}\", ...}"
```

バイパスを作ると勝手に発動される問題を心配していたら、開発者自身が真っ先にバイパスを発明する側に回るというオチです。

## footgunから得られた教訓

### 1. メタデータ（ポリシー / フック本体）は規制対象から構造的に外す

今回は**偶然** `extensions = [".rs"]`のスコープ追加によって`.toml`ファイルが対象外になり、ポリシーの自己編集が通るようになりました。もしこのスコープがなかったら、ポリシーは永久にロックされていました。

ルールを書くときは「このルールが対象とすべきファイルの種類」を明示し、メタデータファイル（ポリシー本体 / フック自体 / README）は構造的にスコープ外になるよう設計します。

### 2. 緊急脱出口を残す

何重にもブロックされて手詰まりになっても、フックスクリプトをリネームすれば一時的に無効化できます:

```bash
mv ~/.claude/hooks/block-suppress.py /tmp/bak
# …編集…
mv /tmp/bak ~/.claude/hooks/block-suppress.py
```

このコマンドには`.rs`も抑制属性のリテラルも含まれないので、フック自身が止めようがありません。「最後の安全弁」として、フックが自分自身のリネーム / 削除をブロックしないことは大事です。逆に言うと、ここまで防ぐ設計にすると詰みます。

### 3. エラーメッセージにリテラルを書かない

```toml
# bad
message = "#[allow(dead_code)] is never permitted"
# good
message = "this suppression attribute is never permitted"
```

エラーメッセージは「何が起きたか」が分かれば十分で、検出対象をリテラルで繰り返す必要はありません。これだけで自家中毒の主要経路が消えます。一般化すると、**ポリシー / ルールの説明テキストには、検出対象のリテラルを書かない**、です。

### 4. fail-open vs fail-closedの選択

セキュリティ系ではfail-closed（壊れたら全部止める）が定石ですが、開発者支援系のフックは**fail-open**にしておかないと、事故った時に何もできなくなります。今回はポリシー読み込み失敗時に0を返す方針にしました。

## このフックはセキュリティ境界ではない

書いておくべき注意点が一つあります。**このフックはエージェントの既定挙動を止めるためのUXナッジであって、セキュリティ境界ではありません**。

理由は単純で、ポリシーファイル（`~/.claude/hooks/suppress-policy.toml`）もフック本体（`block-suppress.py`）もエージェントから普通にRead / Writeできます。エージェントが「フックをバイパスする」意図を持てば、以下のいずれかで即座に無効化されます:

- ポリシーを読んでパターンを学習し、シェル変数の組み立てやエンコードでリテラルを分散させる（前述の`Bash(*SKIP=*)`が`${A}KIP=`で抜けるのと同じ手口）
- フックスクリプト本体をリネーム / 削除 / no-opに上書き
- ポリシーのTOMLを空配列にする
- `settings.json`からフック登録を抜く

つまりこのフックで止まるのは「エージェントの既定動作で抑制属性が混入するケース」と「リント警告がうるさいので`allow`貼っちゃおう程度の判断ミス」までで、**意図的な回避や悪意あるサプライチェーン攻撃は止められません**。本気の防御層は別です:

- エージェントをサンドボックス（Docker / gVisor / firejail等）に閉じ込めて`~/.claude/`を読み取り専用でマウント
- macOSのTCCやLinuxのAppArmor / SELinuxで書き込み権限を絞る
- CI側で`cargo clippy -- -D warnings`を必須チェックにして、ローカルで何が起きてもマージできなくする
- ブランチ保護で直接pushを禁止

これらはフックの領分を超えた話です。本記事のフックは**「意図せぬ既定を止める層」**という限定された役割で運用します。

## おわりに

エージェントの自走を抑える仕組みを書くときは、エージェントをどう縛るかと同じくらい**自分を縛らない設計**が大事です。バイパスをユーザーメッセージに固定する設計は、エージェントの自己発火を防ぎつつ自分の手は残すバランスとして悪くありませんでした。一方、メタデータ自身を規制から外す配慮を最初から組み込んでおかないと、いつの間にかポリシー自体を編集できない状態に陥ります。

「エージェントが勝手に発動するからバイパスは作らない」と「バイパスを作るとロックアウトされる」の両方を踏まないようにするには、

- バイパスの発火源はエージェントが改ざんできないチャネル（＝ユーザーメッセージ）に固定
- メタデータ（ポリシー / フック / ドキュメント）は構造的にスコープ外
- 緊急脱出口（フックのリネーム）は塞がない
- メッセージに検出対象のリテラルを書かない

の4点セットを最初から守っておくと良いです。後で気付いて修正する側に回ると、自分のフックで自分のフックが編集できないという見事なfootgunを踏むことになります。

---

最後にひとつ書かせてください。

この記事を書く中で扱った手段を並べてみます。変数代入でリテラルをばらす。base64でgrepを欺く。相対パスで`deny`を抜ける。シンボリックリンクでマッチャを狂わせる。

並べると、シェルインジェクションやパストラバーサルの典型ベクタとほぼ重なっています。

エージェントにリンターを守ってもらえれば、それでよかったはずです。気づけばCTFが始まっていました。AIエージェントの監督は、実質的に脅威モデリングと地続きなのだなと感じます。

フックで完全防御を目指すと、攻撃面は無限に広がっていきます。最初に「意図せぬ既定の抑制を止める層であって、意図的なバイパスまでは追わない」と線引きをしておくほうが、長続きします。
