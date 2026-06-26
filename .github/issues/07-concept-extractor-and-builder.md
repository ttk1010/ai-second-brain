# Issue #7: Concept Extractor と Knowledge Object Builder（プロバイダ抽象化込み）

Labels: core, parser, llm
Milestone: Phase 1 — Foundation

## Why
概念入力を Knowledge Object へ正規化する第一経路。CHARTER の「単一AIプロバイダに依存しない」原則を守るため、LLM/画像生成は抽象インターフェース越しに呼ぶ設計を最初から導入する。

## Goal
概念入力から Knowledge Object を生成する。LLM・画像生成をプロバイダ抽象越しに呼べる基盤を整える。

## Tasks
- [ ] `LLMProvider` インターフェースを定義（実装注入＝DI）し、OpenAI 実装を1つ用意
- [ ] `ImageProvider` インターフェースを定義（既定実装は `gpt-image-2`）。「品質×解像度→概算コスト」を返すユーティリティも持たせる
- [ ] `backend/parser/` に Concept Extractor を実装
- [ ] Knowledge Object Builder で抽出結果を #4 のスキーマに正規化
- [ ] プロンプトはコードに埋め込まず `backend/prompts/extraction/` のテンプレートに分離（PROMPT_STYLE_GUIDE 準拠）
- [ ] LLM/画像をモック化した単体テスト（外部API非依存でCIが通る）

## Definition of Done
- 概念入力 → 妥当な Knowledge Object が生成される
- プロバイダを差し替え可能（OpenAI依存がコア層に漏れない）
- 外部APIに接続せずにテストが通る

## Notes
- gpt-image-2 を既定とするが、`image_model` 設定で差し替え可能にする（gpt-image-1 は将来廃止予定のため）
