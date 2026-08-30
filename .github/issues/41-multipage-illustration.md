# Issue #41: イラストを複数ページ（観点ごとの連続解説）で生成するオプション

Labels: enhancement, image, planner, services

## Why
現状は **1ノート＝イラスト1枚**（`ko.outputs['illustration']` に1パス、Markdown「Illustration」節に1回埋め込み）。込み入った概念を1枚に詰め込むと情報過多になりがちで、「全体像→仕組み→具体例→注意点」のように **観点ごとの連続ページ** に分けられれば、ASB の狙い（わかりにくい概念をわかりやすく）をさらに伸ばせる。既定は1枚のまま、**オプトインのオプション** として追加する。

## 決定事項（すり合わせ済み）
- 成果物＝**観点ごとの連続解説ページ**（各ページ別テーマ・同一視覚言語で一貫）。
- 枚数は **単一フラグ `--pages`** で表現：
  - フラグ無し → **1ページ（現状どおり・完全後方互換）**
  - `--pages N` → **N ページ**（Planner が N 観点に分割）
  - `--pages auto` → **複数ページ・枚数は Planner が自動決定**（上限つき）
- 対象タイプ＝ **concept / news / comparison**。**digest は対象外**（1枚俯瞰が仕様＝ADR 0010）。
- 既定1ページ＝**課金・冪等性は現状のまま**。複数指定時のみ画像を N 回生成（N 倍課金）。

## 一貫性の実現方式（方式A：参照画像・確定）
公式ドキュメント（developers.openai.com / gpt-image-2）で以下を確認済み：
- `images.generate` の **`n` は同一プロンプトのバリエーション** のみ。各ページに別プロンプトを割り当てられないため **今回は非採用**。
- `images.edit` は **複数の参照画像を配列 `image: [...]` で受け取れる**。gpt-image-2 は **全入力画像を常に高フィデリティで処理**（`input_fidelity` は指定不要）ため、参照のスタイル/キャラが保たれやすい。
- Responses API のマルチターン（`previous_response_id` + `image_generation` tool）でも文脈保持は可能だが、テキストモデルのターンに載る分だけ課金・実装が重い → **本 Issue では採らない**（#29 等の対話的リファインメント向き）。

**採用＝方式A**：1枚目は `generate`、2枚目以降は **それまでのページを参照画像として `edit`** に渡して逐次生成する。画像 API だけで完結し、既存の `ImageProvider` 抽象への追加が最小で済む。どの方式でも **ページ1枚ごとに別コール＝N回課金** は不変。

## 提案する設計
- **data model**
  - `EducationalPlan` に `pages: list[PageSpec]` を追加（各 `PageSpec` = `title` / `learning_objective` / `visualization`（記述）/ `aspect_ratio`）。1枚時は `pages` 空で従来どおり。
  - `KnowledgeObject` に `illustrations: list[str]`（Vault 相対パス・順序保持）を追加。`outputs['illustration']` は1枚目＝後方互換として残す（参照のみ・ADR 0001）。
- **planner**：`--pages` の指定（数値 / auto / 無し）をパイプライン経由で受け取り、複数時は N（または自動決定した枚数、**上限=6**）の観点分割を生成。
- **image provider**：`ImageProvider.generate(..., reference_images: list[Path] | None = None)` を拡張。`OpenAIImageProvider` は `reference_images` があれば `images.edit(model=..., image=[...], prompt=...)`、無ければ従来 `images.generate`。
- **prompt**：`build_illustration_page_prompt(ko, page, index, total, guidance)` を追加。「これはシリーズの **k/n 枚目**、テーマは○○、**同一スタイル・同一キャラ・同一配色を維持**」をプロンプトに注入。
- **storage**：`IllustrationWriter` を複数ページ対応。1枚目→それを参照に2枚目→…と **逐次生成**（前ページ群を `reference_images` に渡す）。ファイルは `-p2`,`-p3`… のサフィックス。返り値はパスのリスト。`--overwrite` 時は **旧セットを掃除** してから書く（#39 の二重化バグと整合）。
- **markdown**：`_illustration()` を全ページ順次埋め込みに拡張（各ページに小見出し/キャプション）。1枚時は従来表記のまま。
- **CLI**：`asb` / `asb-inbox` に `--pages {N|auto}`（既定=1）を追加。`--no-image` が最優先（複数指定より優先して画像を作らない）。
- **cost**：README/docs に「複数ページ＝画像 N 回課金・`n` は非採用・一貫性は参照画像方式」を明記。上限で暴走防止。
- **ADR 0012**：不変条件「1KO=1イラスト」とコストモデルの変更、方式A（参照画像）の採用理由を記録。

## Tasks
- [ ] `EducationalPlan.pages`（`PageSpec`）追加 ＋ `KnowledgeObject.illustrations`
- [ ] `ImageProvider.generate(reference_images=...)` 拡張、`OpenAIImageProvider` の `images.edit` 経路
- [ ] Planner：観点分割（`--pages N` / auto / 上限=6）
- [ ] `build_illustration_page_prompt`（シリーズ一貫性の文脈注入）
- [ ] `IllustrationWriter` 複数ページ逐次生成・命名・旧セット掃除
- [ ] `MarkdownGenerator` 複数ページ埋め込み
- [ ] CLI `--pages {N|auto}`（`asb` / `asb-inbox`）
- [ ] 単体テスト（1枚=後方互換 / N枚 / auto / --no-image優先 / overwrite掃除 / 参照画像が2枚目以降に渡る）
- [ ] README/docs にコスト注記、ADR 0012

## Definition of Done
- オプション無し＝従来どおり1枚（課金・出力・冪等性が不変）
- `--pages N` / `--pages auto` で観点分割の複数ページが **一貫スタイル** で生成される（前ページを参照画像として引き継ぐ）
- 複数ページのコスト（N倍・参照画像方式・`n`非採用）が明文化されている
- 外部API非依存でテストが通る（モック provider）

## フェーズ / 扱い
イラスト体験の強化。番号付きフェーズには束ねず単独 enhancement（`--pages` はオプトイン）。`images.edit`（複数参照・高フィデリティ）の知見は #29（対話的リファインメント）にも波及（同 Issue に追記メモ済み）。
