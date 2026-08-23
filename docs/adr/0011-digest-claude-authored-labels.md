# ADR 0011: ダイジェストのラベル/要約は Claude スキルで本文から執筆する

- Status: Accepted
- Date: 2026-07-26
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

ADR 0010 の月次ダイジェストは、イラスト内ラベルと一文要約を**記事タイトルだけ**から OpenAI(gpt-5.4) で生成していた。そのため記事の核心語（例「ヤコビアン予想」「Fable 5」）が落ち、内容を捉えないラベルになることがあった。`asb-relink`（ADR 0005）は「スキル＝Claude 推論・サブスク範囲・OpenAI 課金ゼロ＋決定論ヘルパー」の型を確立している。本文を読んで執筆すれば品質が上がり、テキスト生成の課金も無くせる。

## Decision

### A. 本文を読む執筆は Claude スキルで行う（二層構成）

`asb-digest` スキルを追加する（`asb-relink` と同型）：
1. `asb-digest fetch` が30日ランキング＋各記事本文を JSON 出力（`RankingFetcher` + `HttpArticleFetcher`、**OpenAI 不使用**）。
2. **Claude が本文を読み**、各記事の label（核心語を最低1語含む、完全な短い句）＋一文要約、全体所感・concepts・entities を執筆。
3. `asb-digest build --from FILE` が執筆 JSON から KO を構築 → ノート＋イラスト生成（`render_digest`）。

テキスト生成は Claude サブスク範囲（**OpenAI テキスト課金ゼロ**）。**画像のみ OpenAI 課金**（gpt-image-2。Claude はこのパイプラインでラスター画像を生成しない）。

### B. 全自動 `asb-digest`（OpenAI テキスト）は残す

無人 cron/launchd 実行はスキル（＝Claude Code セッションが必要）では回らないため、OpenAI がテキストも書く全自動パスを温存する。全自動パスの label プロンプトも「核心語を保持する」よう改善した（cron 品質の底上げ）。

### C. CLI はサブコマンド化（後方互換）

`asb-digest`（無し）＝全自動、`fetch`＝本文つき JSON、`build --from`＝執筆 JSON からの構築。無サブコマンドは従来どおり全自動なので後方互換。

## Consequences

- スキル経由では本文根拠で label（核心語入り）・要約の品質が上がり、テキスト生成の OpenAI 課金が無くなる（画像のみ課金）。
- 経路が2つになる：品質重視の Claude スキル（手動）／無人向けの全自動 OpenAI（cron）。役割が明確。
- `KnowledgePipeline.render_digest`（事前執筆データからの構築）を追加。`run_digest`（全自動）もこれを再利用。
- ラベルは `DigestItem.label`（画像用キャプション）。ノート本文には出さず、正確な一文要約のみ載せる（ADR 0010 の役割分担を継承）。

## Alternatives considered

- **OpenAI に本文を読ませて要約**：品質は上がるが 10 記事のフェッチ＋テキスト課金増。ADR 0010 の「タイトル起点・安価」と矛盾。Claude スキルなら課金ゼロで本文を読めるため不採用。
- **タイトルのみでプロンプト改善だけ**：安いが、タイトルに核心語が無い記事では限界。cron 用の底上げとしては採用しつつ、主経路はスキルにする。
- **全自動パスを廃止しスキルだけにする**：無人 cron が回らなくなるため不採用。両方維持。
