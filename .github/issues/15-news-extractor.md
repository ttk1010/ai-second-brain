# Issue #15: News Extractor（URL入力の知識抽出）

Labels: core, parser, llm
Milestone: Phase 2 — Educational Content

## Why
現状 URL 入力は分類されるだけで `unsupported` を返す（`backend/services/pipeline.py`）。Phase 2 の「News parser」を実装し、URL から教育的知識を抽出して Concept と対になる第二経路を用意する。ARCHITECTURE の News Pipeline（summary / technology / companies / impact / related concepts）に対応。

## Goal
URL を取得・本文抽出し、LLM で構造化フィールド（要約・技術・企業・影響・関連概念）を抽出する。`ConceptExtractor` と対になる `NewsExtractor` を実装する。

## Tasks
- [ ] `backend/parser/news_extractor.py` に `NewsExtractor` を実装（`ConceptExtractor` の構造に倣う）
- [ ] URL 取得＋本文抽出（取得失敗・非HTML・空本文を明示的にエラー処理。無音失敗禁止）
- [ ] LLM 抽出はプロバイダ抽象越し（`LLMProvider`）。プロンプトは `backend/prompts/extraction/news.py` に分離（PROMPT_STYLE_GUIDE 準拠）
- [ ] 出力 dataclass（`NewsExtraction`）を定義し、必須フィールド欠落時は `LLMError`
- [ ] LLM/HTTP をモック化した単体テスト（外部API・ネットワーク非依存でCIが通る）

## Definition of Done
- URL から妥当な構造化フィールドが抽出される
- 取得・解析の失敗が明示的に扱われる
- 外部API/ネットワークに接続せずテストが通る

## Notes
- KO への正規化と Pipeline 結線は #16。本 Issue は抽出まで。
- Research Paper / Documentation も当面 News 経路で暫定処理（ADR 0001）。
