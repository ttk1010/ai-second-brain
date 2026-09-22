# ADR 0016: クラウド経路だけ画像モデルを gpt-image-2.5-flare にする

- Status: Accepted
- Date: 2026-09-22
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

GPT Image 2.5（`gpt-image-2.5-flare` / `gpt-image-2.5-sunburst`）が公開された。flare は「gpt-image-2 より高品質で約 50% 低レイテンシ」とされ、API（`images.generate` / `images.edit`）もサイズも互換で、`image_model` を変えるだけで切り替えられる。

クラウド経路（[ADR 0015](0015-serverless-instant-generation.md)）は iOS ショートカットの約 60 秒タイムアウトに収める必要があり、これまでは画像品質を `low` に落として対応していた。

[Issue #45](https://github.com/ttk1010/ai-second-brain/issues/89) で、同じ Knowledge Object を両モデルで画像化して比較した（`scripts/measure_generation.py`、2026-09-22）。

- **速度とコスト**：flare は品質段階がトークン上で 1 段下にずれている。flare `high` の出力トークンと費用（1 枚約 $0.044）は gpt-image-2 `medium` と同じで、生成は約 25 秒（gpt-image-2 medium は 47〜59 秒）。
- **絵柄**：既存のプロンプト（`hand-drawn, textbook-inspired`）のままだと、flare はフラットなベクター調のインフォグラフィックになり、ASB の視覚言語から外れる。手描きの特徴（ペンの線、手書き風文字、色鉛筆・水彩風の塗り、手描きの人物）を具体的に書き、フラットなベクター調を避けるよう指示すると、手描き・教科書調にほぼ戻る。既存画像を絵柄の見本として参照させる案は、上積みが小さいうえに費用が約 30% 増え、誤字も出たため採らない。
- **日本語**：どちらも正確。
- **好み**：指示を強めた flare も十分近いが、オーナーは gpt-image-2 の絵柄を好む。

## Decision

1. **ローカル経路（CLI / Inbox / Telegram / GitHub Actions）は `gpt-image-2` の `medium` を維持する。** プロンプトも変えない。
2. **クラウド経路（Lambda）だけ `gpt-image-2.5-flare` の `high` を使う。** 費用は据え置きで、生成が約 2 倍速くなり、`low` に落とす必要がなくなる。
3. flare には**手描きの特徴を具体的に書いた絵柄指示**（`IllustrationStyle.EXPLICIT_HAND_DRAWN`）を使う。視覚言語そのものは同じで、書き方だけを変える。どちらの書き方を使うかは設定 `illustration_style` で選び、既定は `standard`（従来の文言）。

## Consequences

- 外出先で生成した画像の品質が上がる（`low` → gpt-image-2 `medium` 相当）。1 枚あたりの費用は約 $0.007 → 約 $0.044 に上がるが、1 ノート全体で約 $0.06 に収まる。
- Vault 内に 2 つのモデルの画像が混ざる。絵柄は近いが同一ではない。気になる画像は手元で `asb --overwrite` すれば gpt-image-2 で描き直せる。
- 絵柄指示が 2 通りになる。どちらも `backend/prompts/illustration/educational.py` にあり、視覚言語を変えるときは両方を更新する。
- 計測スクリプトと料金スナップショット（`backend/services/cost.py`）が残るので、新しいモデルが出たときも同じ手順で比較できる。

## Alternatives considered

- **全経路を flare に切り替える**：速くて同コストだが、オーナーが gpt-image-2 の絵柄を好むため採らない。
- **gpt-image-2 のまま（クラウドは `low`）**：60 秒には収まるが、外出先の画像の品質が低い。
- **既存画像を絵柄の見本として参照させる**：絵柄の上積みが小さく、費用が約 30% 増え、誤字・英語タイトル化が出た。
- **`gpt-image-2.5-sunburst`**：編集精度重視で生成が遅く、速度が目的のクラウド経路に合わない。
