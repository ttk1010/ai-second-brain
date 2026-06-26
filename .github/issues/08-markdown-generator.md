# Issue #8: Markdown Generator（標準テンプレート）

Labels: core, output, markdown
Milestone: Phase 1 — Foundation

## Why
Markdown は長期知識の主形式であり、AIツールなしでも価値を保つ必要がある。

## Goal
Knowledge Object から標準テンプレートに沿った Markdown ノートを生成する。

## Tasks
- [ ] `backend/markdown/` に Generator を実装
- [ ] 標準テンプレート（Frontmatter / Summary / Illustration / Background / Key Takeaways / Related Notes / References / Tags）を出力
- [ ] テンプレートはコードに埋め込まず分離（PROMPT_STYLE_GUIDE / Markdown Rules 準拠）
- [ ] 入力は Knowledge Object のみ（プレゼン情報をモデルへ逆流させない）
- [ ] 決定的な出力を検証するスナップショットテスト

## Definition of Done
- Knowledge Object のみから標準テンプレートの Markdown を生成できる
- AIツールなしで読める人間可読なノートになる
- スナップショットテスト通過
