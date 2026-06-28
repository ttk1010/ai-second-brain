# ADR 0003: エンリッチ処理のグレースフル劣化（Educational Plan / Illustration）

- Status: Accepted
- Date: 2026-06-28
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

Phase 2 で Educational Planner（教育設計）とイラスト生成を Concept / News パイプラインに統合した。どちらも外部 LLM / 画像 API に依存し、失敗しうる（不正な JSON 応答、API エラー等）。

ここで「ノート生成全体を失敗させるか／一部欠落でも生成を続けるか」という方針が必要になった。CHARTER の「AI-assisted, not AI-dependent」と、CLAUDE.md の「Fail fast」「無音で失敗を握りつぶさない」をどう両立させるかが論点。

## Decision

パイプラインの工程を **コア工程** と **エンリッチ工程** に分け、扱いを変える。

### コア工程は fail-fast

入力分類・抽出（Concept/News）・Knowledge Object 構築・Markdown 生成・Vault 書き込みは、失敗したらエラーで停止する。これらが欠けるとノートが成立しないため。

### エンリッチ工程は fail-soft（劣化して継続）

Educational Plan の生成とイラスト生成は **任意（optional）の注入コンポーネント**とし、失敗しても**警告ログを残してノート生成は継続**する。

- `EducationalPlanner` の失敗 → `educational_plan = None` のままノートを生成。
- `IllustrationWriter` の失敗（`ImageError`） → イラストなしでノートを生成（Markdown はプレースホルダにフォールバック）。
- `KnowledgePipeline` はこれらを optional 引数で受け取り、未注入なら工程をスキップする（テストや最小構成でも動く）。

失敗は必ずログに記録し、無音で握りつぶさない。

## Consequences

- 1回の LLM/画像 API の不調でノート生成全体が落ちることがなくなり、知識キャプチャが頑健になる。
- optional 注入により、ユニットテストはモック/未注入で軽量に書け、CI が外部 API に依存しない。
- 「失敗 = 例外」を期待する将来の実装者が、この fail-soft を誤って fail-fast に「修正」しないよう、本 ADR で意図を明示する。
- 劣化時は plan やイラストを欠いたノートになる。Phase 3 以降の処理（リンク等）はこれら欠落を前提に動く必要がある。

## Alternatives considered

- **全工程 fail-fast**: 一時的な API 不調でノートが作れず、日常利用の体験を損なうため不採用。
- **失敗を黙って無視（ログなし）**: 問題の発見が遅れ、CLAUDE.md「無音で失敗を握りつぶさない」に反するため不採用。必ずログを残す。
- **リトライ機構を組み込む**: Phase 2 時点では YAGNI。必要になれば別途検討する。
