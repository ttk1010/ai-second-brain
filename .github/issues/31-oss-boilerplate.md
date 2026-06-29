# Issue #31: OSS ボイラープレート（LICENSE / CONTRIBUTING / メタデータ）

Labels: documentation, chore
Milestone: OSS Release

## Why
公開前に OSS の必須要素が揃っていない。LICENSE が無く（公開のブロッカー）、`pyproject.toml` にライセンス・URL・classifiers などの配布メタデータも無い。貢献手順も未整備。

## Goal
MIT ライセンスで公開できる状態にし、配布メタデータと貢献ガイドを整える。

## Tasks
- [ ] `LICENSE`（MIT、著作権者 ttk1010、年 2026）を追加
- [ ] `pyproject.toml` に license / project URLs（Homepage, Repository）/ authors / classifiers を追加
- [ ] `CONTRIBUTING.md`（開発手順、テスト/lint、Issue 駆動・小さなPR、コミット規約の要点）
- [ ] README にライセンス記載とバッジ（CI / license / Python）
- [ ] （任意）CODE_OF_CONDUCT は必要に応じて

## Definition of Done
- リポジトリに MIT LICENSE があり、README からも参照される
- `pyproject` に配布メタデータが入る
- 貢献手順が文書化される

## Notes
- README へのライセンス記載・バッジは #30 の再構成と整合させる。
