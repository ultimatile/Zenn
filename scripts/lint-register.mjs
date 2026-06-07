#!/usr/bin/env node
// register-mode-aware textlint gate (manual, NOT pre-commit).
//
// Why this exists: the preset rule `no-mix-dearu-desumasu` can only pin ONE 文体
// (本文=ですます / 箇条書き=である by default), which hard-codes almost敬体 and makes
// all敬体 / all常体 fail. The pre-commit config therefore disables that rule, and this
// script restores mechanical 文体 enforcement per article: it reads each article's
// `register` frontmatter key (almost|keitai|joutai; default almost) and runs textlint
// with `no-mix-dearu-desumasu` configured for that mode. `register` is an unknown key
// that Zenn ignores (verified by an actual push of a published:false draft).
//
// Usage: node scripts/lint-register.mjs [file ...]   (no args = all articles/*.md)

import { readFileSync, writeFileSync, readdirSync, unlinkSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

// 文体 mode -> no-mix-dearu-desumasu options. preferInHeader is left at the rule
// default so 体言止め headings are not flagged.
const MODES = {
  almost: { preferInBody: "ですます", preferInList: "である" },
  keitai: { preferInBody: "ですます", preferInList: "ですます" },
  joutai: { preferInBody: "である", preferInList: "である" },
};

function modeOf(file) {
  const text = readFileSync(file, "utf8");
  const fm = text.match(/^---\n([\s\S]*?)\n---/);
  if (!fm) return "almost";
  const r = fm[1].match(/^register:\s*["']?([A-Za-z-]+)["']?\s*$/m);
  if (!r) return "almost";
  if (!(r[1] in MODES)) {
    console.error(`warning: ${file}: unknown register "${r[1]}", treating as almost`);
    return "almost";
  }
  return r[1];
}

const base = JSON.parse(readFileSync(".textlintrc.json", "utf8"));

let files = process.argv.slice(2);
if (files.length === 0) {
  files = readdirSync("articles")
    .filter((f) => f.endsWith(".md"))
    .map((f) => join("articles", f));
}

const byMode = {};
for (const f of files) (byMode[modeOf(f)] ??= []).push(f);

let failed = false;
for (const [mode, modeFiles] of Object.entries(byMode)) {
  const cfg = structuredClone(base);
  cfg.rules["preset-ja-technical-writing"]["no-mix-dearu-desumasu"] = MODES[mode];
  // rulePaths in the config are resolved relative to the config file's location;
  // the temp config lives in tmpdir, so absolutize prh's path back to the repo.
  if (cfg.rules.prh?.rulePaths) {
    cfg.rules.prh.rulePaths = cfg.rules.prh.rulePaths.map((p) => resolve(p));
  }
  const cfgPath = join(tmpdir(), `textlintrc-register-${mode}.json`);
  writeFileSync(cfgPath, JSON.stringify(cfg));
  console.log(`\n# register=${mode} (${modeFiles.length} file(s))`);
  try {
    execFileSync("node_modules/.bin/textlint", ["-c", cfgPath, ...modeFiles], {
      stdio: "inherit",
    });
  } catch {
    failed = true;
  } finally {
    unlinkSync(cfgPath);
  }
}

process.exit(failed ? 1 : 0);
