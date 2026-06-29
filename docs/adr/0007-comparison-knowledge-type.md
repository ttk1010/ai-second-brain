# ADR 0007: 比較（Comparison）という知識タイプ

- Status: Accepted
- Date: 2026-06-29
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

「GPT vs Claude vs Gemini」のように、1つの枠組みで複数対象を比較する内容を Vault に残したい要望がある。従来の入力タイプは Concept / News のみで、比較を入力しても自由記述の概念ノートになり、比較対象・比較軸・比較表といった構造を持てなかった（Issue #28）。

トリガー方式・スキーマ・保存フォルダ・比較表の粒度を決める必要がある。あわせて Vault のフォルダ番号体系がこれまで暗黙だった点も整理する。

## Decision

### A. トリガーは「`compare:` 接頭辞」を中核、`--compare` は糖衣

`classify()` が入力先頭の `compare:`（大文字小文字無視）を検出して `SourceType.COMPARISON` に振り分ける。接頭辞はプレーンテキストなので **CLI / Inbox スタブ / Telegram(Channels) の全経路で透過的に機能する**（分岐点を `classify()` に一元化する既存設計を維持）。CLI の `--compare` は入力を `compare:` 形へ正規化するだけの薄い糖衣とし、実体の経路は1つに保つ。Telegram からは `asb-capture` スキルが自然文を解釈して `--compare` 付き実行に変換する。

### B. スキーマは items / rows / recommendation

Knowledge Object に任意フィールド `comparison`（`ComparisonData`）を追加する：

- `items: list[str]` — 比較対象（列）
- `rows: list[ComparisonRow]`（`dimension: str`, `cells: list[str]`、cells は items と同順・同数）— 表の行
- `recommendation: str` — どんな時にどれを選ぶか

表ネイティブな行持ちにより Markdown 比較表を決定論的に描画できる。比較対象は `concepts` にも入れ、各対象のノートへリンクする。ADR 0001 の「スキーマを安易に増やさない」に該当するため、本 ADR と DATA_MODEL.md で明示する。

### C. 保存は `04 Comparisons`。フォルダ番号体系を明文化

`SourceType.COMPARISON` → `04 Comparisons`。あわせて Vault のフォルダ番号設計を次のとおり定める（02/03/05 は細分類器が出来るまで予約。現状 Concept は 01 に集約）：

```
00 Inbox / 01 Concepts / 02 Models* / 03 Tools* / 04 Comparisons /
05 Companies* / 06 News / 07 Papers          （* = 予約・将来の内容分類で使用）
```

### D. 比較表の粒度は「短い事実セル」

各セルは数語または数値の事実（例：コンテキスト長「400K」、価格、強み）。記号評価（◎○△×）は技術比較では潰れやすいため既定にしない（総合評価の補助としては将来追加余地あり）。

## Consequences

- 比較が第一級の知識タイプになり、比較表付きノートが `04 Comparisons` に生成され、各対象ノートへリンクして知識グラフに繋がる。
- 全キャプチャ経路（CLI/Inbox/Telegram）で同一トリガーが効く。`--compare` は人間が CLI で打つ時の利便。
- KO スキーマが1フィールド増える（任意・比較ノート以外は None）。frontmatter には影響せず、ADR 0001 の outputs 方針とも矛盾しない。
- フォルダ番号体系が文書化され、将来の細分類（Models/Tools/Companies）の置き場が定まる。

## Alternatives considered

- **トリガーを `--compare` フラグのみ / サブコマンド `asb compare`**：CLI 専用で Inbox スタブや素の Telegram メッセージに乗らない。全経路統一のため接頭辞を中核に採用。
- **「vs」自動判定**：曖昧（概念名に "vs" を含む等）で誤爆するため不採用。
- **スキーマを対象中心（items に attrs を持つ）**：pros/cons は自然だが表化にピボットが要る。表ネイティブな行持ち（D 案）を採用。
- **記号評価セル**：一覧性は高いが技術比較ではニュアンスを失うため既定にしない。
