# Issue #6: Input Classifier の実装

Labels: core, parser
Milestone: Phase 1 — Foundation

## Why
入力（AI概念 / URL）によって処理経路が分岐する。パイプラインの最初の分岐点。

## Goal
入力種別を判定する軽量な Input Classifier を実装する。

## Tasks
- [ ] `backend/parser/` に Classifier を実装
- [ ] URL か キーワード（概念）かを判定するロジック
- [ ] 第一版スコープ（#1準拠）：Concept / News(URL) を判定。Paper/Documentation は当面 News 経路で暫定処理、判別不能は `Unknown`
- [ ] `Unknown` 時のフォールバック挙動を定義
- [ ] 代表入力・エッジケースの単体テスト

## Definition of Done
- 代表的な概念・URL入力を正しく分類できる
- エッジケース（空文字、不正URL等）のテストが通過
