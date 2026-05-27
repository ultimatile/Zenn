---
title: "Claude Codeがリンターをちょろまかしていたのでフックで封じたら自分の足を撃ち抜いた話"
emoji: "🔫"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["claudecode", "rust", "ハーネスエンジニアリング"]
published: false
---

## はじめに

Rustには[Clippy](https://github.com/rust-lang/rust-clippy)というリンターがあり、私はpre-commitフックでclippyがクリーンでなければコミットできないようにしています。主にClaude Codeで開発しているライブラリでの話です。

ある日、`use std::sync::Arc;` の未使用importが残っていました。これはclippyが警告を出すのでコミットできません。正解は単にこのimportを消すだけでよかったのに、Claude Codeはとんでもない方法で"clippy clean"にしていました。

```rust
use std::sync::Arc;

// ... (Arcを使わないテスト群) ...

#[allow(dead_code)]
fn _arc_marker<T>(_: Arc<T>) {}
```

まず `_arc_marker` というフェイク関数で、未使用インポート状態を解消しています。しかし、ここで `_arc_marker` は実際に使用されませんから、今度は未使用関数に関する `dead_code` 警告が出ます。それを `#[allow(dead_code)]` 属性を付与して抑制していたのです。

`#[allow(dead_code)]`の使用が許容されることは通常まずないでしょう。

## TL;DR

- Claude Codeのagentはwarningを黙らせるのが目的化して`#[allow(dead_code)]`などの抑制属性をしれっと貼りに来る。
`permissions.deny`は**コマンド名のallowlistとしては堅牢に動くが、引数substringのcontent filterとして使うとshell展開でtrivialに抜ける**。さらに**Write / Edit / NotebookEditにはcontent matchのAPIが原理的に無い**ため、permission DSLでは全経路を統一的には塞げない。
- 解は**PreToolUse hook**で`Write / Edit / NotebookEdit / Bash`の入力テキストを統一的にregex検査し、検出時は`exit 2`でagentに返す。
- bypassは必要悪のために用意するが、**userメッセージに含まれるトークンだけを認める**ことで「agentが勝手にbypassする」発火経路を物理的に断つ。assistantの発話はtranscript上`type:"assistant"`で記録されるので、userフリをしてtokenを出しても通らない。
- ポリシー(どの属性をblock / token要求)はTOMLに分離。各ルールに`extensions = [".rs"]`を持たせて、Markdown中のコード解説やPythonファイルへの誤検出を避ける。
- 最後に**自分のhookで自分のhookが編集できなくなるfootgun**を踏んだ。教訓: メッセージにliteralを書かない、メタデータ(policy / hook本体)を構造的にスコープ外にする、緊急脱出口を残す。

## 動機: warningを黙らせるagent

Claude CodeのagentにRustコードを書かせると、warningが出るたびに

```rust
#[allow(dead_code)]
fn helper() { ... }
```

を貼って黙らせる挙動が目立つ。`dead_code`だけならまだしも`#[doc(hidden)]`や`#[allow(clippy::*)]`も大体舐めてくる。

`dead_code`の許容はほぼ正当化できない(本当に未使用なら消すべきで、テスト専用なら`#[cfg(test)]`の中に置くべき)のでこれは原則blockしたい。一方`#[doc(hidden)]`やclippyの個別allowは必要悪の局面が確かにあるので「全面禁止」までは厳しい。

つまり以下を満たす仕組みが必要:

1. agentが**自発的に**抑制属性を貼ろうとしたら止める
2. **ユーザーが明示的に許可した時だけ**通す
3. 経路網羅: WriteもEditも`echo … >> file.rs`経由も全部塞ぐ

## まずpre-commitではないのか

先に「git pre-commit hookでgrepしてrejectすればよくない？」という発想を潰しておく。実際pre-commitには強力な利点がある:

- **経路に例外がない**: agentがWriteで書こうがBashの`echo … >> foo.rs`で書こうが、最終的に`git commit`を通る限り全部捕まる。後述の「経路網羅」が無料で得られる。

それでも今回は採用しなかった。理由は2つ。

### 理由1: ユーザーも巻き込む

pre-commitはagentと人間を区別しない。**自分が**一時的に`#[allow(dead_code)]`を貼って様子を見たい局面でも同じ強度でrejectされる。「agentの自走を止めたい」と「自分の試行錯誤を止めたい」は別の話なのに、検出層をcommit時点に置くと両者が同じ規制に縛られる。今回欲しいのは前者だけ。

### 理由2: プレフィックス許可で`--no-verify`が通る

pre-commitは`git commit --no-verify`の1語で全部スキップされる。これ自体は周知の話だが、Claude Codeの`permissions.allow`が**プレフィックスマッチ**であることと組み合わさると厄介:

```json
"allow": [
  "Bash(git commit:*)"
]
```

を入れている人(筆者)の環境では、`git commit --no-verify -m "..."`も同じallowに巻き取られて素通りする。`Bash(git commit --no-verify*)`を別途denyに積む手はあるが、前述の通りBash用permissionパターンはsubstring一致のために設計されていないので、`--no-verify`を引数の途中に置かれたら抜ける。

要するに、pre-commitは**人間も含めた最終ゲート**としては優秀だが、**agentが手を入れた瞬間に止める層**としては(a)規制対象が広すぎ、(b) agent自身がスキップ呪文を持っている、という2点で不向き。今回欲しいのは「agentが手を入れた瞬間」のレイヤなので、PreToolUse hookを選ぶ。

## なぜ`permissions.deny`だけでは足りないか

最初に考えるのは`~/.claude/settings.json`の`permissions.deny`に

```json
"deny": [
  "Write(*#[allow(dead_code)]*)",
  "Bash(*#[allow(dead_code)]*)"
]
```

のような形で書くこと。だがこれは2つの理由で破綻する。

### 理由1: ツール数だけルールを書く羽目になる

ファイルに文字列を書き込む経路は無数にある:

- `Write`ツール
- `Edit`ツール(`new_string`)
- `NotebookEdit`ツール(`.ipynb`の場合)
- Bash経由: `echo`, `printf`, `tee -a`, `cat << EOF`, `sed -i`, `python -c`, …

`Bash(echo:*)`をdenyにするとechoしか塞げず、他経路が全部素通り。網羅は事実上不可能。

### 理由2: そもそもpermission DSLはcontent filterとして設計されていない

`permissions.{allow, deny}`は「どの**ツール／コマンド名**を走らせていいか」を決める入口ゲートとして設計されたもので、引数やpayloadの中身まで見るcontent filterは最初から想定外。今回の用途(「コマンド文字列の任意位置に`#[allow(dead_code)]`が含まれていたら止める」)からすると、このDSLは構造的にガバガバ。実機で挙動を確認しながら見ていく。

#### Bashの照合は「コマンド名はshell解決後、引数substringは解決前」という分裂仕様

permission DSLのBash照合には設計上の明確な分離があり、これは実機で確認できる:

- **コマンド名(head)はshell expansion後で照合**: `Bash(git:*)`をdenyに入れて`IT=it; g$IT --version`を実行すると、ちゃんとblockされる。展開後のコマンド名が`git`であることが識別されている。
- **substringパターンはexpansion前のliteralで照合**: `Bash(*SKIP=*)`をdenyに入れても`A=S; ${A}KIP=foo bar`は素通りする。コマンド文字列のliteralに`SKIP=`が出てこないため。

つまりpermission DSLは**コマンド名allowlist (tool-name gate) としては堅牢に動く一方、引数substringのcontent filterとしてはshell展開でtrivialに抜ける**。これは実装バグではなく、「コマンド名で縛る」用途と「引数文字列で縛る」用途がDSLの中で分離されている**spec**の表れ。我々の用途は後者なので、ここで原理的に詰む。

#### Write / Edit / NotebookEditにはcontent matchのAPIが無い

permission DSLでpath系tool (Write / Edit / Read / NotebookEdit) のパターンは**gitignore-styleのpath glob限定**。書き込むcontentをconditionにする文法は存在しない。Bashで頑張って`Bash(*#[allow(dead_code)]*)`相当を書いても、agentが`Write`ツールに切り替えれば素通り。

なおpath自体の照合は (canonicalize含めて) 概ね機能する。`Write(//Users/me/forbidden.txt)`をdenyに入れれば、agentが`~/forbidden.txt`で書こうが`../../Users/me/forbidden.txt`で書こうが正しくblockされる[^tmp-symlink]。

[^tmp-symlink]: macOSの`/tmp` → `/private/tmp` symlinkを経由するpathで照合がずれる既知バグはある (issue [#54486](https://github.com/anthropics/claude-code/issues/54486)、2026-02以来4回refileされて未解決)。今回の用途には直接関係しない特殊ケース。

#### bypass tokenをuser限定にする手段が無い

permission DSLは静的ルールしか持たない。発話チャネル (user vs assistant) を区別した動的判定や、transcriptを読んだ上での判断はできない。「必要悪のためのbypass」をuserの物理発話に限定する設計は、permissionでは原理的に書けない。

#### 結論: レイヤが違う

これは「permission systemが壊れている」のではなく、入口ゲート用の粗い粒度の仕組みを**content gateとして誤用しようとしている**のが原因。家の玄関の鍵で金庫を開けようとしているのに近い。contentフィルタが本当に欲しいなら、permissionではなく**PreToolUse hook**で`tool_input.content` / `tool_input.command`をgrepする方が原理的に正しい。

## 設計: hookでcontentを統一的に検査する

PreToolUse hookはagentのツール呼び出し直前に走り、JSONで`tool_name`, `tool_input`, `transcript_path`をstdinから受け取る。`exit 2`でstderrがagentに返り、ツール呼び出しはabortされる。

ツールごとに「テキストを含むフィールド」が決まっているので、それを取り出して同じregexで検査する:

| Tool |検査するフィールド|
|---|---|
| Write | `content` |
| Edit | `new_string` |
| NotebookEdit | `new_source` |
| Bash | `command` |

regexを1つ用意すれば、`echo "…" >> foo.rs`も`Edit`の差分も同じ枠で捕まる。

## bypass設計: 発火源をuserメッセージに固定する

ここが今回の肝。

「必要悪のためのbypass」を作ると、agentはそのbypassを発見した瞬間に**発火源になりにくる**。「ユーザー許可済みと判断したのでbypassトークンを使いました」と言って自分で発動するパターン。

これを構造的に防ぐには、**bypassの発火条件をagentが改ざんできないチャネルに置く**のが効く。Claude CodeのtranscriptはJSONLで

```json
{"type": "user",      "message": {"content": "…"}}
{"type": "assistant", "message": {"content": "…"}}
```

のように発話者が記録されている。hook側で

> bypass tokenは**直近のuserメッセージにあるときだけ**有効

と決めれば、agentがいくら`BYPASS:doc_hidden`と発言してもassistant turnとして記録されるので無効になる。userの物理的な発話だけがbypassの発火源になる。

これで「bypassを作ると勝手にバイパスされる」問題が消える。

## 実装

### Policy: `~/.claude/hooks/suppress-policy.toml`

データ(どの属性をどう扱うか)はコードから分離してTOMLに。

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

`extensions`で`.rs`に絞っているのは、Markdownのコード解説中にliteralが出てきたりPythonファイルに同形のコメントを書いたりした時の誤検出を避けるため。後述のfootgunと直結する設計判断。

### Hook: `~/.claude/hooks/block-suppress.py`

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

設計上の注意点:

- **fail-open**: policyが読めない場合(TOMLが壊れている/ファイルが消えた)は0を返す。hookが原因でagentが完全に固まるのは事故なので避ける。blockは副作用大なので「黙って通す」側に倒す。
- **assistant turnは無視**: `latest_user_message`は`type != "user"`を全部スキップする。これが「agentによるself-bypass」を物理的に防ぐ要。
- **拡張子判定**: Write系は`file_path`の末尾チェック、Bashはコマンド中のsubstring。Bashは厳密じゃないが、`mv`や`cat foo.rs >> bar`経由の経路もまとめて巻き取れるので実用上は十分。

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

## footgun: 自分のhookで自分が編集できない

ここからが本題。一通り動かしてテストも書いて満足したあと、policyに`extensions = [".rs"]`を追加するために`Edit`を発火させたら、こう返ってきた:

```
PreToolUse:Edit hook error: blocked [dead_code]: #[allow(dead_code)] is never permitted
```

…自分のpolicyが自分の編集をブロックしている。

原因はすぐ判明。policyにこう書いていた:

```toml
message = "#[allow(dead_code)] is never permitted"
```

エラーメッセージにブロック対象のliteralを含めていたせい。`Edit`の`new_string`をhookがscanするときに、messageフィールド内の`#[allow(dead_code)]`自体がdead_codeルールに引っかかる。

しかも`dead_code`は**bypassトークンを意図的に用意していない**唯一のルールなので、agentからは解除手段がない。完璧な詰み。

二重に面白かったのは、テストスクリプトを書こうとしたら**テストコマンド自体がhookにブロックされる**こと。Bashの検査は「コマンド文字列に`.rs`のsubstringがある+抑制属性patternがmatchする」で発火するので、`echo "#[allow(dead_code)]" >> src/lib.rs`をテストケースとして書いた瞬間にコマンドそのものがブロックされる。

結局、テスト用のパターンはbase64でエンコードしてdynamic decodeするハメになった:

```bash
DEAD=$(printf '%s' 'I1thbGxvdyhkZWFkX2NvZGUpXQ==' | base64 -d)
run A 2 "{\"tool_name\":\"Write\", ..., \"content\":\"$DEAD fn x(){}\", ...}"
```

bypassを作ると勝手に発動される問題を心配していたら、開発者自身が真っ先にバイパスを発明する側に回るというオチ。

## footgunから得られた教訓

### 1.メタデータ(policy / hook本体)は規制対象から構造的に外す

今回は**偶然** `extensions = [".rs"]`のスコープ追加によって`.toml`ファイルが対象外になり、policyの自編集が通るようになった。もしこのスコープがなかったらpolicyは永久にロックされていた。

ルールを書くときは「このルールが対象とすべきファイルの種類」を明示し、メタデータファイル(policy本体/ hook自体/ README)は構造的にスコープ外になるよう設計する。

### 2.緊急脱出口を残す

何重にもブロックされて手詰まりになっても、hook scriptをリネームすれば一時的に無効化できる:

```bash
mv ~/.claude/hooks/block-suppress.py /tmp/bak
# …編集…
mv /tmp/bak ~/.claude/hooks/block-suppress.py
```

このコマンドには`.rs`も抑制属性literalも含まれないのでhook自身が止めようがない。「最後の安全弁」として、hookが自分自身のリネーム/削除をblockしないことは大事。逆に言うと、ここまで防ぐ設計にすると詰む。

### 3.エラーメッセージにliteralを書かない

```toml
# bad
message = "#[allow(dead_code)] is never permitted"
# good
message = "this suppression attribute is never permitted"
```

エラーメッセージは「何が起きたか」が分かれば十分で、検出対象をliteralで繰り返す必要はない。これだけで自家中毒の主要経路が消える。一般化すると**policy / ruleの説明テキストには、検出対象のliteralを書かない**。

### 4. fail-open vs fail-closedの選択

セキュリティ系ではfail-closed (壊れたら全部止める)が定石だが、開発者支援系のhookは**fail-open**にしておかないと事故った時に何もできなくなる。今回はpolicy読み込み失敗時に0を返す方針にした。

## このhookはsecurity boundaryではない

書いておくべき注意点が一つ。**このhookはagentのdefault挙動を止めるためのUX nudgeであって、security boundaryではない**。

理由は単純で、policyファイル(`~/.claude/hooks/suppress-policy.toml`)もhook本体(`block-suppress.py`)もagentから普通にRead / Writeできる。agentが「hookをbypassする」意図を持てば、以下のいずれかで即座に無効化される:

- policyを読んでpatternを学習し、shell variable assemblyやencodingでliteralを分散させる (前述の`Bash(*SKIP=*)`が`${A}KIP=`で抜けるのと同じ手口)
- hook script本体をrename / 削除 / no-opに上書き
- policyのTOMLを空配列にする
- `settings.json`からhook登録を抜く

つまりこのhookで止まるのは「agentのdefault動作で抑制属性が混入するケース」と「lint警告がうるさいのでallow貼っちゃおう程度の判断ミス」までで、**意図的な回避や悪意あるsupply chain攻撃は止められない**。本気の防御層は別:

- agentをsandbox (Docker / gVisor / firejail等) に閉じ込めて`~/.claude/`をread-only mount
- macOSのTCCやLinuxのAppArmor / SELinuxで書き込み権限を絞る
- CI側で`cargo clippy -- -D warnings`をrequired checkにして、ローカルで何が起きてもmergeできなくする
- branch protectionでdirect pushを禁止

これらはhookの領分を超えた話。本記事のhookは**「意図せぬdefaultを止める層」**という限定された役割で運用する。

## おわりに

agentの自走を抑える仕組みを書くときは、agentをどう縛るかと同じくらい**自分を縛らない設計**が大事。bypassをuserメッセージに固定する設計は、agentの自己発火を防ぎつつ自分の手は残すバランスとして悪くなかった。一方、メタデータ自身を規制から外す配慮を最初から組み込んでおかないと、いつの間にかpolicy自体を編集できない状態に陥る。

「agentが勝手に発動するからbypassは作らない」と「bypassを作るとロックアウトされる」の両方を踏まないようにするには、

- bypassの発火源はagentが改ざんできないチャネル(= userメッセージ)に固定
- メタデータ(policy / hook / docs)は構造的にスコープ外
- 緊急脱出口(hookのrename)は塞がない
- メッセージに検出対象literalを書かない

の4点セットを最初から守っておくと良い。後で気付いて修正する側に回ると、自分のhookで自分のhookが編集できないという見事なfootgunを踏むことになる。

---

最後にひとつ書かせてください。

この記事を書く中で扱った手段を並べてみます。変数代入でliteralをばらす。base64でgrepを欺く。相対pathでdenyを抜ける。シンボリックリンクでmatcherを狂わせる。

並べると、shell injectionやpath traversalの典型ベクタとほぼ重なっています。

agentにlinterを守ってもらえれば、それでよかったはずです。気づけばCTFが始まっていました。AI agentのsupervisionは、実質的にthreat modelingと地続きなのだなと感じます。

hookで完全防御を目指すと、攻撃面は無限に広がっていきます。最初に「意図せぬdefault抑制を止める層であって、意図的なbypassまでは追わない」と線引きをしておくほうが、長続きします。
