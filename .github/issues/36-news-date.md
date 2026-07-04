# Issue #36: ニュースノートに記事の公開日を入れる

Labels: enhancement, parser, markdown

## Why
入力がニュースの場合、いつの記事かが分かるように**記事の公開日**を生成ノートに入れたい。News は「いつの出来事か」が知識の価値に直結する。

## 決定事項
- **どの日付**：記事の**公開日**（生成日 `created` とは別に）
- **どこに入れる**：frontmatter ＋ **本文にも**（見出し直下に表示）
- **フォールバック**：公開日が取れない時は**無記載**（`created` で代替しない）
- **ファイル名**：**付けない**（命名規則 #20 を維持）
- **拡張性**：日付は `Metadata.published_date`（型非依存の既存フィールド）に持たせ、描画も汎用にする。将来 News 以外が公開日を持つ場合にもそのまま出る余地を残す（抽出だけ News 固有）

## Tasks
- [ ] News 抽出プロンプトに公開日（ISO `YYYY-MM-DD`、不明なら空）を追加、`NewsExtraction.published_date` に格納
- [ ] `builder.from_news` で文字列を `date` に解釈し `Metadata.published_date` に反映（不正/空は None）
- [ ] Markdown Generator：`published_date` があれば frontmatter に描画し、見出し直下に日付行を表示（汎用実装＝source_type 非依存）
- [ ] 単体テスト（公開日あり/なし、frontmatter＋本文描画、不正日付→無記載、News 以外は無変化）

## Definition of Done
- News ノートに公開日が frontmatter と本文に入る
- 公開日が取れない/不正な場合は無記載で破綻しない
- 概念/比較など既存挙動は変わらない（回帰なし）
- テストが外部API非依存で通る

## Notes
- `Metadata.published_date: date | None` は既存（未使用）。これを活用。
- イラスト画像への文字焼き込みは対象外（gpt-image-2 の文字描画が不安定なため）。
