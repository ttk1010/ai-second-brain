# Issue #20: 出力ファイル名の簡潔化

Labels: enhancement, storage
Milestone: (none — output hardening)

## Why
ニュース記事から生成したノート/画像のファイル名が長すぎる。実テストでは
`06 News/Ledge.ai article notes Anthropic guidance for instructing Claude Code agents.md`
のように LLM 生成タイトルをそのままファイル名にしており、扱いづらい。

## Goal
記事内容から簡潔で安定したファイル名を生成する（ノートの可読性とVault内の取り回しを改善）。

## Tasks
- [ ] ファイル名用の短いスラッグ生成（長さ上限、語数制限、または記事の主題語からの生成）
- [ ] frontmatter の `title` は完全なまま、ファイル名のみ簡潔化
- [ ] concept / news 双方で一貫した規則。既存の衝突回避（`-2` 連番）と冪等性は維持
- [ ] 単体テスト（長いタイトル→簡潔な安定スラッグ）

## Definition of Done
- 長いタイトルでも簡潔で安定したファイル名になる
- 表示用タイトル（frontmatter / 見出し）は維持される
- 既存ノートとの衝突を安全に処理する

## Notes
- 記録のみ（実装時期は別途判断）。#19（fetcher 強化）と同じ News 出力品質の改善群。
