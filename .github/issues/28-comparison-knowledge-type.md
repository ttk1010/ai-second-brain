# Issue #28: 比較ノート（Comparison という知識タイプ）

Labels: enhancement, parser, models, markdown

## Why
「GPT vs Claude vs Gemini」のように、**1つの枠組みの中で複数の対象を比較**する内容を Vault に残したい場面がある。現状の入力タイプは Concept / News のみで、比較を入力しても自由記述の概念ノートになるだけ。比較対象の列挙・比較軸・各対象の属性・比較表といった**構造**が無く、第一級の比較知識として扱えない。

## Goal
複数対象を比較する入力から、構造化された Comparison の Knowledge Object とノート（**比較表**を含む）を生成する。各対象は既存の概念ノートへリンクし、知識グラフに繋がる。

## 提案する設計（実装時に Open questions を確定）
- **新しい SourceType `COMPARISON`** を追加し、専用フォルダ（例 `04 Comparisons`）へ振り分け
- **トリガー**：明示的に比較モードを指定（自動判定は曖昧で脆いため避ける）。第一候補は `asb --compare "GPT, Claude, Gemini"`（入力＝比較対象リスト。`,` や `vs` 区切り）
- **ComparisonExtractor**：LLM で title / short_title / 比較対象（items）/ 比較軸（dimensions）/ 各 item×dimension の評価（matrix）/ summary / background / key_takeaways /「どんな時にどれを選ぶか」を抽出（Concept/News と同じくプロバイダ抽象越し・JSON）
- **KO スキーマ拡張**：比較構造を表す `comparison`（items / dimensions / cells など）を追加。「スキーマを安易に増やさない」(ADR 0001) に照らし、形は要議論（短い ADR を起こす可能性）
- **Markdown**：標準セクションに加え **比較表（Markdown table：行=比較軸／列=対象）** を描画。プロンプト同様テンプレートに分離
- **リンク**：比較ノートから各対象の概念ノートへ `[[GPT]]` 等でリンク（linker / Obsidian backlink と整合）

## Tasks
- [ ] `SourceType.COMPARISON` と `04 Comparisons` フォルダ振り分けを追加
- [ ] トリガー（`--compare` 等）を CLI / classifier に実装
- [ ] `backend/prompts/extraction/comparison.py` と `ComparisonExtractor`
- [ ] KO に比較構造を追加（DATA_MODEL.md 更新。必要なら ADR）
- [ ] Builder（`from_comparison`）と pipeline 結線（plan→illustrate→markdown→vault の共通後段を再利用）
- [ ] Markdown に比較表セクションを追加
- [ ] モック LLM・一時 Vault での単体テスト（外部API非依存）／実 API で1件確認
- [ ] README / docs に使い方を追記

## Definition of Done
- 比較入力から、比較表を含む構造化ノートが生成され、`04 Comparisons` に保存される
- 各対象が既存ノートへリンクされる
- 外部API非依存でテストが通る

## Open questions（実装前に決める）
1. トリガー UX：`--compare` フラグ / `asb compare` サブコマンド / 入力中の「vs」自動判定 のどれにするか
2. KO の比較スキーマの形（items / dimensions / cells の構造、ADR の要否）
3. Vault フォルダ名・番号（`04 Comparisons` で良いか）
4. 比較表をどこまで詳細にするか（◎○△× 記号 / 短文セル / 自由記述）

## Notes
- マイルストーン無しの単独 enhancement。将来「論文深掘り」「チュートリアル」等の知識タイプが増えるなら、まとめて1テーマに再編する案もある。
