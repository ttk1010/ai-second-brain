# Issue #17: Background / Key Takeaways の実体化

Labels: core, output, markdown, llm
Milestone: Phase 2 — Educational Content

## Why
標準テンプレートの Background と Key Takeaways セクションは現状すべて `PLACEHOLDER` のまま描画される（`backend/markdown/generator.py`）。見出しだけで中身が空のため、Phase 2 成功基準「一貫した教育的スタイルで全ノートが揃う」を満たせない。これらを実際の教育内容で埋める。

## Goal
- Background: 概念/ニュースが重要な理由・登場の経緯・前提知識を説明する散文
- Key Takeaways: 読者が押さえるべき要点の箇条書き（3〜5項目）
を Knowledge Object のデータから生成し、Markdown に描画する。

## Tasks
- [ ] 抽出層（`ConceptExtractor` / `NewsExtractor`）の LLM 出力に `background` と `key_takeaways` を追加（プロンプトテンプレート更新、PROMPT_STYLE_GUIDE 準拠）
- [ ] Knowledge Object に該当フィールドを保持（#4 スキーマ拡張、`DATA_MODEL.md` を更新）
- [ ] `MarkdownGenerator` の `_background` / `_key_takeaways` を、データがある場合に実内容で描画、無ければ従来プレースホルダ
- [ ] 入力は Knowledge Object のみ（プレゼン情報をモデルへ逆流させない、ADR 0001）
- [ ] スナップショット/単体テストを更新（決定的出力）

## Definition of Done
- 生成ノートの Background / Key Takeaways に実内容が入る
- データが無い場合も安全にプレースホルダで描画される（後方互換）
- 決定的出力のテストが通る

## Notes
- イラスト系統（#11〜#14）とは独立。仕上げとして単独でも並行でも実装可能。
- `DATA_MODEL.md` のスキーマ更新を忘れないこと。
