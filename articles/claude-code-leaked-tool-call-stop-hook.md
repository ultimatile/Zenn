---
title: "Claude Codeでツール呼び出しが実行されず生テキストとして表示されるときの対策"
emoji: "🩹"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["claudecode", "harnessengineering"]
published: false
register: almost
---

::: message

本記事はClaude Code (Opus 4.8/Fable 5)と一緒に書きました。正確を期すよう心がけていますが、記事の内容の速報性・揮発性を考慮して普段よりチェックが甘くなっています。不正確な箇所があれば教えていただけるとありがたいです。

:::

## 症状

Claude Codeを長時間使っていると、まれにモデルのツール呼び出しが実行されず、内部マークアップがそのまま会話に表示されることがあります。

```text
call
<invoke name="Bash">
<parameter name="command">npm test</parameter>
</invoke>
```

先頭の`call`は、ツール呼び出しの開始トークンがテキストに分解された残骸と見られ、付かないこともあります（[anthropics/claude-code#60584](https://github.com/anthropics/claude-code/issues/60584)では`court`という断片も報告されています）。こうなったターンは、コマンドが実行されないまま終わります。エラーメッセージは出ません。本稿ではこの現象の既知情報を整理し、ユーザー側でできる応急処置としてStopフックによるガードを提案します。

## 2つの壊れ方

ハーネス（モデルの出力からツール呼び出しを取り出して実行する、Claude Code本体側の機構）の視点では、壊れ方は2段階あります。

- 部分的に壊れている場合: ツール呼び出しの開始は認識できるが、中身がパースできない。ハーネスは`Your tool call was malformed and could not be parsed.`というエラーをモデルに返し、モデルはその場でリトライできる。
- 完全に壊れている場合: マークアップのprefixごと欠落するなどして、ツール呼び出しの開始として検知すらされない。ただのテキストとして会話に流れ、エラーも出ずにターンが終わる。

GitHubで報告が多いのは前者です。エラーメッセージという検索可能な文字列が残るので、報告されやすいという観測バイアスもあると思います。冒頭の例は後者で、本稿が主に扱うのもこちらのサイレント変種です。

## 関連issueの系譜

[anthropics/claude-codeのissue](https://github.com/anthropics/claude-code)には同種の報告が複数あります（2026年6月時点）。

| issue                                                            | 作成    | 状態                   | 概要                                                             |
| ---------------------------------------------------------------- | ------- | ---------------------- | ---------------------------------------------------------------- |
| [#24364](https://github.com/anthropics/claude-code/issues/24364) | 2026-02 | closed（NOT_PLANNED）  | Opus 4.6でmalformedなツール呼び出しが繰り返される                |
| [#49747](https://github.com/anthropics/claude-code/issues/49747) | 2026-04 | open                   | Opus 4.7が長い出力でlegacy XML形式をJSONのツール呼び出しに混ぜる |
| [#60584](https://github.com/anthropics/claude-code/issues/60584) | 2026-05 | closed（#49747と重複） | ツール呼び出しがリテラルなテキストとして出力される               |
| [#62344](https://github.com/anthropics/claude-code/issues/62344) | 2026-05 | closed（#61367と重複） | 長セッションでのfew-shot self-poisoning仮説                      |
| [#63604](https://github.com/anthropics/claude-code/issues/63604) | 2026-05 | open                   | Opus 4.8で再発し、応答全体が破棄される                           |
| [#66400](https://github.com/anthropics/claude-code/issues/66400) | 2026-06 | open                   | エラー変種とテキスト描画変種の両方を報告                         |

closedの多くはbotによる自動重複判定で、類似issueの提示後3日で自動closeされたものです。修正を伴ってcloseされたものはどの世代にもなく、モデル世代を跨いでissueを乗り換えながら続いているのが現状です。

## 自家中毒(few-shot self-poisoning)仮説

[anthropics/claude-code#62344](https://github.com/anthropics/claude-code/issues/62344)は、この現象が長セッションに偏ることへの説明として、壊れた実例が後続の自分の出力を害する、いわば自家中毒（few-shot self-poisoning）という仮説を提示しています。一度壊れたツール呼び出しが会話履歴に入ると、モデルがそれをお手本として参照してしまい、以降のツール呼び出しも同じ形に壊れ続ける、というものです。

この仮説に立つと、サイレント変種はエラー変種より毒性が強いことになります。エラー変種では、壊れたブロックの直後に「malformedだった」というエラーと、リトライで成功した正しい呼び出しが履歴に並びます。負例と正例のペアとして働くわけです。サイレント変種では、壊れたブロックが注釈なしで履歴に残り、文脈上は受理された正常な出力と見分けがつきません。

発生時の対処もこの仮説から導けます。セッション全体を捨てる`/clear`や、要約に壊れたテキストが持ち越されうる`/compact`ではなく、壊れた出力の直前のチェックポイントへ`/rewind`で戻るのが最小ロスです。毒の実例だけが履歴から消え、それ以前の文脈は無傷で残ります。

ここまでは#62344の仮説に沿った説明です。ただし本稿の執筆中にも、このサイレント変種が複数回発生しました。発生したのはいずれも1つの応答に複数のEdit呼び出しをまとめたときで、1編集ずつに分けるとそのまま通りました。少なくとも今回の発生は、長セッションに伴う汚染ではなく、1ターンに詰めるツール呼び出しの数に比例するシリアライズの崩れとして説明できそうです。自家中毒は長セッションで起きるという#62344の観測には合いますが、本稿の観測には合いません。両者は排他ではなく、それぞれ別の現象を捉えているのだと思います。

原因がこちらなら、対処は単純なリトライと、重い編集を1ターンに詰めないことで足ります。前述のrewindは、汚染が連鎖する場合に効く保険という位置づけになります。いずれにせよ、漏れたマークアップを捕まえてターンを回復するというフックの働きは、根本原因がどちらでも変わりません。

## Stopフックによるガード

上流の修正を待つ間、ユーザー側でも一段の防御を入れられます。Claude Codeの[Stopフック](https://docs.claude.com/en/docs/claude-code/hooks)はターン終了時に発火してtranscript（会話ログのJSONLファイル）を読めるので、最後のassistantメッセージに行頭のツール呼び出しマークアップが残っていたら、ターン終了をブロックして「それは実行されていない。正規の形式で再発行せよ」とモデルに差し戻せます。

疑似コードでは次のようになります。

```text
on Stop / SubagentStop(last_assistant_message, stop_hook_active):
    # ループガード: 差し戻しは1ターンに1回まで。
    # 再発行がまた壊れても無限ループせず、
    # 正当な引用への誤検知もこの1回で必ず収束する
    if stop_hook_active: return

    # last_assistant_messageはハーネスが直接渡す最後のアシスタント出力。
    # SubagentStopではサブエージェント自身の最終メッセージが入る
    # (transcript_pathは親セッションを指すので使わない)
    text = last_assistant_message
    if textに行頭の "<invoke name=" や "<function_calls>" がマッチ:
        # 撤去判断のための発火記録（オプション）
        append_log(現在時刻, session_id, マッチ箇所)
        block(reason = "直前の出力に生のツール呼び出しマークアップが
            含まれており、実行されていない。正規のツール呼び出しとして
            再発行せよ。意図的な引用ならその旨を述べて終了してよい")

    # スクリプト内部のエラーはすべて握りつぶして素通し（fail-open）。
    # ガード自身のバグでセッションを巻き込まないため
```

設計判断は次の3つです。

- 検知して差し戻すだけにして、漏れたマークアップを寛容にパースして実行することは絶対にしない。引用やユーザーの貼り付けたテキストが実行に化ける経路を作ると、プロンプトインジェクションの昇格に直結する。
- 引用と事故の区別をしない。本稿のようにマークアップを例示する正当なテキストと事故の漏れは、同じバイト列が文脈次第でどちらにもなる以上、構文だけでは原理的に区別できない。賢い判定器を作るとそれ自体が誤るので、誤検知のコストを差し戻し1回に固定し、意図の判定はモデル自身に委ねる。
- 発火のたびにログへ記録する（オプション。ガードの動作自体には不要）。これは上流修正待ちの暫定ガードで、短期で外すことになる可能性があるため、撤去判断の材料として発火頻度を計測したくて足している。発火しないことが正常な、アサーションとしての運用。十分な利用とターン数を重ねても発火しなければ撤去の判断材料になるが、発火ゼロは利用量の減少やモデルの変更、正規表現の検出漏れでも起こるので、証拠ではなく目安にとどめる。

:::details 実装例（Python、2026年6月時点で動作確認）

筆者環境（macOS）で動作確認した実装です。`Stop`に加えて、サブエージェント用に`SubagentStop`にも同じスクリプトを登録しています。

```python:~/.claude/hooks/detect-leaked-toolcall.py
#!/usr/bin/env python3
"""Stop/SubagentStop hook: bounce leaked tool-call markup back to the model.

Models occasionally regress to the legacy in-text XML tool-call format
(anthropics/claude-code#49747, #66400). When the markup is mangled enough
that the harness never recognizes it as a tool call, it streams to the user
as plain text with no error — and the unlabeled broken block then acts as a
few-shot exemplar that poisons later tool calls (#62344).

This hook detects such orphan markup in the turn's final assistant message
and blocks the stop once, feeding a correction back so the model re-issues
the call properly. This both recovers the turn and converts the silent
poison into a labeled negative example in history.

Deliberate properties:
- Detect-and-bounce only; never parses or executes the leaked call
  (lenient parse + execute would be a prompt-injection escalation path).
- stop_hook_active guard caps the bounce at one per turn, so a false
  positive (e.g. legitimately quoted markup) costs a single retry.
- Fails open: any internal error exits 0 so a hook bug can never wedge
  the session.
- Each trigger is appended to leaked-toolcall-triggers.log to gauge fire
  frequency. A sustained zero (over enough usage/turns) is evidence toward
  retiring the guard — though zero can also come from low usage, a model
  change, or the regex missing a new variant, so it is a signal, not proof.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).with_name("leaked-toolcall-triggers.log")

# Opening forms of the legacy XML tool-call markup, with or without a
# namespace prefix. Anchored to line start to cut false positives from
# inline mentions in prose.
LEAK_RE = re.compile(
    r"^[ \t]*<(?:[A-Za-z][\w.-]*:)?"
    r"(?:invoke\s+name=|function_calls\s*>|parameter\s+name=)",
    re.M,
)


def last_assistant_text(transcript_path: str) -> str:
    """Concatenated text blocks of the last assistant entry in the JSONL."""
    text = ""
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant":
                continue
            content = entry.get("message", {}).get("content", [])
            if isinstance(content, str):
                text = content
            else:
                text = "\n".join(
                    b.get("text", "") for b in content if b.get("type") == "text"
                )
    return text


def main() -> None:
    payload = json.load(sys.stdin)
    # Loop guard: if we are already continuing because of a stop hook,
    # never block again — one bounce per turn maximum.
    if payload.get("stop_hook_active"):
        return
    # Prefer the message the harness hands us directly. For SubagentStop this
    # is the subagent's OWN final message; transcript_path there points at the
    # PARENT session, so reading it would miss the subagent and mis-target the
    # parent conversation. Fall back to parsing the transcript only when the
    # field is absent (older CLI versions).
    text = payload.get("last_assistant_message")
    if text is None:
        transcript_path = payload.get("transcript_path")
        text = last_assistant_text(transcript_path) if transcript_path else ""
    match = LEAK_RE.search(text)
    if not match:
        return
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(LOG_PATH, "a", encoding="utf-8") as log:
        log.write(
            f"{timestamp} session={payload.get('session_id', '?')} "
            f"match={match.group(0).strip()!r}\n"
        )
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": (
                    "Your last message contains raw tool-call markup emitted as "
                    "plain text (it was NOT executed). Re-issue it as a proper "
                    "structured tool call. If the markup was an intentional "
                    "quotation rather than an attempted call, simply state that "
                    "and finish your turn."
                ),
                "systemMessage": (
                    "leaked-toolcall guard: 生のツール呼び出しマークアップを検知し、"
                    "モデルに再発行を要求しました"
                ),
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Fail open: a broken guard must never prevent the session from
        # stopping or mask the model's output.
        sys.exit(0)
```

`chmod +x`して、`~/.claude/settings.json`に登録します。

```json:~/.claude/settings.jsonの抜粋
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/detect-leaked-toolcall.py"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/detect-leaked-toolcall.py"
          }
        ]
      }
    ]
  }
}
```

:::

## なぜ上流修正を待たずにフックを足すのか

正直なところ、poisoning対策としての効果は分かりません。自家中毒はあくまでissue上の仮説で、差し戻しによって履歴の毒がラベル付きの負例に変わることがどれだけ効くかは検証していません。そこは安全側に倒しているだけです。

主目的は別にあります。サイレント変種の実害は、エージェントが作業の途中でエラーも出さずに止まることです。自律実行を長く走らせる使い方では、人手の介入なしに走り続けられる長さがそのまま使い勝手を決めます。このフックは沈黙死を自動リトライに変換するので、検知できた範囲では損失が差し戻し1回分で済みます。

もう1つは、上流修正の時期が読みにくいことです。[anthropics/claude-code#49747](https://github.com/anthropics/claude-code/issues/49747)のタイトル"Opus 4.7 mixes legacy XML tool-use format into JSON tool calls on longer payloads"が示すとおり、漏れているのは旧世代のClaudeが実際に使っていたテキスト埋め込みのXML形式です。ただしissueで確認できるのは、投稿者がこの旧形式の混入を観測したところまでで、原因が学習データやモデル学習にあるとAnthropicが認めたわけではありません。あくまで仮説として、学習データに残る廃止済み形式への先祖返りだとすれば、ハーネスの単発バグではなくモデル側の問題ということになり、Opus 4.6から4.8まで世代を跨いで再発している事実とも整合します。この見立てが当たっていれば次の世代でも出るので、発火ログという撤去の目安付きのガードは、保守コストの割に賞味期限が長いことになります。
