# Issue #13: Image Provider 実装（gpt-image-2）

Labels: core, image, llm
Milestone: Phase 2 — Educational Content

## Why
`backend/image/base.py` は `ImageProvider` 抽象インターフェースのみで、具体実装が無い（Phase 1 で意図的に未実装）。Phase 2 のイラスト生成にはこの抽象を満たす OpenAI 実装が必要。CHARTER の「単一AIプロバイダに依存しない」原則を守り、コア層に OpenAI 依存を漏らさない。

## Goal
`ImageProvider.generate()` を `gpt-image-2` で実装し、プロンプトから画像を生成して指定パスに書き出す。

## Tasks
- [ ] `backend/image/` に `OpenAIImageProvider`（`gpt-image-2`）を実装
- [ ] `image_model` 設定で差し替え可能にする（既定 `gpt-image-2`）
- [ ] `AspectRatio` / `ImageQuality`（`image_quality`）を生成パラメータに反映
- [ ] `openai` SDK は遅延 import（テスト/CI が API キー無しで動くこと、Phase 1 の LLM 実装に倣う）
- [ ] 失敗時は `ImageError` で明示的に失敗させる（無音失敗禁止）
- [ ] 画像APIをモック化した単体テスト（外部API非依存でCIが通る）

## Definition of Done
- プロンプトから画像が生成され `output_path` に書き出される
- プロバイダを差し替え可能（OpenAI依存がコア層に漏れない）
- 外部APIに接続せずテストが通る

## Notes
- gpt-image-2 を既定とするが設定で差し替え可能（#7 の Notes に準拠）。
- コスト感応のため `image_quality` の既定は MEDIUM（settings 既定）。
