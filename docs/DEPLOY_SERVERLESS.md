# サーバーレス即時生成のデプロイ手順（Phase 1）

外出先の iPhone から、家の Mac 抜きでイラストを即時生成する構成（[ADR 0015](adr/0015-serverless-instant-generation.md)、[構成図](architecture-diagrams.md) の図2）のセットアップ手順。

- 生成は既存 `backend/` パイプライン（OpenAI 直叩き）を **Lambda** で実行し、画像を即返信する。
- ノート＋画像は **GitHub リポジトリ（Vault）** にコミットされ、Mac が `git pull` で取り込み、iCloud で iPhone に届く。
- 認証は **共有シークレット**（`Authorization: Bearer`）。

> AWS の操作・シークレット登録・デプロイは各自の手元で行う。以下はそのための手順。

## 0. 前提ツール
- AWS アカウントと AWS CLI（`aws configure` 済み）
- **AWS SAM CLI**、**Docker**（コンテナイメージのビルドに使用）

## 1. GitHub 側：Vault リポジトリと PAT
1. **private リポジトリ**を作成（これが Vault の実体、または生成物の保存先）。既存 Vault を使うなら、その内容を最初に push しておく。
2. **fine-grained Personal Access Token** を発行：対象をそのリポジトリに限定し、権限 **Contents: Read and write**。

## 2. Secrets Manager：設定を1つの秘密に
```bash
aws secretsmanager create-secret --name asb/config --secret-string '{
  "OPENAI_API_KEY": "sk-...",
  "GITHUB_TOKEN": "github_pat_...",
  "GITHUB_REPO": "<owner>/<repo>",
  "ASB_AUTH_SECRET": "<長いランダム文字列>"
}'
```
`ASB_AUTH_SECRET` は自分で決める合言葉（例：`openssl rand -hex 32`）。後で iPhone 側にも設定する。

## 3. デプロイ
```bash
sam build -t infra/template.yaml
sam deploy --guided        # 初回のみ対話。ECR リポジトリは SAM が自動作成
```
- `SecretName` パラメータの既定は `asb/config`。
- デプロイ主体（あなたの IAM）に Secrets Manager 読み取り権限が必要（環境変数へ差し込むため）。Lambda 自体は秘密を環境変数で受け取る。
- 出力の **`FunctionUrl`** が生成エンドポイント。

## 4. 動作確認（curl）
```bash
curl -X POST "<FunctionUrl>" \
  -H "Authorization: Bearer <ASB_AUTH_SECRET>" \
  -H "Content-Type: application/json" \
  -d '{"input":"Transformer"}' --output out.png
open out.png
```
`{"input": "...", "guidance": "...", "pages": 3}` を受け付ける（`pages` は最大 3）。画像は応答で即返り、ノート＋画像は Vault リポジトリにコミットされる。

## 5. iPhone：iOS ショートカット（一発生成）
「ショートカット」アプリで新規作成：
1. **テキストを尋ねる**（プロンプト例「何を生成する?」）
2. **URL の内容を取得**：
   - URL＝`FunctionUrl`、方法＝**POST**
   - ヘッダ：`Authorization` = `Bearer <ASB_AUTH_SECRET>`、`Content-Type` = `application/json`
   - 本文＝**JSON**：`input` = 手順1の入力
3. **クイックルック**（画像を表示）／必要なら「写真に保存」
- 共有シート起動にすると、選択テキストからそのまま生成できる。
- 合言葉（Bearer）がショートカット内に保存される点に注意（個人利用前提）。

## 6. Mac：Vault を Git 化（`.git` は iCloud の外に置く）
Vault は `~/Documents` 配下＝iCloud 同期対象。**`.git` をそのまま置くと iCloud が同期して壊す**ので、Git 内部データを iCloud 外に分離する。
```bash
cd "~/Documents/ai-catchup/Vault"
git init --separate-git-dir "$HOME/asb-vault.git"   # .git 本体は iCloud 外へ
git remote add origin https://github.com/<owner>/<repo>.git
git add -A && git commit -m "Initial vault" && git branch -M main && git push -u origin main
```
以後、クラウドが同じリポジトリにコミットする。Mac は差分を取り込むだけ：
```bash
git -C "~/Documents/ai-catchup/Vault" pull --ff-only
```
### 起動時に自動 pull（launchd）
`~/Library/LaunchAgents/com.asb.vaultpull.plist` を作成（例）:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.asb.vaultpull</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/git</string>
    <string>-C</string>
    <string>/Users/<you>/Documents/ai-catchup/Vault</string>
    <string>pull</string>
    <string>--ff-only</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>1800</integer>
</dict></plist>
```
```bash
launchctl load ~/Library/LaunchAgents/com.asb.vaultpull.plist
```
これで Mac 起動時＋30 分ごとに、外出先で作った生成物が Vault に取り込まれ、iCloud で iPhone のファイルアプリからも見られる。

## 7. コスト対策
- 1 リクエストのイラストは最大 3 枚（ハンドラで固定）。
- AWS の **課金アラーム**（CloudWatch Billing / Budgets）を設定しておく。
- Lambda は未使用時ゼロスケール。個人利用ではインフラ費はほぼ無料枠内、OpenAI の従量課金のみ。

## 秘密のローテーション
Secrets Manager の値を更新 → `sam deploy` で再反映。GitHub PAT / `ASB_AUTH_SECRET` を変えたら iPhone ショートカットの Bearer も更新する。

## スコープ外（後続フェーズ）
会話しながらの生成（MCP コネクタ）、Telegram 連携、既存ノートのイラスト改善（#29）のリモート化、認証強化（IAM/OAuth）。
