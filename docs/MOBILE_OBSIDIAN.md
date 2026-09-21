# モバイル閲覧セットアップ（Obsidian iOS × iCloud）

生成したノートを iPhone / iPad の Obsidian アプリから読むための手順です。

## なぜ Vault が iOS から見えないのか

Vault が iCloud Drive の中にあっても、**iOS 版 Obsidian は
`iCloud Drive/Obsidian/` フォルダ（アプリ専用コンテナ
`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/`）の中しか読めません**。

macOS の「デスクトップと書類」同期を使って `~/Documents/...` に Vault を置いていると、
iCloud には入っているのにアプリの Vault 一覧には現れません。解決策は、Vault を
Obsidian のコンテナフォルダへ移動することです。

## 移動しても git が壊れない理由

ASB の推奨構成では、Vault の `.git` は実体ではなく
`gitdir: <パス>` と書かれたポインタファイルで、git データベース本体は Vault の外
（例: `~/asb-vault.git`）にあります（[DEPLOY_SERVERLESS.md](DEPLOY_SERVERLESS.md) の
`git init --separate-git-dir`）。

- ポインタは Vault と一緒に移動し、参照先は絶対パスなので変わらない
- `core.worktree` が未設定なら、git は「`.git` ファイルが置かれている場所」を
  作業ツリーとみなす

このため **Vault フォルダを移動しても git の設定変更は不要**です。あわせて、
iCloud が同期するのは作業ファイルだけで `.git` の中身は同期対象外になるため、
「git リポジトリを iCloud に置くと壊れる」という典型的な事故も避けられます。

確認コマンド:

```bash
cat "<Vault>/.git"                                   # gitdir: ... と出れば該当構成
git -C "<Vault>" config --get core.worktree          # 何も出なければ移動して安全
```

## 手順（Mac 側）

### 1. 事前チェック

移動前に、Vault がクリーンでリモートに push 済みであることを確認します（万一失敗
しても GitHub から復旧できる状態にしておく）。

```bash
git -C "<Vault>" status --porcelain                  # 空であること
git -C "<Vault>" rev-list --left-right --count HEAD...origin/main   # 0  0
```

iCloud の「ストレージを最適化」でファイルが退避されていないことも確認します。

```bash
find "<Vault>" -name "*.icloud" | wc -l              # 0 であること
```

### 2. Obsidian デスクトップを終了する

開いたまま移動すると、アプリが旧パスに設定を書き戻すことがあります。

```bash
osascript -e 'quit app "Obsidian"'
```

### 3. Vault を移動する

```bash
mv "<Vault>" ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/"<Vault名>"
```

### 4. `vault_path` を更新する

`config/settings.toml` の `vault_path` を新しいパスに書き換えます。ASB 側で変更が
必要なのはここだけです（Lambda / GitHub Actions 経路は git リモート経由なので影響
ありません）。

### 5. 動作確認

```bash
git -C "<新パス>" status -sb        # クリーン・追跡ブランチが生きている
uv run asb "LLM"                    # 既存ノートをスキップすれば設定OK（課金なし）
uv run asb-link index | head        # Vault を読めている
```

Obsidian デスクトップの Vault 一覧も旧パスのままなので、アプリを開いて新しい場所の
Vault を開き直します（`~/Library/Application Support/obsidian/obsidian.json` の
`vaults` のパスを直接書き換えても同じです。編集前にバックアップを取ること）。

## 手順（iPhone / iPad 側）

1. Obsidian アプリを開く
2. Vault 一覧に Vault 名が表示されるので、タップして開く

表示されない場合:

- **iCloud のアップロード待ち** — Vault に画像が多いと初回同期に時間がかかります。
  Mac 側でファイルが揃っていれば、待てば現れます。
- **Obsidian の iCloud が OFF** — iOS の「設定 → Apple ID → iCloud」で確認します。

## 注意: モバイルでの編集は自動コミットされない

`auto_commit` は ASB が**生成した**ファイルだけをコミットします。モバイルで既存
ノートを手で編集した場合、その変更は iCloud 経由で Mac の作業ツリーには届きますが、
git にはコミットされません。

閲覧と生成が中心なら問題ありませんが、モバイル編集を履歴に残したい場合は、Mac 側で
定期的に次を実行します。

```bash
git -C "<Vault>" add -A && git -C "<Vault>" commit -m "Sync mobile edits" && git -C "<Vault>" push
```

## 代替案

| 方式 | 利点 | 欠点 |
|---|---|---|
| iCloud（本ガイド） | 無料・プラグイン不要・iOS が標準対応 | iOS では Obsidian コンテナ配下に置く必要がある |
| Obsidian Git プラグイン | 「git が唯一の真実」という構成と最も整合 | iOS 版は大きめのリポジトリ（画像バイナリ多数）で不安定・低速。スマホに PAT の保存が必要 |
| Obsidian Sync（有料） | 最も確実・競合処理が専用設計 | 月額費用、同期経路が 1 つ増える |
