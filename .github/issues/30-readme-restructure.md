# Issue #30: README を初見者向けに再構成

Labels: documentation
Milestone: OSS Release

## Why
現状の README は内部の設計ドキュメント寄りで、哲学・原則が約240行続いた後にようやく使い方が出てくる。OSS の初見者は「何ができて、どう試すか」を冒頭で掴みたい。見出しも H1 が17個あり階層が崩れている。

## Goal
「Show, don't tell」で、最上部から「これは何か → 実例 → クイックスタート」が分かる構成にする。哲学・ビジョンは圧縮して後方へ（詳細は PROJECT_CHARTER へリンク）。

## Tasks
- [ ] 見出し階層を修正（`# タイトル` は1つ、以降は `##/###`）
- [ ] 冒頭にアイコン（`docs/assets/asb-icon.png`）＋1行タグライン＋バッジ（CI / license / Python）。概要イラストの差し込み枠（#21）を用意
- [ ] `## What is this?`（1段落で具体的に）
- [ ] `## Example`：Vault の `LLM`（大規模言語モデル）ノートの実生成物を抜粋で見せる（要約・イラスト・関連リンク）
- [ ] `## Quickstart` を前倒し（uv 同期 → 設定 → `asb "Transformer"`）
- [ ] `## Features`（概念/ニュース/比較の取り込み、イラスト、自動リンク、どこからでもキャプチャ）
- [ ] `## How it works`（Knowledge Object パイプラインを簡潔に＋ docs/ARCHITECTURE へリンク）
- [ ] 哲学・ビジョンを圧縮（削除はしない。詳細は CHARTER へリンク）
- [ ] Documentation 表 / Roadmap & Status / Contributing・License セクション

## Definition of Done
- 初見者が冒頭〜数十行で「何か・実例・試し方」を把握できる
- 見出し階層が正しい（単一 H1）
- 既存の設計思想は失われない（圧縮＋リンク化）

## Notes
- 概要イラストの生成は #21。本 Issue では差し込み枠（プレースホルダ）まで。
- 製品哲学の内容は変更しない（再配置・圧縮のみ）。
