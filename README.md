# Zenn CLI

* [📘 How to use](https://zenn.dev/zenn/articles/zenn-cli-guide)

# 記事作成

```bash:
npx zenn new:article --slug 記事のスラッグ --title タイトル --type tech --emoji 🦀
```

# preview

```bash:
npx zenn preview
```

# セットアップ

```bash:
npm install
```

zenn-cli の依存と、pre-commit フック（textlint で表記ゆれを autofix）に必要な依存がインストールされ、フックも有効化される（`pre-commit install` 相当は不要）。textlint・フックの運用詳細は [CLAUDE.md](./CLAUDE.md) を参照。
