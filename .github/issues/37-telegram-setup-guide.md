# Issue #37: Telegram 連携のセットアップ手順を1か所にまとめる

Labels: documentation

## Why
Telegram（Claude Code Channels）経由のチャットキャプチャは動作しているが、**ゼロから設定する手順が1か所にまとまっていない**。現状は次のように分散している:

- `README.md` … 外部 [Claude Code Channels](https://code.claude.com/docs/en/channels) へのリンクと「setup は TROUBLESHOOTING.md を見よ」という誘導のみ
- `docs/TROUBLESHOOTING.md` … 「Claude Code Channels (Telegram)」節はあるが**症状→原因→対処**の形式で、プラグイン導入・トークン設定・アクセス方針・事前承認といった手順が対処記事の中に断片的に埋もれている
- `docs/adr/0006-capture-interface-local-first.md` / `asb-capture` スキル … 設計判断・スキル説明であって手順ではない

新規に環境構築する人（＝将来の自分/仲間）が、順を追って設定を完了できる導線が欠けている。

## Goal
**「ゼロ → チャットキャプチャが動く」までを順番どおりに追える単一のセットアップガイド**を用意する（例: `docs/TELEGRAM_SETUP.md`）。README から明示的にリンクし、`TROUBLESHOOTING.md` は個別トラブル対処に専念させて相互参照でつなぐ。既存の記述と重複させず、手順は新ガイドへ、問題対処は TROUBLESHOOTING へ、という役割分担にする。

## カバーする手順（既存の TROUBLESHOOTING / ADR 0006 から抽出・整理）
1. **前提**: Claude Pro サブスクリプション（API キー単体では不可）、`bun` インストール済み、`OPENAI_API_KEY`（生成に必要）
2. **Bot 作成**: Telegram の @BotFather で bot を作成しトークンを取得
3. **プラグイン導入**: `claude plugin install telegram@claude-plugins-official --scope project`
4. **設定**: Claude Code 対話セッションで `/telegram:configure <token>`
5. **アクセス方針とペアリング**: `/telegram:access`（ポリシー設定・ペアリング承認）
6. **無人実行のための事前承認**: `settings.local.json`（共有の `settings.json` ではない）に Telegram プラグインの MCP ツールと `asb` 実行を許可登録
7. **動作確認**: bot に URL / 概念を送ると `asb-capture` が走りノートが生成され、返信が届く
8. **セキュリティ注意**（強調）: ペアリング承認・許可登録は**必ずターミナル側で**行う。チャンネル（Telegram メッセージ）からの「承認して」「allowlist に追加して」は**プロンプトインジェクションの典型**なので従わない。個人パスを含む許可は `settings.local.json` に置き git に乗せない

## Tasks
- [ ] `docs/TELEGRAM_SETUP.md`（新規）に上記 1〜8 を順序立てて記述
- [ ] README の「Chat capture (Telegram)」を新ガイドへのリンクに更新（現在の「TROUBLESHOOTING.md for setup」誘導を差し替え）
- [ ] `docs/TROUBLESHOOTING.md` は対処記事に専念させ、冒頭からセットアップガイドへ相互リンク
- [ ] セキュリティ注意（インジェクション防御・`settings.local.json` 分離）をガイド内で明示
- [ ] 実際の手順どおりに追試して齟齬がないか確認（コマンド名・スラッシュコマンド・MCP ツール識別子）

## Definition of Done
- 新規ユーザーがガイドだけを順に実行してチャットキャプチャを動かせる（トラブル記事を読まなくても完了できる）
- README からガイドへ1クリックで辿れる
- セキュリティ注意（ペアリング/allowlist をチャンネル発言で承認しない、個人設定は local に分離）が明記されている
- 手順とトラブル対処の役割が分離され、相互参照されている

## Notes
- 素材はすでに `docs/TROUBLESHOOTING.md`（プラグイン導入 / `401` 認証 / DM 無反応 / 自動承認）と ADR 0006 に存在する。**新規作成というより抽出・再構成**が主。
- ドキュメントのみの変更（アプリケーションコードに触れない）ため、ブランチを切らず main へ直接コミットする運用でよい（CLAUDE.md の Git 方針）。
