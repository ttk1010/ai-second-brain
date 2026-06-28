# Issue #24: 冪等な生成（既存ノートはスキップして再課金を防ぐ）

Labels: enhancement, services, cost

## Why
現状、同じ入力で `asb` を再実行すると、`--overwrite` なしでは番号付きの重複ノート（`Transformer-2.md` 等）が作られ、かつ LLM・画像生成に**再課金**される。日常運用でキャプチャ頻度が上がると、無駄なコストと重複の温床になる（コスト議論・ADR 0005 のコスト最小方針に反する）。

## Goal
同じソース（概念名 / 記事URL）のノートが既に存在する場合は、**API を一切呼ばずにスキップ**する。明示的に再生成したいときだけ `--overwrite` で置き換える。

## Tasks
- [ ] 既存ノート検出：frontmatter の `source`（概念名 or URL）が一致するノートを Vault から探すヘルパーを storage 層に追加
- [ ] パイプラインで**抽出の前**に検出し、存在すれば status=`exists` で早期 return（API 呼び出しゼロ）
- [ ] `--overwrite` 指定時は従来どおり再生成して置き換える
- [ ] CLI は「既存のためスキップ（再生成は --overwrite）」を明示出力
- [ ] 単体テスト（既存検出でスキップ・API未呼出、--overwrite で再生成、別ソースは衝突しない）

## Definition of Done
- 同一ソースの再実行で API を呼ばず、重複ノートも作られない
- `--overwrite` で意図的な再生成ができる
- 外部API非依存でテストが通る

## Notes
- 検出キーは frontmatter `source`（concept は概念名、news は URL）。ファイル名（short_title 由来）には依存しない。
