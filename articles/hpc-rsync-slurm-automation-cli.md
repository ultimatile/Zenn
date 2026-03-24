---
title: "コーディングエージェントでスパコンを壊さずに利用するためのCLIツールを作った"
emoji: "🖥️"
type: "tech"
topics: [hpc, slurm, cli, claudecode]
published: true
---

## スパコンでコーディングエージェントを動かすとどうなるか

先日、スパコンのログインノードでCodexを起動したらノードがハングして複数ユーザーに影響が出た、という事例が話題になりました。

https://zenn.dev/chizuchizu/articles/a991c61ff0d073

詳細な原因は記事を参照していただきたいですが、プロセスがLustreストレージの応答待ちでハングするなどの現象が報告されています。

通常、スパコンのログインノードで高負荷プロセスを動かすことは推奨されません。
スパコンでの開発は、手元でコードを書いて、`rsync`で送って、`ssh`して`sbatch`でジョブ投入して、結果を`cat`して...というサイクルの繰り返しです。
`rsync`のオプション、ジョブスクリプトの記述、`module load`の手順など、毎回ちゃんと書くのはめんどくさいです。
エージェントにも同じサイクルを回させれば、スパコン上で直接動かす必要はありません。
ということでこのサイクルをまとめたhpcというCLIツールを作りました。

https://github.com/ultimatile/hpc

## hpc: ローカルで考えて、リモートで計算する

やることはシンプルです。

**コーディングエージェントはローカルで動かし、スパコンには計算だけを投げる。**

```mermaid
sequenceDiagram
    participant L as ローカル
    participant LN as ログインノード
    participant CN as 計算ノード
    L->>L: コード編集・ファイル探索
    L->>LN: hpc sync（rsync差分転送）
    L->>LN: hpc submit（ジョブ投入）
    LN->>CN: スケジューラーがジョブ実行
    CN-->>LN: 結果出力
    L->>LN: hpc status / hpc job-output
    LN-->>L: hpc sync （結果取得）
    L->>L: 結果確認・コード修正
```

ファイルの探索やコード編集はローカルファイルシステムで行い、`rsync`で差分同期してからジョブを投入します。
スパコンの典型的な開発サイクルをワンストップでカバーするrsync + Slurmのラッパーです。

SnakemakeやNextflowのようなジョブオーケストレーターとは異なり、ワークフローのDAG定義や依存関係の解決は行いません。
「コードを送って、ジョブを投げて、結果を見る」という手作業をCLIにまとめただけのハンディなツールで、本番計算よりも開発・テスト段階での利用を主な対象としています。

## インストール

```bash
# ワンショット実行
uvx --from git+https://github.com/ultimatile/hpc hpc

# 永続インストール
uv tool install git+https://github.com/ultimatile/hpc
```

## 基本ワークフロー

### 1. プロジェクトの初期化

```bash
hpc init
```

`hpc.toml`が生成されます。クラスタの接続情報と環境設定を記述します。

```toml:hpc.toml
[cluster]
host = "myhpc"                    # ~/.ssh/configのホスト名
workdir = "/scratch/user/myproj"  # リモートの作業ディレクトリ
scheduler = "slurm"               # "slurm" or "pjm"

[env]
modules = ["gcc/12.2.0", "cuda/12.2"]

[sync]
ignore = ["hpc.toml", ".git"]

[slurm.options]
partition = "gpu"
time = "02:00:00"
gpus = 1
```

### 2. ファイルの同期

```bash
hpc sync              # 双方向同期（push → pull）
hpc sync --dry-run    # プレビュー
hpc sync --push       # pushのみ（ローカル → リモート）
```

rsyncベースでチェックサム比較がデフォルトです。
`hpc.toml`の`[sync] ignore`で除外パターンを指定できます。

### 3. ログインノードでのセットアップ

パッケージインストールなどインターネットアクセスが必要な操作は、スケジューラーを介さずログインノードで直接実行します。

```bash
hpc exec "pip install -r requirements.txt"
hpc exec "julia -e 'using Pkg; Pkg.instantiate()'"
```

`[env]`セクションの`module load`等は自動適用されます。

### 4. ジョブの投入

```bash
hpc submit "python train.py"
hpc submit --script run.sh --wait  # スクリプト投入＋完了待ち
```

`--wait`をつけるとジョブ完了までポーリングします。
コーディングエージェントと組み合わせると、投入→待機→結果確認→コード修正のループを自動で回せます。

### 5. 結果の確認

```bash
hpc status 12345678       # ジョブステータス
hpc job-output 12345678   # 標準出力
hpc job-output -e 12345678  # 標準エラー
```

### コーディングエージェントからの利用例

実際にClaude Codeから使うと、こんなフローになります。

```
> Aのバグを修正して。テストはクラスター上で実行して。
> コードの共有とジョブ投入はhpcコマンドを使って。

Claude Code:
  1. コードを読んでバグを修正
  2. hpc sync                              # 修正をクラスタに同期
  3. hpc submit "pytest tests/" --wait     # テストを投入して待つ
  4. hpc job-output <job_id>               # 結果を確認
  5. （FAILED...）修正を追加
  6. hpc sync && hpc submit ... --wait     # 再投入
  7. hpc job-output <job_id>               # PASSED → 完了
```

ローカルでコードを編集し、スパコンでは計算だけが走ります。

その他コマンドやオプションに関しては`hpc --help`や[README](https://github.com/ultimatile/hpc/blob/main/README.md)を参照してください。

なお、hpcリポジトリにはClaude Code向けの[スキルファイル](https://docs.anthropic.com/en/docs/claude-code/skills)（`.claude/skills/hpc/SKILL.md`）が同梱されています。
プロジェクトに配置するだけで、CLIの使い方やワークフローをClaude Codeが自動的に把握し、上記のようなフローを自然言語で指示できるようになります。
人間がオプションを覚える必要はありません。

## おわりに

Anthropicが最近公開したブログ[Long-running Claude for scientific computing](https://www.anthropic.com/research/long-running-Claude)では、Claude Codeを直接スパコンの計算ノード上で48時間動かして科学計算コードを自律開発させる事例が紹介されています。

Claude Codeの推論はAnthropicのサーバーで行われるため、計算ノードからインターネットへのアクセスが必要です。
通常のHPCクラスタではそのような構成になっていません。
この事例で使われているPittsburgh Supercomputing CenterのBridges-2は、インターネットアクセスが可能な構成なのかもしれません。

一般的なスパコンでこれを真似しようとすると、ログインノードでコーディングエージェントを動かすことになり、冒頭の事例のようにノードをハングさせるリスクがあります。

hpcはエージェントをローカルに留め、スパコンへの操作をrsyncとssh越しのコマンド実行に限定します。
スパコンの運用ポリシーに反さないよう設計しており、他のユーザーへの影響も小さくなります。
計算ノードのネットワーク制限が緩和されるまでは、「ローカルで考えて、リモートで計算する」が現実的な解だと考えています。
