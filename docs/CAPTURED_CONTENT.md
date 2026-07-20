# ログイン必須サイトの取り込みガイド（Captured Content）

ログイン（無料会員登録を含む）が必要なサイトの記事は、`asb` が URL を直接
フェッチできません。その場合は**自分のログイン済みブラウザで本文を取得して
ASB に渡す**ことで、フェッチをスキップして通常どおり News ノート
（`06 News/`、`source` は元 URL）を生成できます
（[ADR 0009](adr/0009-captured-content-ingestion.md)）。

ASB は**認証情報も Cookie も一切扱いません**。渡された本文テキストを信頼して
要約するだけです。ペイウォール・CAPTCHA・MFA の回避は行いません。正当に
アクセスできるコンテンツのみを、各サイトの利用規約の範囲で取り込んでください。

取り込み方法は 3 つあります。

---

## 方法 1: Inbox スタブ（Obsidian から）

`00 Inbox/` にスタブノートを置き、`uv run asb-inbox` で処理します。
frontmatter の `source:` に元 URL、本文に記事テキストを貼り付けます。

```markdown
---
source: https://atmarkit.itmedia.co.jp/...
title: 記事タイトル   # 省略可
---
（記事本文をここに貼り付け）
```

成功するとスタブは消費（削除）され、News ノートが生成されます。

記事ページ上で実行すると「frontmatter ＋ 本文」をクリップボードにコピーする
ブックマークレット：

```javascript
javascript:(()=>{const t=(document.querySelector('article')||document.body).innerText.trim();const s=`---\nsource: ${location.href}\ntitle: ${document.title}\n---\n\n${t}`;navigator.clipboard.writeText(s);})();
```

## 方法 2: CLI（`--captured-from`）

本文は `--text-file` / 位置引数 / 標準入力のいずれかで渡します。

```bash
uv run asb --captured-from "https://atmarkit.itmedia.co.jp/..." --text-file article.txt

# クリップボードから直接（macOS）:
pbpaste | uv run asb --captured-from "https://atmarkit.itmedia.co.jp/..."
```

- `--title "記事タイトル"` でタイトルを補える（省略可）。
- `--guidance` / `--no-image` / `--overwrite` は通常どおり併用可能。
- 冪等性は URL 一致で効く（同じ URL の再実行はスキップ）。

## 方法 3: Claude Code ＋ Claude in Chrome（コピペ不要）

[Claude in Chrome](https://chromewebstore.google.com/detail/fcoeoabgfenejglbffodgkkbkcdhcgfn)
拡張機能を使うと、Claude Code が**あなたの Chrome のログイン済みセッション**で
記事本文を読み取り、そのまま方法 2 の CLI を実行してくれます。手作業の
コピペが不要になります。

1. 拡張機能をインストールし、Chrome の Claude サイドパネルで **Claude Code と
   同じアカウント**にサインインする。
2. 対象サイトに Chrome でログインしておく。
3. Claude Code に「この記事の KO を生成して（URL）。ログインが必要な記事です」
   のように依頼する。Claude Code が Chrome 内にセッション用タブを開いて本文を
   読み取り（Cookie はブラウザプロファイル共有なのでログイン状態が引き継がれる）、
   `--captured-from` で取り込む。

補足：

- Claude Code が見えるのは**セッション専用のタブグループ**だけ。手動で作った
  タブグループやその他のタブは見えないため、参考にしてほしいページがあれば
  URL をチャットで渡す。
- この方法でも認証情報を入力するのは人間側で、Claude Code / ASB はログイン
  操作を行わない（ADR 0009 の方針の範囲内）。

---

## トラブルシューティング

- **「この記事は会員限定です」までしか取れない** — ブラウザ側でログインが
  切れている。サイトにログインし直してから再取得する。
- **同じ URL で内容を作り直したい** — `--overwrite` を付けて再実行する。
- その他は [TROUBLESHOOTING.md](TROUBLESHOOTING.md) を参照。
