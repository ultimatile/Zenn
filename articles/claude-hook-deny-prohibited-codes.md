---
title: "エージェントが勝手にリンターを黙らせるのを止めるには、ユーザーと区別できるゲートが必要"
emoji: "🛂"
type: "tech" # tech: 技術記事/ idea: アイデア
topics: ["claudecode", "rust", "ハーネスエンジニアリング"]
published: false
register: almost
---

## TL;DR

- Claude Code（以下CC）が警告潰しに`#[allow(dead_code)]`などの抑制属性を勝手に貼る。これを確率的なプロンプト指示ではなく決定的に止めたい。
- やりたいのは主体での分岐（エージェントの自走を止め、ユーザー許可だけ通す）。だが主体を見分けられるのは、基本的に**エージェント境界のツール（PreToolUseフック）だけ**だ。リント設定やコミットゲートでは表現できない。
- CCのトランスクリプトはuser/assistantを区別して記録する。これを使い「バイパストークンが直近のユーザーメッセージにあるときだけ通す」**トークンベースのフック**にすれば、エージェントは自己バイパスできなくなる。
- 検査が**コード編集の瞬間**（`Write`／`Edit`／`Bash`）に走るので、コミットまで気づかず手戻りする事態を避けられる。
- 設定ファイルやフック本体までエージェントに編集させる構成では、自分のフックで自分を撃つfootgunに注意（メタデータはスコープ外・エラーメッセージに検出対象のリテラルを書かない・非常口を残す）。

## はじめに

Claude CodeでRustライブラリを開発しているときの話です。Rustには[Clippy](https://github.com/rust-lang/rust-clippy)というリンターがあり、私は[pre-commit](https://github.com/pre-commit/pre-commit)フックでClippyがクリーンでなければコミットできないようにしています。

ある日、`use std::sync::Arc;`の未使用インポートが残っていました。このままではClippyが警告を出し、pre-commitフックに弾かれてコミットできません。コミットを通すには単にこのインポートを消すだけでよかったのに、CCは以下のようなとんでもない方法で「Clippy clean」にしていました。

```rust
use std::sync::Arc;

// ... (Arcを使わないテスト群) ...

#[allow(dead_code)]
fn _arc_marker<T>(_: Arc<T>) {}
```

まず`_arc_marker`というダミー函数で未使用インポート状態を解消しています。すると今度は`_arc_marker`自体が未使用函数になって`dead_code`警告が出るので、それを`#[allow(dead_code)]`で抑制しています。本当に未使用なら消すだけでよかったインポートを、二段重ねの小細工で「警告は出ていない」状態に偽装したわけです。

こうした「警告を黙らせること自体が目的化した」挙動は`dead_code`に限りません。CCにコードを書かせていると、`#[doc(hidden)]`やClippyの個別`#[allow(clippy::*)]`もよく貼ってきます。

ここで厄介なのは、抑制属性が一律に悪いわけではない点です。`dead_code`の許容はほぼ正当化できません（本当に未使用なら消すべきです）。一方`#[doc(hidden)]`やClippyの個別`allow`には必要悪の局面があります。たとえば`doc(hidden)`は、諸事情でパブリックにするしかない函数をドキュメント上から隠すための属性で、原則は避けたいが事情があれば使う、という位置づけです。

つまり欲しいのは、属性の有無ではなく**誰がそれを入れたか**で分岐するゲートです。次の3つを満たす必要があると考えられます。

1. エージェントが自発的に抑制属性を貼ろうとしたら止める
2. ユーザーが明示的に許可したときだけ通す
3. 経路網羅：`Write`も`Edit`も`echo … >> file.rs`経由もできるだけ全部塞ぐ

プロンプトで「やむを得ない場合を除いて使うな」と指示するのも一定の効果はありますが、あくまで確率的な挙動で、指示を守らないコードが生成される可能性はゼロになりません。だから決定的なハーネスで制御したい、というのがモチベーションです。

## リント設定とコミットゲートでは不十分

手近なリント設定と前述のpre-commitなどのコミットゲートで制御できるか考えてみます。**行為の時点で早く効くか**と**ユーザーとエージェントを見分けられるか**の2軸で見ると、どちらも不十分であることを以下で述べます。

### リント設定: 早いがユーザー許可を表現できない

まず思いつくのはClippyの設定です。`dead_code`のように正当用途が無いものは、以下のように`Cargo.toml`で`forbid`を設定すれば全面的に禁止できます[^ws-lints]。

```toml:Cargo.toml
[workspace.lints.rust]
dead_code = "forbid"
```

[^ws-lints]: ワークスペースでは、これはroot側の宣言で、各メンバーの`Cargo.toml`で`[lints]`テーブルに`workspace = true`を指定して初めて継承される。

`forbid`は誰も`#[allow]`で上書きできないので、`dead_code`はこれで解決します（実際そう設定しています）。ですが`forbid`は二値で、ユーザーの局所的な例外まで殺します。`doc(hidden)`のような必要悪には使えません。かといって一段弱い`deny`（`dead_code = "deny"`）にしても、`#[allow]`をコードに書き足せば打ち消せてしまいます。冒頭の`_arc_marker`がまさにこの状況で、`deny`にしたところで何も解決しません。

リント設定は行為の時点（コードが書かれる瞬間）に効くので早いものの、「ユーザーが許可した例外だけ通す」を表現できません。`forbid`なら例外ゼロ、`deny`の例外（`#[allow]`）は誰でも書けて、その中間（ユーザーだけ許可）に当たるレベルが無いからです。

### コミット・PRゲート: 主体は区別できるが遅すぎる

それなら、git pre-commitフックで`grep`して弾くのはどうでしょうか。pre-commitには強力な利点があります。`Write`で書こうが`Bash`の`echo … >> foo.rs`で書こうが、`git commit`を通る限り全部捕まるので、経路網羅が無料で手に入ります。主体の区別も、封じたCIコンテナでGitのアイデンティティを焼けば原理的には可能です。

それでも本題には不向きです。理由は2つあります。

1つ目は遅いことです。pre-commitはコミット粒度で発火するので、`doc(hidden)`が多くの変更の土台になっていたら手戻りが大きくなります。いつ混入するか、つまり`Write`の瞬間に弾けるのがベストです。

2つ目はバイパスが緩く、しかもユーザーを巻き込むことです。pre-commitは`git commit --no-verify`の1語で全部スキップされます。これ自体は周知ですが、CCの`permissions.allow`がプレフィックスマッチなので、`Bash(git commit:*)`を許可している環境（筆者です）では`git commit --no-verify -m "..."`も同じ`allow`に巻き取られて素通りします。エージェント自身がスキップ呪文を持っているわけです。一方でpre-commitはユーザーとエージェントを区別しないので、自分が一時的に`#[allow(dead_code)]`を貼って様子を見たい局面でも同じ強度で拒否されます。インタラクティブな現場で主体を区別させようとすると追加の機構（co-author強制など）が要り、コストに見合いません。

要するに、リント設定は早いがユーザー許可を表現できず、コミットゲートは主体を区別できても遅くて緩いのです。欲しいのは**行為の時点で早く効き、かつ主体を見分けられる層**です。

## PreToolUse フックに置く

そのレイヤをCCで探すと、まずナイーブに思いつくのは`permissions.deny`です。CCの設定ファイル`~/.claude/settings.json`に

```json
"deny": [
  "Write(*#[allow(dead_code)]*)",
  "Bash(*#[allow(dead_code)]*)"
]
```

のように書けないか、という発想です。ですがこれは経路網羅の点で破綻します。CCの`permissions.{allow, deny}`は「どのツール／コマンド名を走らせてよいか」を決める入口ゲートで、引数やペイロードの中身を見るコンテンツフィルタとして設計されていないためです。実際、Bashの部分文字列照合はシェル展開前のリテラルに対して行われるので、`Bash(*SKIP=*)`を`permissions.deny`に入れても`A=S; ${A}KIP=foo bar`のように組み立てれば素通りします[^bash-split]。さらに`Write`/`Edit`/`NotebookEdit`のパターンはパスのglob限定で、書き込む中身を条件にする文法がそもそもありません。Bashだけ塞いでもエージェントが`Write`に切り替えれば抜けます。`permissions.deny`による経路網羅は事実上不可能です。

[^bash-split]: 逆にコマンド名はシェル展開後に照合されます。`Bash(git:*)`を`permissions.deny`に入れて`IT=it; g$IT --version`を実行するとブロックされます。コマンド名ゲートとしては堅牢に動く一方、引数の部分文字列フィルタとしては抜ける、という非対称性があります。

中身を全経路で統一的に見るには、PreToolUseフックが正しいレイヤです。PreToolUse フックはエージェントのツール呼び出し直前に走り、`tool_name`、`tool_input`、`transcript_path`をJSONで標準入力から受け取ります。`exit 2`を返すと標準エラー出力がエージェントに渡り、ツール呼び出しは中止されます。

経路網羅も素直に書けます。ツールごとにテキストを含むフィールドが決まっているので、それを取り出して同じ正規表現で検査するだけです。

| ツール | 検査するフィールド |
|---|---|
| Write |`content`|
| Edit |`new_string`|
| NotebookEdit |`new_source`|
| Bash |`command`|

正規表現を1つ用意すれば、`echo "…" >> foo.rs`も`Edit`の差分も同じ枠で捕まります。

残るは非常口です。`doc(hidden)`のような必要悪のために、ルールを通すバイパスが要ります。素直な実装は、`BYPASS:doc_hidden`のような決まったトークン文字列が出ていたら、そのルールだけ見逃す、というものです。

問題は、このトークンをどこに書かれていたら有効とするか、です。エージェントが自由にトークンを発行できると、結局好き放題されてしまいます。そうならないための対策を考えるにあたり、CCのトランスクリプトはJSONLで、以下のように発話者が記録されていることに注目します。

```json
{"type": "user",      "message": {"content": "…"}}
{"type": "assistant", "message": {"content": "…"}}
```

この仕組みを利用して「バイパストークンが直近のユーザーメッセージにあるときだけ有効」と決めます。するとエージェントがいくら`BYPASS:doc_hidden`と発言しても、それはアシスタントのターンとして記録されるので無効です。ユーザーの物理的な発話だけがバイパスを発動できます。

以下ではこのアイデアを実装に移します。

## 実装

### ポリシー:`~/.claude/hooks/suppress-policy.toml`

どの属性をどう扱うかは、コードから分離してTOMLに置きます。コードに埋め込んでも構いませんが、こちらの方がルールを管理しやすいです。

```toml
# action:
#   "block"          - 常に拒否。bypassトークンも受け付けない。
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

`extensions`で`.rs`に絞っているのは、Markdownのコード解説やPythonファイルにリテラルが出てきたときの誤検出を避けるためです。これを忘れると後述の事故のようなことが起きます。

### フック:`~/.claude/hooks/block-suppress.py`

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

設計上の要点は3つです。

- fail-open: ポリシーが読めない（TOMLが壊れた／消えた）ときは0を返して通す。フックが原因でエージェントが固まるのは事故なので、ブロックより「黙って通す」に倒す。
- アシスタントのターンを無視:`latest_user_message`は`type != "user"`を全部スキップする。これがバイパスを防ぐ要。
- 拡張子判定: Write系なら`file_path`の末尾、Bashならコマンド中の部分文字列を見る。後者は厳密でないが、`mv`や`cat foo.rs >> bar`経由もまとめて巻き取れるので実用上は十分。

### `settings.json`への登録

```json:~/.claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|NotebookEdit|Bash",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/block-suppress.py" }
        ]
      }
    ]
  }
}
```

## やらかした話と実装上の諸注意

最初の実装は簡単なところから進めようと拡張子の設定を後回しにしていました。CCに指示をして後からポリシーに`extensions = [".rs"]`を足そうとしたところ、`Edit`が

```
PreToolUse:Edit hook error: blocked [dead_code]: #[allow(dead_code)] is never permitted
```

でブロックされました。原因は、以下のようにエラーメッセージにブロック対象のリテラルを書いていたことでした。

```toml
message = "#[allow(dead_code)] is never permitted"
```

`Edit`の`new_string`をスキャンするとき、この`message`内の`#[allow(dead_code)]`自体が`dead_code`ルールに引っかかります。

ここで`extensions = [".rs"]`がまだ設定できていなかったというのも二重でやらかしです。先にこれを書いていたら設定ファイルはTOMLファイルなので検査対象から外れているはずでした。

まとめると以下のようになります。

- メタデータ（ポリシー本体／フック自体／README）は構造的に規制対象の外へ置く。各ルールに「対象とすべきファイルの種類」を明示し、メタデータがスコープから外れるよう設計する
- 検出対象のリテラルを説明テキストに書かない。エラーメッセージは「何が起きたか」が分かれば十分で、`message = "this suppression attribute is never permitted"`のように書けば自家中毒の主要経路が消える

このときCCはフックスクリプトをリネームして無効化して回避しました。

```bash
mv ~/.claude/hooks/block-suppress.py /tmp/bak
# 編集
mv /tmp/bak ~/.claude/hooks/block-suppress.py
```

このコマンドには`.rs`も抑制属性のリテラルも含まれないので、フック自身に止める手段がありません。

このフックのテストを書かせようとしたときにも、同様のトラブルが起きました。テストコマンド自体がフックにブロックされたのです。Bashの検査は「コマンド文字列に`.rs`があり、かつ抑制属性のパターンにマッチする」で発火するので、`echo "#[allow(dead_code)]" >> src/lib.rs`をテストケースとして書いた瞬間にコマンドそのものが弾かれます。このときCCはテスト用のパターンをbase64でエンコードし、動的にデコードして回避しました。

```bash
DEAD=$(printf '%s' 'I1thbGxvdyhkZWFkX2NvZGUpXQ==' | base64 -d)
run A 2 "{\"tool_name\":\"Write\", ..., \"content\":\"$DEAD fn x(){}\", ...}"
```

ここまでバイパスを閉じる話をしてきたはずなのに実際にバイパスされてしまっています。実はこのようにエージェントがその気になれば今回の実装にはバイパス経路が残っています。冒頭で「決定的に制御したい」と書きましたが、ここでの決定的とは「確率的なプロンプト指示を、既定挙動なら必ず発火するゲートに置き換える」という意味であって、意図的な回避まで決定的に防げるという意味ではありません。この意味で今回の実装はセキュリティ境界には使えないことが分かります。今回の実装では、ポリシーファイルもフック本体もエージェントから普通にRead/Writeできてしまうからです。止まるのは「既定動作で抑制属性が混入する」「警告がうるさいので`#[allow]`を貼ってしまう」程度までで、意図的な回避は追えません。本気の防御はサンドボックスやCI側の必須チェック、ブランチ保護の領分で、フックの役割ではありません。

フックで完全防御を目指すと攻撃面は無限に広がります。最初に「意図せぬ既定の抑制を止める層であって、意図的なバイパスは追わない」と線引きしておくほうが、長続きします。

## 補遺: `permissionDecision: "ask"` でよかったのでは

なお、この記事を書き終わってから気づいたのですが、トークン方式は自前で組む必要がありませんでした。PreToolUseフックがstdoutにJSONを返すだけで、その場でユーザーに確認できます。

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "…"}}
```

`permissionDecision`は`"allow"`（即通過）・`"deny"`（拒否）・`"ask"`（通常の許可プロンプトを表示）の3値です。`require_token`のルールは`"ask"`を返すだけで置き換えられます。ユーザーはトークンを覚えて打つ必要がありません。エージェントはプロンプトをクリックできないので、自己バイパスも同様に防げます。こちらのほうがずっと素直です。

トークン方式に残る差は、人間が応答できないヘッドレス実行（`-p`やSDK）でも効く点くらいです。`ask`が対話モード専用で、ヘッドレスでは`defer`を返す設計だからです。ただヘッドレス実行は、料金面の事情もあって出番が限られます。都度の許可が要るようなやりとりをヘッドレスでやる場面も、そもそも考えにくいです。この差は実用上ほとんど効きません。

主体をエージェント境界で判定する、という記事の骨格は変わりません。ただ、その実装はトランスクリプトを自分で読むより、`permissionDecision: "ask"`に委ねたほうが簡単でした。
