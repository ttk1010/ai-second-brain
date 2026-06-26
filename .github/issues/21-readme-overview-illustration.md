# Issue #21: README 用の概要イラスト（OSS公開準備）

Labels: documentation, illustration
Milestone: (none — OSS release prep / backlog)

## Why
将来 OSS として公開する際、このリポジトリのコードで「何ができるか」を一目で伝えたい。本プロジェクトが生成するイラストと同じテイスト（hand-drawn / soft colors / white background / textbook-inspired、PROMPT_STYLE_GUIDE 準拠）で、システム全体像を1枚にまとめて README 冒頭に掲載する。

## Goal
入力（概念/URL）→ Knowledge Object → 教育設計 → 出力（Markdown / イラスト / Vault）の流れを、プロジェクト固有の視覚言語で1枚に表現したイラストを README に貼る。

## Tasks
- [ ] 図解内容の設計（パイプライン全体像。何ができるかが伝わること）
- [ ] 既存のイラストスタイル（`ILLUSTRATION_STYLE`）に揃えて生成（必要なら専用プロンプト）
- [ ] 画像をリポジトリ内の適切な場所（例: `docs/assets/`）に配置（Vault ではなくコードリポジトリ）
- [ ] README 冒頭に埋め込み、代替テキストを付与

## Definition of Done
- README にプロジェクト概要イラストが表示される
- スタイルが生成ノートのイラストと一貫している
- 画像はコードリポジトリで管理される（知識データではないため Vault 対象外）

## Notes
- 記録のみ。OSS 公開準備のタイミングで実施。番号付きロードマップ・フェーズには含めない。
