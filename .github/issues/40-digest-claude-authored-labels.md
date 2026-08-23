# Issue #40: 月次ダイジェストのラベル/要約を Claude スキルで本文から執筆する

Labels: enhancement, services, documentation

## Why
#39 のダイジェストは、イラスト内タイトル（label）と一文要約を **記事タイトルだけ**から OpenAI(gpt-5.4) で生成している。そのため記事の核心語（例：「ヤコビアン予想」「Fable 5」）が落ちて、内容を捉えないラベルになることがある。

`asb-relink` と同じく **Claude Code スキル（サブスク範囲・OpenAI テキスト課金ゼロ）** で **記事本文を読んで** label・一文要約・所感を執筆すれば、品質が上がり、テキスト生成の課金も無くなる。イラストは gpt-image-2（OpenAI）で描くため、画像の課金のみ残る。

## Goal
本文を根拠に、Claude が各記事の label（核心語を含む短い完全な句）＋一文要約＋全体所感を執筆し、それを決定論ヘルパーがノート＋イラストに落とす経路を追加する。既存の全自動 `asb-digest`（OpenAI テキスト）は cron 用に温存する（無人実行にはスキルではなくこちらを使う）。

## 決定事項（すり合わせ済み）
- 方式 **B（Claude スキルが本文を読む）**。`asb-relink` と同型（スキル＝Claude 推論＋決定論 CLI）。
- テキスト生成は Claude（サブスク・無料）、**画像のみ OpenAI 課金**。
- 全自動 `asb-digest`（OpenAI テキスト）は残す（無人 cron 用）。

## 提案する設計
CLI をサブコマンド化（後方互換：サブコマンド無しは従来の全自動）:
- `asb-digest fetch --top N [--month M] [--chars N]` … 30日ランキング＋各記事本文を JSON 出力（`RankingFetcher` + `HttpArticleFetcher`。ネットワークのみ・OpenAI 不使用）。
- `asb-digest build --from FILE [--no-image] [--overwrite]` … Claude 執筆 JSON（period, overview, concepts, entities, items:[{rank,title,url,label,summary}]）から KO を構築 → ノート＋イラスト生成（画像のみ OpenAI）。
- `asb-digest`（無し）… 従来の全自動（OpenAI テキスト＋画像）。

スキル `.claude/skills/asb-digest/SKILL.md`:
1. `fetch` を実行して本文つき JSON を得る。
2. 本文を読み、各記事の label（**核心語＝固有名詞/主題を最低1語含む**、完全な句、鉤括弧を閉じる、~8-16字）＋一文要約、全体所感・concepts・entities を執筆。
3. 執筆 JSON を一時ファイルに書き、`build --from` を実行。
4. 生成物パスを簡潔に報告。

パイプライン：`render_digest(period, ranked, extraction, *, top, overwrite)` を追加（冪等チェック→ `from_digest` → finalize、教育設計はスキップ）。`run_digest` はこれを再利用。

## Tasks
- [ ] `KnowledgePipeline.render_digest`（事前執筆データからの構築経路）
- [ ] `asb-digest` サブコマンド化：`fetch`（本文つき JSON）/ `build`（JSON→ノート＋イラスト）/ 既定=全自動
- [ ] `.claude/skills/asb-digest/SKILL.md`（本文を読んで label/要約/所感を執筆）
- [ ] 全自動パスの label プロンプトも「核心語を保持」に軽く改善（cron 用の品質底上げ）
- [ ] 単体テスト（fetch の JSON 生成＝モック fetcher、build の JSON→ノート、render_digest、後方互換）
- [ ] README/docs に2経路（全自動 cron / Claude スキル）を明記。ADR 追記

## Definition of Done
- スキル経由で、本文根拠の label（核心語入り）と一文要約でダイジェストが生成される
- テキスト生成は OpenAI 課金ゼロ（画像のみ課金）
- 従来の全自動 `asb-digest` は不変（後方互換）。無人 cron で使える
- 外部API/ネットワーク非依存でテストが通る

## フェーズ / 扱い
#39 の品質改善（ラベル）。`asb-relink`（ADR 0005 のスキル＝サブスク・無料）と同じ二層構成の適用。番号付きフェーズに束ねず単独 enhancement。
