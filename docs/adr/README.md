# Architecture Decision Records (ADR)

このディレクトリは AI Second Brain の重要な設計判断を記録する。

## 目的

- 設計判断とその理由を残し、将来「なぜこうなっているのか」を辿れるようにする。
- ドキュメント間で設計が食い違ったとき、どの決定が正かを明確にする。

## ルール

- 1つの決定につき1ファイル。`NNNN-kebab-title.md` 形式で連番を振る。
- 一度 Accepted になった ADR は書き換えない。決定を覆す場合は新しい ADR を作り、旧 ADR の Status を `Superseded by NNNN` に更新する。
- 各 ADR は `0000-template.md` の構成に従う。

## Status の値

- `Proposed` — 提案中
- `Accepted` — 採用済み
- `Superseded by NNNN` — 別の ADR に置き換えられた
- `Deprecated` — 廃止

## Index

| ADR | Title | Status |
| --- | ----- | ------ |
| [0001](0001-design-baseline.md) | Design baseline: terminology, pipeline scope, data ownership | Accepted |
| [0002](0002-vault-and-layout.md) | Vault location, Git tracking scope, and backend layout | Accepted |
| [0003](0003-graceful-degradation-of-enrichment.md) | Graceful degradation of enrichment (Educational Plan / Illustration) | Accepted |
| [0004](0004-news-ingestion-structured-extraction.md) | News ingestion: structured-source extraction, no headless browser | Accepted |
| [0005](0005-knowledge-organization-cost-model.md) | Knowledge organization: cost model, linker design, KO non-persistence | Accepted |
| [0006](0006-capture-interface-local-first.md) | Capture interface: local-first (Inbox queue + Claude Code Channels) | Accepted |
