# Troubleshooting

Operational notes for setting up and running AI Second Brain — symptoms we hit
and how they were resolved. This complements the setup steps in `README.md` and
the design rationale in `docs/adr/`.

> Each entry follows the template below. Keep entries short and concrete.

## Entry template (copy for new issues)

### <short symptom title>

- **Symptom:** what you saw (exact error if possible)
- **Cause:** why it happened
- **Fix:** the steps that resolved it
- **Notes:** caveats, related links, how to avoid it next time

---

## Claude Code Channels (Telegram)

### `/reload-plugins` → `zsh: no such file or directory`

- **Symptom:** ターミナル（zsh）で `/reload-plugins` を打つと `zsh: no such file or directory` になる
- **Cause:** `/reload-plugins` は Claude Code の **対話セッション内** のスラッシュコマンドであり、シェルコマンドではない
- **Fix:** `claude` を起動した状態で `/reload-plugins` と入力する。または `claude` を再起動するだけで自動反映される。プラグインのインストール自体は通常のシェルで `claude plugin install telegram@claude-plugins-official --scope project` と実行する
- **Notes:** スラッシュコマンド（`/reload-plugins`、`/telegram:access` など）はすべて Claude Code 対話セッション専用。シェルプロンプトでは使えない

### `/telegram:configure` → `401 authentication_error` / "Please run /login"

- **Symptom:** `/telegram:configure <token>` を実行すると `401 authentication_error` または「Please run /login」が表示される
- **Cause:** Telegram API の認証エラーではなく、Claude Code セッション自体の Anthropic 認証が無効になっている。環境変数 `ANTHROPIC_BASE_URL` が標準外エンドポイントを指していると Pro サブスクのログイン認証が通らない
- **Fix:**
  ```
  unset ANTHROPIC_BASE_URL
  unset ANTHROPIC_API_KEY   # 必要な場合のみ
  ```
  その後 `claude` を起動し直し → `/login` で Claude Pro にサインイン → `/telegram:configure <token>` を再実行
- **Notes:** Claude Code Channels は **Pro サブスクリプション前提**（API キー単体では不可）。`~/.zshrc` や `~/.zshenv` に `ANTHROPIC_BASE_URL` の永続設定がある場合はそちらも確認・削除する

### Bot が DM に無反応（Telegram チャンネル設定直後）

- **Symptom:** Bot にメッセージを送っても返信がない。`~/.claude/channels/telegram/access.json` の `pending` も増えない（ポーリング自体が動いていない）
- **Cause:** 以下の複合要因：
  1. **bun 未インストール** → `server.ts` が起動できずポーリング不能
  2. **`dmPolicy: allowlist` かつ `allowFrom` が空** → 全 DM が silently drop される
  3. **`~/.claude/mcp-needs-auth-cache.json` にキャッシュ** → 過去の起動失敗が記録され、Claude がサーバー起動を再試行しない
- **Fix:**
  ```bash
  # 1. bun をインストール（要シェル再起動）
  curl -fsSL https://bun.sh/install | bash

  # 2. dmPolicy を pairing に変更（Claude Code 内で）
  /telegram:access policy pairing

  # 3. キャッシュ削除 → channels プロセス再起動
  rm ~/.claude/mcp-needs-auth-cache.json
  kill $(pgrep -f "channels plugin:telegram")
  ```
  その後 Claude Code を再起動すると `bun server.ts` が起動し `telegram channel: polling as @<botname>` がログに出る
- **Notes:** bun インストール後はシェルを再起動してから Claude Code を起動すること（PATH が引き継がれないと channels プロセスが bun を見つけられない）。動作確認は `ps aux | grep "bun"` でプロセスの存在を確認する

### (add more Channels entries here)

---

## Generation / CLI / environment

### `uv run asb` (or `asb-link` / `asb-inbox`) → `ModuleNotFoundError: No module named 'backend'`

- **Symptom:** `uv run asb` 実行時に `ModuleNotFoundError: No module named 'backend'` が出て終了する
- **Cause:** パス移行・venv 再構築・Python バージョン変更などの後、editable インストールが古くなりパッケージが認識されなくなる
- **Fix:**
  ```bash
  uv sync --reinstall-package ai-second-brain
  ```
  または代替として：
  ```bash
  uv run python -m backend.cli "<入力>"
  ```
- **Notes:** プロジェクト構成を変更した後（ディレクトリ移動、Python バージョン変更など）は editable インストールが無効になることがある。`uv sync` だけでは不十分な場合は `--reinstall-package` オプションを付ける

### (add more CLI/environment entries here)
