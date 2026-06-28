# Issue #26: Inbox ワーカー（00 Inbox キューの処理）

Labels: core, services, automation
Milestone: Phase 4 — Automation

## Why
モバイル/PC からの日常キャプチャをローカル・固定費ゼロで実現する土台（ADR 0006）。Vault の `00 Inbox/` に「URL か概念のスタブ」を置いておけば、PC 起動時にワーカーがまとめて処理して正式なノートにする。入力場所（Obsidian モバイル等）と処理場所（キー・Vault のあるマシン）をキューで分離する。

## Goal
`00 Inbox/` 内のスタブを既存パイプラインで処理し、完成ノート化したらスタブを消費（削除）するワーカーと CLI を用意する。冪等（#24）なので再実行は安全。

## Tasks
- [ ] パイプライン構築を共通化：`asb` と `asb-inbox` が同じ生成パイプラインを使えるよう factory（`build_pipeline(settings, *, no_image=False)`）に抽出
- [ ] `backend/inbox/`：`InboxWorker(pipeline, inbox_dir)`。各 `*.md` スタブから入力（本文の最初の非空行、先頭の `#`/`-`/`*` を除去。空なら filename stem）を取り出して `pipeline.run()`
- [ ] 成功（created / exists）でスタブ削除、失敗時は残してログ（無音失敗禁止）
- [ ] `asb-inbox` console script：設定読込→パイプライン構築→`00 Inbox` を処理→件数サマリ出力。`--no-image` も受け付ける
- [ ] 単体テスト（一時 Vault＋スタブ：入力抽出、成功で消費、失敗で残置、件数サマリ）。パイプラインはフェイクを注入し外部API非依存

## Definition of Done
- `00 Inbox/` のスタブが処理され正式ノートになり、成功したスタブは消える
- 失敗スタブは残り、再実行で再試行できる（冪等）
- 外部API非依存でテストが通る

## Notes
- スタブは「キューの要素」。消費＝削除（実ノートは 01 Concepts / 06 News 側に生成される）。
- 監視（watcher）常駐は導入せず、`asb-inbox` を手動 or cron/launchd で定期実行する運用（重い依存を避ける）。
