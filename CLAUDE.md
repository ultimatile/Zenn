# CLAUDE.md（Zenn記事リポジトリ）

Zenn CLIで管理する記事リポジトリ。記事は `articles/<slug>.md`、本は `books/`。

## 運用コマンド

- 新規記事: `./new.sh <slug>`（`npx zenn new:article --slug <slug> --title mytitle --type tech --emoji 🦀` のラッパ）
- プレビュー: `npx zenn preview`（`preview.sh`）

## Frontmatter schema

各記事の先頭。`new.sh` のデフォルトは `type: tech` / `emoji: 🦀`。

```yaml
---
title: "記事タイトル"   # 文字列。引用符で囲む
emoji: "🦀"             # 表紙に使う絵文字1つ
type: "tech"           # tech: 技術記事 / idea: アイデア
topics: ["rust"]       # 配列。日本語タグ可（例: ["量子力学", "物理"]）
published: false       # true=公開 / false=下書き
---
```

## 文章品質（普遍ルール）

普遍的な日本語散文の品質ルールはグローバルの `japanese-writing` skill に集約する。本ファイルはそこへ委譲しつつ、最低限を再掲する。

**プリファレンス確定ゲート:** 文体・句読点など記事ごとに割れる軸は、silentに決めずに執筆開始時に**推奨案を添えて許可を取り**、確定してから書く（例: 「技術文書のため敬体・句読点は `、。` を推奨します。よろしいでしょうか？」）。用語の新造が要る場合も同様に [`GLOSSARY.md`](./GLOSSARY.md) の運用原則どおり提案して確認する。

- **文体は記事ごとに次の3モードから選ぶ（確定ゲートで確認するask軸）:**
  - **all敬体**: 全文を敬体で書く。
  - **all常体**: 全文を常体で書く。
  - **almost敬体**: 地の文は敬体。ただし TL;DR などの箇条書きは情報密度のため常体を許容する。
  いずれのモードでも**地の文（散文）内では文体を一貫**させ、混ぜない。almost敬体で常体を使うのは箇条書きに限る（地の文には持ち込まない）。ジャンルによる強制はしない（技術=敬体・数物=常体の傾向は既存記事にあるが規則ではない）。
  - **モードはfrontmatterの `register` キーで宣言し、`npm run lint:register`（主導実行ゲート）が機械チェックする。** 値は `almost`（未指定時の既定）／`keitai`（all敬体）／`joutai`（all常体）。`scripts/lint-register.mjs` が各記事の `register` を読み、モード別に `no-mix-dearu-desumasu`（本文/箇条書きの文体）を当てて textlint する。`register` はZennが無視する独自キーで、デプロイ・プレビューに影響しないことを実push（published:false記事）で検証済み。**pre-commitでは `no-mix-dearu-desumasu` を無効化**している（プリセット既定が「本文=ですます・箇条書き=である」でalmost敬体を固定し、all敬体/all常体を弾くため）。よって文体ゲートはhusky外の `lint:register` が担い、pre-commitは表記ゆれ・用字＋autofixに専念する。
- **句読点（`、。` と `，．`）は著者の選択。** 記事ごとに一貫させ、混在させない。既存記事のスタイルを矯正しない。
- **地の文の段落は1論理行で書く（1文1行にしない）。** Zennのレンダラ（markdown-it）は `breaks: true` で、**単一改行が `<br>`（表示上の改行）になる**（CommonMarkのように半角空白へは畳まれない）。そのため1文1行（semantic line break）にすると文ごとに改行表示されて段落が崩れる。長い行の編集はソース改行ではなく**エディタのソフトラップ**で行う。表示に出ないソース改行を入れる手段は無い（HTMLコメントは `html: false` でエスケープされ、行末 `\` や2スペースは `<br>` を増やすだけ。実レンダラで確認済み）。コードブロック・リスト・表・`:::` 行は対象外。
- **本文は `##`（見出し2）から始める。** `#`（H1）は使わない（タイトルはfrontmatterが持つ）。Zennもアクセシビリティ上 `##` 始まりを推奨。
- LLM由来の修辞過剰（節・文を丸ごと太字／`——`二倍ダッシュ／アフォリズム調の締め・メタ言及／対句・三段の修辞／日本語概念への英語一語グロスの乱発）を避ける。語彙狩り（接続詞や専門用語の禁止）はしない。詳細は `japanese-writing` skill を参照。
- イタリック `*…*` は日本語の強調に使わない（日本語に斜体強調の慣習が無い）。英単語に当てるのは文法上可だが用途は限定的。画像直後の `*キャプション*` はキャプション構文なので対象外。
- プレゼン: 初出のOSS・ツールは公式GitHub/ランディングにリンク。一般的でないが説明するほどでない専門用語は権威あるリンク（Wikipedia等）を張る。記事の核心となる用語はリンクで済ませず分野・意味・注目される理由を説明する。専門家前提の導入を避け、非専門家が追える足場を置く。詳細は `japanese-writing` skill。
- **用語・表記（英単語/カタカナ/人名由来テクニカルターム）は [`GLOSSARY.md`](./GLOSSARY.md) に従う。**
- **表記ゆれ・用字（しくみ⇔仕組み 等）は textlint で機械的に統制する**（`npm run lint:text` / `npm run lint:text:fix`）。表記辞書は `prh.yml`、設定は `.textlintrc.json`。数の漢字／算用数字の選択は語彙化依存（三角形は漢字・65537角形は算用）で機械化に向かないため、`arabic-kanji-numbers` は無効化し書き手判断とする。意味的な用語判断は GLOSSARY、機械的な表記ゆれは textlint、と役割を分ける。
- **埋め込みバレットパターンの局所disable**: 「intro行＋箇条書き＋末尾`。`」で1文を成す書き方（例: `内側のエラーは` / `- A` / `- B` / `…のどちらか一方です。`）は日本語として正当だが、`ja-no-mixed-period` はリストをまたぐ continuation を認識せず intro行を「`。`止めでない文」として警告する。導入済みの `textlint-filter-rule-comments`（`.textlintrc.json` の `filters.comments: true`）で、該当範囲を `<!-- textlint-disable ja-technical-writing/ja-no-mixed-period -->` … `<!-- textlint-enable ja-technical-writing/ja-no-mixed-period -->` で囲んで黙らせる。disable は埋め込みリストを保ちたいときに限り、文として素直に閉じられる場面（出力ブロックのラベル等）は `。` で閉じる。
- **`:::` ブロックは内側に空行を入れる**: `:::message`（や `alert` / `:::details`）の本文を空行なしで囲むと、Zennのパーサが「開始行〜本文〜閉じ `:::`」を1段落とみなし、閉じ `:::` が `。`止めでない行として `ja-no-mixed-period` に誤検出される。**`:::xxx` の直後と閉じ `:::` の直前に空行**を入れると、本文が独立段落として `。` で閉じ、`:::` 単独行は文として扱われず誤検出が消える（実レンダラ/textlintで確認済み）。
- **pre-commit フック**（husky + lint-staged）が、コミット時にステージ済み `articles/**/*.md` を `textlint --fix` で自動修正・再ステージする（**autofix-only**。`textlint --fix` は常に exit 0 なので構造エラーでは止めない。doubled-joshi 等の構造面は skill 監査レーン／手動 `lint:text` でケア）。止めたくない・スキップしたいときは lazygit の `w` キー、またはメッセージ頭に `WIP`（lazygit の `skipHookPrefix` が `--no-verify` に翻訳）、または `git commit --no-verify`。生の `git commit -m "WIP..."` は lazygit 経由でないとスキップされない点に注意。

## Zenn Markdown記法

出典: <https://zenn.dev/zenn/articles/markdown-guide> をトレース（全機能）。

### 基本記法

- **見出し**: `#`〜`####`（見出し1〜4）。アクセシビリティ上 `##`（見出し2）から始めるのを推奨。
- **リスト**: 行頭 `-` または `*`。ネストはインデント。
- **番号付きリスト**: `1.` `2.` …
- **テキストリンク**: `[アンカーテキスト](URL)`。
- **画像**: `![](URL)`
  - 横幅指定: `![](URL =250x)`（URLの後に半角スペース＋`=○○x`、px単位）
  - Altテキスト: `![Altテキスト](URL)`
  - キャプション: 画像直下の行に `*キャプション*`（`*`で挟む）
  - 画像にリンク: `[![](画像URL)](リンクURL)`
- **テーブル**: 標準のパイプ記法（`| Head | Head |` / `| ---- | ---- |`）。
- **引用**: 行頭 `> `。
- **脚注**: 参照 `本文[^1]` ＋ 定義 `[^1]: 内容`。インライン脚注 `^[脚注の内容]` も可。
- **区切り線**: `---`（`-----`）。
- **インラインスタイル**: `*イタリック*` / `**太字**` / `~~打ち消し線~~` / `` `code` ``。
- **インラインコメント**: `<!-- メモ -->`。公開ページには表示されない。**複数行コメントは非対応**（1行ずつ）。

### コードブロック

- ` ```言語 ` で囲む。シンタックスハイライトはShiki（対応言語は <https://shiki.style/languages>）。
- ファイル名表示: ` ```言語:ファイル名 `（`:`区切り）。
- diff: ` ```diff 言語 `（半角スペース区切り）。`+`・`-`・`>`・`<`・半角スペースで始まる行のみハイライト。ファイル名併用 ` ```diff 言語:ファイル名 ` も可。

### 数式（KaTeX）

- 常に最新KaTeX。対応記法 <https://katex.org/docs/support_table.html>。
- ブロック: `$$` で挟む。**`$$` の前後は空行**でないと正しく埋め込まれないことがある。
- インライン: `$a\ne0$` のように `$` ひとつで挟む。

### Zenn独自記法

- **メッセージ**: `:::message` … `:::` / 警告は `:::message alert` … `:::`。本文の前後に空行を入れる（textlint `ja-no-mixed-period` 誤検出回避。詳細は文章品質節）。
- **アコーディオン（トグル）**: `:::details タイトル` … `:::`。
- **ネスト**: 外側の開始/終了に `:` を1つ追加（例: `::::details` の中に `:::message`）。

### コンテンツ埋め込み

URLだけの行（前後に改行）で自動埋め込みされるもの、または `@[...](...)` 記法。

- **リンクカード**: URLだけの行、または `@[card](URL)`。
- **X（Twitter）**: ポストURLだけの行（`twitter.com` / `x.com`）。リプライ元非表示は `?conversation=none`。
- **YouTube**: 動画URLだけの行。
- **GitHub**: ファイルURL/パーマリンクだけの行。行指定 `#L1-L3` または `#L3`。テキストファイルのみ。
- **GitHub Gist**: `@[gist](GistのURL)`。特定ファイルは `?file=ファイル名`。
- **CodePen**: `@[codepen](URL)`。タブは `?default-tab=html,css`。
- **SlideShare**: `@[slideshare](key)`。
- **SpeakerDeck**: `@[speakerdeck](ID)`。スライド番号 `?slide=24`。
- **Docswell**: `@[docswell](URL)`。
- **JSFiddle**: `@[jsfiddle](URL)`。
- **CodeSandbox**: `@[codesandbox](embed用URL)`。
- **StackBlitz**: `@[stackblitz](embed用URL)`。
- **Figma**: `@[figma](ファイル/プロトタイプのURL)`。
- **blueprintUE**: `@[blueprintue](ページURL)`。

アンダースコア `_` を含むURLが自動リンク/カードで途切れる場合は、`@[card](URL)`／`@[tweet](URL)` を使うか、URLを `<` `>` で囲む。

### ダイアグラム（mermaid.js）

- ` ```mermaid ` のコードブロックで自動レンダリング。文法は mermaid.js 公式に従う。
- 制限: 1ブロック**2000文字**以内、フローチャートの `&` チェーンは**10**以下、クリックイベント（Interaction）は無効。

### 入力補完（エディタ機能・Markdown記法ではない）

- 絵文字: `:` に続けて1文字入力で候補表示。
