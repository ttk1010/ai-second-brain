# Issue #16: News パイプライン統合（Builder + Pipeline 結線）

Labels: core, parser, services
Milestone: Phase 2 — Educational Content

## Why
`NewsExtractor`（#15）の出力を Knowledge Object に正規化し、Pipeline の `unsupported` 分岐を実処理へ置き換えて URL 入力を E2E で通す必要がある。Downstream は入力がキーワードかURLかを意識しない（ARCHITECTURE）。Phase 1 の成功基準「URL入力でノートが保存される」を実際に満たす。

## Goal
News 抽出結果を KO に正規化し、URL 入力で Markdown（＋イラスト）ノートが Vault に保存されるところまで結線する。

## Tasks
- [ ] `KnowledgeObjectBuilder` に `from_news()` を追加（#4 のスキーマへ正規化、`source.type = NEWS`）
- [ ] `KnowledgePipeline.run()` の News 分岐を実処理に置換（classify→news_extract→build→plan→markdown(+illustration)→vault）
- [ ] News ノートの保存先フォルダ規則を確認（`folder_for` が NEWS を適切に振り分けること）
- [ ] `PipelineStatus` / 戻り値が News でも一貫すること
- [ ] モック LLM・モック ImageProvider・一時 Vault を使った E2E テスト（URL入力）

## Definition of Done
- URL 入力から KO が生成され、ノートが Vault の正しいフォルダに保存される
- Concept と News が同じ下流（Planner/Markdown/Storage）を共有する
- 外部API非依存でテストが通る

## Notes
- これで Phase 2 の News 系統が E2E で完成する。
