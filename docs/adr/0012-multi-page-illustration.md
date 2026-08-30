# ADR 0012: 複数ページのイラスト（観点ごとの連続解説）

- Status: Accepted
- Date: 2026-08-30
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

これまで **1つの Knowledge Object につきイラストは1枚**で、`ko.outputs['illustration']` に単一パスを持ち、Markdown の「Illustration」節に1回だけ埋め込んでいた。込み入った概念を1枚に詰め込むと情報過多になりやすい。「全体像→仕組み→具体例→注意点」のように **観点ごとの連続ページ** に分けられれば、ASB の狙い（わかりにくい概念をわかりやすく）を伸ばせる（Issue #41）。

OpenAI 画像 API（gpt-image-2）の仕様を公式ドキュメントで確認した：

- `images.generate` の `n` は **同一プロンプトのバリエーション** のみで、各ページに別プロンプトを割り当てられない。
- `images.edit` は **複数の参照画像を配列で受け取れる**。gpt-image-2 は **全入力画像を常に高フィデリティで処理** する（`input_fidelity` は指定不可）。
- Responses API のマルチターン（`previous_response_id` + `image_generation` tool）でも文脈保持は可能だが、テキストモデルのターンに載る。

## Decision

### A. 既定は1枚。複数ページはオプトイン（`--pages`）

`asb` / `asb-inbox` に `--pages {N|auto}` を追加する。フラグ無し＝従来どおり1枚（完全後方互換）、`--pages N`＝N ページ、`--pages auto`＝Educational Planner が枚数を決定。上限は **`MAX_PAGES = 6`**（暴走課金防止）。**digest は対象外**（1枚俯瞰が仕様＝ADR 0010）。

### B. 一貫性は「参照画像方式（方式A）」で担保する

各ページは観点が異なるため `n` では作れない。1枚目を `images.generate` で作り、**2ページ目以降は1枚目を参照画像として `images.edit` に渡す**。画像 API だけで完結し（テキストモデルの追加課金なし）、gpt-image-2 が参照を高フィデリティ処理するのでスタイル/配色/キャラが揃う。全ページを1枚目にアンカーすることで、累積ドリフトを避けつつ参照は毎回1枚に抑える。

Responses API マルチターン（方式B）は文脈保持がより自然だがテキスト課金と別 SDK 面を要するため、本 Issue では採らない（対話的リファインメント #29 向き）。

### C. データモデル

- `EducationalPlan.pages: list[PageSpec]` を追加（各 `PageSpec` = title / learning_objective / description / aspect_ratio）。単一ページ時は空。
- `KnowledgeObject.illustrations: list[str]`（順序付き Vault 相対パス）を追加。`outputs['illustration']` は1枚目＝後方互換として維持（参照のみ・ADR 0001 不変）。
- `ImageProvider.generate(..., reference_images: list[Path] | None = None)` を拡張。

## Consequences

- **不変条件の変更**：「1 KO = 1 イラスト」は「1 KO = 1 枚（既定）または順序付き複数ページ」になった。単一ページの挙動・課金・冪等性は不変。
- **コスト**：`--pages N` は画像 API を N 回呼ぶ＝画像課金 N 倍（＋2ページ目以降は参照画像1枚分の入力）。`n` で束ねることはできない。`--no-image` が最優先。
- **冪等性/掃除**：`--overwrite` 時、ページ数が減った場合や複数→単一に戻した場合に備え、`{stem}-pN.png` の余剰ファイルを削除してから書く。
- **グレースフルデグラデーション**：Educational Plan の生成に失敗した場合、`pages` は空となり自動的に1枚にフォールバックする（AI 依存にしない）。
- **波及**：`images.edit`（複数参照・高フィデリティ）と Responses API マルチターンの知見は、既存イラストの対話的改善（#29）にも活用できる。

## Alternatives considered

- **`n` で複数枚**：同一プロンプトのバリエーションのみで観点分割にならないため不採用。
- **方式B（Responses API マルチターン）**：文脈保持は自然だがテキストトークン課金と実装コストが増える。反復編集（#29）向きとして温存し、本 Issue では方式A。
- **固定枚数/固定パネル**：単純だが内容に合わない。Planner 主導（`--pages N` / auto）で柔軟性を確保。
- **全ページを直前ページにアンカー**：累積ドリフトと参照コスト増を招く。全ページを1枚目にアンカーする方が安定・安価。
