---
title: "Python CLIアプリでの--versionの生やし方"
emoji: "🏷️"
type: "tech"
topics: ["python", "click", "typer", "argparse", "uv"]
published: false
---

## TL;DR

- バージョンのSSOTは `pyproject.toml` の `project.version`。ランタイムからは `importlib.metadata.version("dist-name")` で読む(Python 3.8+ 標準ライブラリ)。
- **Click**: `@click.version_option(None, "-V", "--version", package_name="dist-name")`
- **Typer**: `is_eager=True` な callback で `metadata.version("dist-name")` を `print` → `typer.Exit()`
- **argparse**: `parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {metadata.version('dist-name')}")`
- `metadata.version()` に渡すのは **distribution name** (`pyproject.toml` の `[project] name`) で、**import name** ではない。両者がハイフン/アンダースコアやプレフィックスで一致しない構成があるので要注意。
- フォールバック(`PackageNotFoundError` 時に `pyproject.toml` を直接読む)は uv ワークフローでは基本踏まれない。デフォルト不要、必要になったら足せばよい。

## 前提: SSOTの所在

```
pyproject.toml [project] version
      │
      │  ビルド時にバックエンド (hatch/setuptools/uv-build/…) が転記
      ▼
<dist>/PKG-INFO の "Version:" 行
      │
      │  importlib.metadata がインストール済み dist-info を走査して拾う
      ▼
importlib.metadata.version("dist-name")
```

`pyproject.toml` がSSOT、`importlib.metadata` が読み出しI/Fです。これ以上のものは要りません。

`importlib.metadata` は Python 3.8+ で標準ライブラリ入りしました(3.7 以前は `importlib_metadata` バックポート)。追加依存ゼロでバージョン解決ができるのが今回の話の土台になります。

### distribution name と import name の食い違いに注意

`metadata.version(...)` に渡すのは **distribution name** (`pyproject.toml` の `[project] name`、つまり PyPI に上がる名前 / `pip install <これ>` で書く名前)で、`import` 時に使う **import name** とは別物です。

- 有名な食い違い例:
  - `Pillow` (dist) / `PIL` (import) — `metadata.version("Pillow")` が正解。
  - `scikit-learn` (dist) / `sklearn` (import) — `metadata.version("scikit-learn")` が正解。
  - `beautifulsoup4` (dist) / `bs4` (import)、`PyYAML` (dist) / `yaml` (import)、`opencv-python` (dist) / `cv2` (import) なども同様。
- 自前プロジェクトでも `pyproject.toml` で `[project] name = "foo-cli"` と書きながらパッケージは `src/foo/` のように別名にしているなら同じ罠が踏めます。
- 一致するかどうかをハードコードしたくない場合でも、`__package__` から逆引きするより distribution name を文字列リテラルで持つほうが事故が少ないです(リネームしたら気づくため)。

両者を実行時に対応付けたい場合は `importlib.metadata.packages_distributions()` が使えますが、これは「ある import name がどの dist に属するか」を返すマップなので、本来 dist 名が分かっているならわざわざ使う必要はありません。

## Click: `@click.version_option`

完全委譲です。`package_name` に dist 名を渡すと、内部で `importlib.metadata.version()` を引いてくれます。

```python
import click

@click.group()
@click.version_option(None, "-V", "--version", package_name="mplc")
def cli():
    ...
```

第一引数 `None` は「明示的なバージョン文字列を渡さない = `package_name` から自動解決する」の意です。短いエイリアスが要らなければ `@click.version_option(package_name="mplc")` だけで `--version` が生えます(`-V` は付きません)。

出力フォーマットはデフォルトで `mplc, version 1.1.0` です。差し替えたければ `message=` を渡します:

```python
@click.version_option(None, "-V", "--version", package_name="mplc", message="%(prog)s %(version)s")
```

利用可能な変数は `%(prog)s` / `%(version)s` / `%(package)s` です。

Click を採用しているならこれが最小・最良です。`importlib.metadata` 呼び出しすら明示的に書かないで済みます。

## Typer: callback パターン

Typer は Click の薄いラッパですが、Click の `version_option` 相当のショートカットは無いので自前で書きます。

```python
import typer
from importlib import metadata

app = typer.Typer()


def _version_callback(value: bool):
    if not value:
        return
    print(f"hpc {metadata.version('hpc')}")
    raise typer.Exit()


@app.callback()
def app_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Print version and exit",
    ),
):
    pass
```

### `is_eager=True` を忘れない

これが地味に重要です。`is_eager=True` を付けないと Typer/Click は他のオプションのパース・バリデーションを先に進めてしまい、サブコマンドの必須引数が無い場合に「`--version` だけ叩いたのに usage エラーで死ぬ」現象が出ます。eager オプションは他のパースより先に発火するので、callback の中で `typer.Exit()` すれば残りのバリデーションをスキップして即終了できます。

### `@app.callback()` 内に同居させる

別の eager オプション(`--skill` のような hidden オプション等)が既にあるなら、同じ `app_callback` の引数に `version` を足す形が無難です。Typer の `@app.callback()` は1つしか持てないので、複数の eager オプションを並べる場所がここしかありません。

## argparse: `action="version"`

argparse 組み込みのアクションを使います。`version=` に文字列を渡すだけで `--version` 時に出力して `SystemExit(0)` してくれます。

```python
import argparse
from importlib import metadata

parser = argparse.ArgumentParser(prog="cjk-space-formatter")
parser.add_argument(
    "-V",
    "--version",
    action="version",
    version=f"%(prog)s {metadata.version('cjk-space-formatter')}",
)
```

- `%(prog)s` は `parser` の `prog` に展開されます(argparse の `version=` は printf-style フォーマットを通します)。
- `metadata.version()` の呼び出しは **parser 構築時**に走るので、起動コストに乗ります。重くはありませんが、起動時間が極端にシビアな用途(補完スクリプト等)では遅延評価したくなるかもしれません。その場合は `action="version"` を捨てて、自前で `--version` を `parse_args` 後に分岐する必要があります(あまり旨味はありません)。

## `__version__` 属性をエクスポートするか

`__init__.py` に `__version__ = "x.y.z"` を置く慣習は古くから根強いです。

```python
# pkg/__init__.py
from importlib import metadata
__version__ = metadata.version("dist-name")
```

ライブラリとして配って、利用者が `pkg.__version__` を参照するユースケースがあるなら付けておく価値があります。アプリ専用(CLI として叩かれるだけ)なら不要です。

ハードコード(`__version__ = "0.1.0"`)はSSOT原則違反なので避けます。書くなら必ず `metadata.version()` から引きます。

## フォールバックは要るか

`importlib.metadata.version()` は dist-info が無いと `PackageNotFoundError` を投げます。これに備えて `pyproject.toml` を直接パースする二段フォールバックを書くこともできます:

```python
def _read_version() -> str:
    from importlib import metadata
    try:
        return metadata.version("dist-name")
    except metadata.PackageNotFoundError:
        pass
    import tomllib  # Python 3.11+
    from pathlib import Path
    try:
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        with pyproject.open("rb") as f:
            return tomllib.load(f)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "unknown"
```

ただし `PackageNotFoundError` が発生するのは要するに「インタプリタ環境に dist-info が存在しない」ときだけです。uv ベースのワークフローだと:

| 操作 | dist-info | `metadata.version()` |
|---|---|---|
| `uv tool install .` | 専用 venv に作られる | ✓ |
| `uv sync` / `uv pip install -e .` | editable でも生成される | ✓ |
| `uv run <cmd>` | 自動 sync 経由で生成済み | ✓ |
| `PYTHONPATH=src python -m pkg` (install 無し) | 無い | ✗ |
| ソースを別 venv にコピーして直叩き | 無い | ✗ |

下 2 行のような「install ステップを踏まずに source tree から直接実行する」運用を想定するなら fallback を書く価値がありますが、`uv tool install` で配るのが主用途なら出番がありません。デフォルトは fallback 無しでよく、必要になった時点で `_read_version()` を足せば十分です。

なお `pyproject.toml` の場所を「ファイルの親の親」のような相対パス決め打ちで取りに行くのは、パッケージ構造を変えたときに静かに壊れます。fallback を入れるなら「パスが見つからない / TOML パース失敗 / `project.version` キー欠落」を全部 `except` で潰して `"unknown"` に逃がす設計にしておきます(上のサンプルはその形です)。

## 動的バージョニングを使っている場合

`setuptools-scm` / `hatch-vcs` / `versioneer` 等で git タグからバージョンを生成する構成でも、ビルド後の dist-info には確定バージョンが焼かれています。**ランタイムからの読み方は `importlib.metadata.version()` で全く同じ**で、CLI 側の実装はバージョン管理戦略に依存しません。

`pyproject.toml` の `[project]` に `dynamic = ["version"]` が入っているプロジェクトだと「TOML を直接パース」フォールバックは `project.version` が無くて失敗します。動的バージョニング採用時は fallback の存在意義が更に薄くなるので、`metadata.version()` のみで割り切るのが妥当です。

## まとめ

- SSOT は `pyproject.toml` の `project.version`、読み出しは `importlib.metadata.version("dist-name")`。
- Click は `@click.version_option(package_name=...)` で完全委譲。
- Typer は `is_eager=True` な callback。
- argparse は `action="version"`。
- distribution name と import name の食い違いに注意。
- フォールバックは uv ワークフローでは基本不要。動的バージョニング採用時は尚更。
- ライブラリ用途でなければ `__version__` 属性も不要。

## むすび: この記事は誰のためか

ここに書いた内容は、コーディングエージェント(Claude Code 等)はすでに全部知っています。`--version` をエミットする実装を頼めば、フレームワークに応じた正しいコードが返ってきますし、`_read_version()` のような二段フォールバックも当然のように提案してくれます。

問題は、エージェントが安全側に倒した提案をしてきたとき(典型的には fallback 付きの実装)に、人間側が「自分の運用前提だとそのフォールバックは不要だ」と即断するための判断材料を持っているかどうかです。`importlib.metadata.version()` が踏むコードパスと、踏まないコードパス(`PackageNotFoundError` 経路)が運用上どういう条件で出るかを言語化しておかないと、毎回エージェントの保険を漫然と受け入れて、要らない分岐が増えていきます。

この記事は、エージェント向けではなく、エージェントの提案にレビューを返す人間側のチェックリストとして書いています。uv 前提で配るアプリなら fallback 無しでよい、という結論を即座に出せるようにするのが主目的です。
