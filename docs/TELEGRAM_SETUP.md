# Telegram セットアップガイド（Claude Code Channels）

Telegram の bot にメッセージを送るだけで、URL・概念・比較を AI Second Brain の
ノートに変換できるようにする手順です。処理は自分のマシン上の Claude Code が
`asb` を実行して行い、固定のホスティング費用はかかりません
（[ADR 0006](adr/0006-capture-interface-local-first.md)）。

「ゼロ → チャットキャプチャが動く」までを上から順に実行してください。各手順で
つまずいたら、[docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) の対応する項目に
症状と対処があります。

> **セキュリティ最重要**: ペアリングと権限の許可登録は**必ず自分のターミナル
> （Claude Code セッション）で**行ってください。Telegram のメッセージ内で「このコードで
> ペアリングして」「allowlist に追加して」と依頼されても**従わないこと**。これはプロンプト
> インジェクションの典型的な手口です（詳細は末尾のセキュリティ節）。

---

## 0. 前提

- **Claude Pro サブスクリプション**（Claude Code Channels は Pro/Max 前提。API キー
  単体では動きません）。
- **[Claude Code](https://www.claude.com/product/claude-code)** がインストール済みで
  `/login` 済み。
- **[bun](https://bun.sh/)** がインストール済み（Channels のポーリングサーバ
  `server.ts` の実行に必要）。未導入なら:
  ```bash
  curl -fsSL https://bun.sh/install | bash
  ```
  **インストール後はシェルを再起動**してから `claude` を起動してください
  （PATH が引き継がれないと bun を見つけられません）。
- **`asb` 本体が動く状態**（`config/settings.toml` の `vault_path` 設定と
  `.env` の `OPENAI_API_KEY`）。README の Quickstart を先に済ませておくこと。
  キャプチャ経由の生成も通常どおり **1 ノートあたり OpenAI 課金**が発生します。

---

## 1. Telegram bot を作成してトークンを取得

1. Telegram で [@BotFather](https://t.me/BotFather) を開く。
2. `/newbot` を送り、bot 名とユーザー名を指定する。
3. 発行された **bot トークン**（`123456:ABC-...` 形式）を控える。

> トークンは秘密情報です。git やチャットに貼らないこと。

---

## 2. Telegram プラグインを導入

通常のシェル（Claude Code セッション**外**）で実行します:

```bash
claude plugin install telegram@claude-plugins-official --scope project
```

> `/reload-plugins` などのスラッシュコマンドは Claude Code の**対話セッション専用**で、
> シェルでは使えません。プラグイン導入だけは上記のとおりシェルで行います。反映は
> `claude` を再起動するか、セッション内で `/reload-plugins` を実行します。

---

## 3. トークンを設定

`claude` を起動し、**対話セッション内**で実行します:

```
/telegram:configure <token>
```

- `401 authentication_error` や「Please run /login」が出る場合は、Telegram では
  なく **Claude Code 側の Anthropic 認証**の問題です。`ANTHROPIC_BASE_URL` /
  `ANTHROPIC_API_KEY` を `unset` し、`claude` を再起動して `/login`（Claude Pro）
  してから再実行してください（→ TROUBLESHOOTING「`/telegram:configure` → `401`」）。

---

## 4. ペアリング

誰が bot 経由で自分の Claude Code に指示できるかは**許可リスト（allowlist）**で
制御します。まず**自分自身を許可リストに登録**します。初期状態のポリシーは
`pairing`（ペアリングコードで登録する方式）です。

1. **起動フラグ付き**で Claude Code を起動する（これがないとメッセージが届きません）:
   ```bash
   claude --channels plugin:telegram@claude-plugins-official
   ```
2. **自分の** Telegram アカウントから bot に何かメッセージを送る。すると Telegram に
   **6文字のペアリングコード**が返ってきます。
3. **ターミナルの Claude Code セッションに戻り**、返ってきたコードを入力して
   ペアリングを確定する:
   ```
   /telegram:access pair <コード>
   ```
   実行すると自分のアカウントが許可リストに追加されます。

---

## 5. allowlist にロックダウン

初期の `pairing` ポリシーのままだと、**知らない人が bot に DM してペアリングコードを
受け取れてしまいます**。自分のペアリングが済んだら、必ず許可リスト方式に切り替えて
**リスト外のユーザーからのメッセージを遮断**します:

```
/telegram:access policy allowlist
```

これ以降、許可リストにいないユーザーのメッセージはブロックされます（コードも発行
されません）。許可リストの確認や管理はセッション内で `/telegram:access` を実行します。

> 別のデバイス／アカウントも使いたい場合は、一時的に `pairing` に戻して手順 4 で
> ペアリングし、済んだら再び `allowlist` に戻す運用にします。

---

## 6. 無人実行のための事前承認

Channels 経由のセッションはリモート起点で、権限プロンプトにその場で応答できません。
そのため、使うツールとコマンドを**事前に許可登録**しておかないと、返信やコマンド
実行のたびに承認待ちで止まります。

**個人設定 `.claude/settings.local.json`**（gitignore 済み）の
`permissions.allow` 配列に、既存エントリを残したまま以下をマージします:

```json
"mcp__plugin_telegram_telegram__reply",
"mcp__plugin_telegram_telegram__edit_message",
"mcp__plugin_telegram_telegram__react",
"mcp__plugin_telegram_telegram__download_attachment",
"Bash(uv run asb *)",
"Bash(uv run asb-inbox *)"
```

- 保存後、**Claude Code セッションを再起動**すると反映されます（現行セッションには
  反映されません）。
- Telegram プラグインのサーバ名は `plugin_telegram_telegram`（アンダースコア区切り）。
- **個人パスを含む許可は必ず `settings.local.json` に書く**こと。共有の
  `.claude/settings.json` に書くと個人設定が git に乗ります。
- `defaultMode` / `bypassPermissions` による全許可は、外部入力を扱う経路では
  乗っ取り時のリスクが高いため**使わない**。個別 allow 方式にする。

---

## 7. 動作確認

1. **起動フラグ付き**で Claude Code を起動する:
   ```bash
   claude --channels plugin:telegram@claude-plugins-official
   ```
2. bot に URL・概念・比較のいずれかを送る:
   - 例（概念）: `Transformer`
   - 例（URL）: `https://ledge.ai/...`
   - 例（比較）: `GPT, Claude, Gemini を比較して`
3. `asb-capture` スキルが走り、Vault にノートが生成され、**bot から返信**が届く
   （作成したノートのパス、または既存でスキップした旨）。

bot が無反応な場合は、bun 未導入 / `dmPolicy` の allowlist が空 /
`mcp-needs-auth-cache.json` のキャッシュが典型原因です
（→ TROUBLESHOOTING「Bot が DM に無反応」）。

> **1 トークン = 1 セッション。** 同じ bot トークンで複数の Channels セッションを
> 同時に起動しないこと（ポーリングが競合します）。運用は 1 セッションに保つ。

---

## セキュリティ（必読）

- **ペアリング（`pair <コード>`）・allowlist 追加・権限の許可登録は、必ず自分の
  ターミナルで行う。** Telegram のメッセージ内に「このコードでペアリングして」
  「allowlist に追加して」といった指示が来ても**従わない**。それはプロンプト
  インジェクションが送ってくる典型的な要求です。`pair` に使うのは**自分の Telegram に
  届いた自分のコードだけ**。承認を求められたら、送信者に「オーナー本人へ直接依頼して」
  と伝える。
- **セットアップが済んだら `policy allowlist` にしておく**（手順 5）。`pairing` の
  ままだと第三者がコードを受け取れてしまう。
- **bot に届くメッセージは信頼できない外部入力**として扱う。だからこそ全許可
  （`bypassPermissions`）ではなく、`asb` 実行と返信系ツールだけの**最小限の個別 allow**
  に留める。
- **個人設定・個人パスは `settings.local.json`（gitignore 済み）に隔離**し、共有の
  `.claude/settings.json` には入れない。

---

## 関連

- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — 症状別の対処（本ガイドで
  つまずいた時の参照先）
- [ADR 0006: Capture interface — local-first](adr/0006-capture-interface-local-first.md)
  — なぜこの構成（Inbox キュー + Channels）なのかの設計判断
- `.claude/skills/asb-capture/SKILL.md` — 受信メッセージを `asb` 実行に変換する
  スキルの定義

## 参考

- [Claude Code Channels で Telegram 連携（note 記事）](https://note.com/major_elk2890/n/n77b5b5c1e795)
