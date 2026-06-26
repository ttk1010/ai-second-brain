# Issue #18: 生成ノートの本文が default_language に従わない（不具合）

Labels: bug, llm, prompts
Milestone: (none — bug fix)

## Why
`config/settings.toml` の `default_language = "ja"` を設定しても、生成されるノート本文（summary / background / key_takeaways など）が英語で出力される。frontmatter には `language: ja` が入るのに、実際の出力言語が設定と食い違っている。実APIテスト（Transformer / ledge.ai 記事）で確認。

## Goal
`default_language` が抽出・教育設計の出力言語を実際に制御するようにする。`ja` 設定なら日本語、`en` 設定なら英語で本文が生成される。

## Tasks
- [ ] 抽出/計画プロンプト（concept / news / planning）に「指定言語で記述せよ」という指示を渡せるようにする（プロンプトはテンプレートに分離、PROMPT_STYLE_GUIDE 準拠）
- [ ] `language` を Extractor / Planner → プロンプトビルダーまで伝搬（パイプラインは既に `language` を保持）
- [ ] 既定は `ja`。タグ等の構造値ではなく散文セクションの言語を制御する
- [ ] モックLLMで「プロンプトに言語指示が含まれる」ことを検証する単体テスト

## Definition of Done
- `default_language = "ja"` で本文が日本語、`en` で英語になる
- プロンプトに言語指示が確実に渡る（テストで担保）
- 外部API非依存でテストが通る
