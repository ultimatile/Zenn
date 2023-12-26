---
title: "LaTeXで縦横に結合セルを持つ表の作成"
emoji: "⛄️"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [latex]
published: false
---

## はじめに
### `multirow`による実装
```tex:
\documentclass[varwidth=\maxdimen, border=5pt]{standalone}
\usepackage{multirow}
\usepackage{graphics}
\begin{document}
    \begin{table}
        \newcommand{\myverpad}{-0.15ex}
        \begin{tabular}{|c|c|c|c|}\hline
            \multicolumn{2}{|c|}{\multirow{2}{*}{table}}  & \multicolumn{2}{|c|}{column} \\\cline{3-4}
            \multicolumn{2}{|c|}{}                        &  \multirow{1}{*}[\myverpad]{1} & \multirow{1}{*}[\myverpad]{2} \\\hline
            \multirow{2}{*}{\rotatebox{90}{row\ }}    & \multirow{1}{*}[\myverpad]{1} & \multirow{1}{*}[\myverpad]{11} & \multirow{1}{*}[\myverpad]{12} \\\cline{2-4}
                                                        & \multirow{1}{*}[\myverpad]{2} & \multirow{1}{*}[\myverpad]{21} & \multirow{1}{*}[\myverpad]{22} \\\hline
        \end{tabular}
    \end{table}
\end{document}
```

### `tabularray`による実装
```tex:
\documentclass[border=5pt]{standalone}
\usepackage{tabularray}
\usepackage{graphics}
\begin{document}
  \begin{tblr}{
      rowsep=0pt,
      colspec={|c|c|c|c|},
      cell{1}{1} = { r = 2, c = 2 }{ halign = c, valign = m },
      cell{1}{3} = { r = 1, c = 2 }{ halign = c, valign = m },
      cell{3}{1} = { r = 2, c = 1 }{ halign = c, valign = m },
      hlines
    }
    table & --- & column & --- \\
    ---  & --- & 1 & 2 \\
    \rotatebox{90}{row\ } & 1 & 11 & 12 \\
    --- & 1 & 21 & 22 \\
  \end{tblr}
\end{document}
```

## 補足
- `\graphics`は`rotatebox`で文字を回転させるために必要です.

## おわりに
実は`tabularray`を使うともっと簡単にできるっぽい
https://qiita.com/Yarakashi_Kikohshi/items/b645de659cbfe8c12b36

## 参考文献
https://zenn.dev/ganariya/articles/latex-multi-row-and-column
