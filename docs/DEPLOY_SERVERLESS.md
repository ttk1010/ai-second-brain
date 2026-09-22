# サーバーレス即時生成 セットアップ手順（Phase 1）

外出先の iPhone から、家の Mac 抜きでイラストを即時生成する構成（[ADR 0015](adr/0015-serverless-instant-generation.md)、構成図は [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) の図2）を、**ゼロから完走する**ための手順。実際に構築したときにハマった箇所を「⚠️ つまずき」として各所に記載する。

**全体像**：iPhone（iOS ショートカット）→ Lambda Function URL → 既存 `backend/` パイプラインを実行 → 画像を即返信＋ノート/画像を GitHub（`asb-vault`）にコミット → Mac が `git pull` で取り込み、iCloud で iPhone のファイルアプリからも閲覧。生成は OpenAI 直叩き。クラウド経路の画像は速度を優先して `gpt-image-2.5-flare`（`high`）を使う（ローカルは `gpt-image-2`、[ADR 0016](adr/0016-cloud-image-model.md)）。

> **前提**：AWS の操作・シークレット登録・デプロイは各自の手元で行う。macOS（Apple Silicon / arm64）を想定。所要 1〜2 時間。

---

## 0. ツールの導入（Homebrew）

| ツール | 用途 | インストール |
| --- | --- | --- |
| Docker Desktop | Lambda コンテナのビルド | `brew install --cask docker` |
| AWS CLI v2 | AWS 操作 | `brew install awscli` |
| AWS SAM CLI | デプロイ | `brew install aws-sam-cli` |

導入後の確認（Docker はアプリを起動し、クジラアイコンが安定してから）:
```bash
aws --version && sam --version && docker --version && docker ps
```

> ⚠️ **つまずき①：Docker Desktop の sudo パスワード**
> `brew install --cask docker` は `/usr/local/bin` 作成のため sudo を求める。パスワードは **Mac のログインパスワード**で、入力しても画面には何も表示されない（正常）。3 回間違えると中断するので落ち着いて入力。先に `sudo mkdir -p /usr/local/bin` を済ませておくと 1 回で通る。
> sudo を避けたい場合は Docker Desktop の代わりに **Colima**（`brew install colima docker && colima start`）でも可。

> ⚠️ **つまずき②：Docker 起動時の Rosetta エラー**
> 「Rosetta installation failed」が出ても **「Continue without Rosetta」で問題ない**。今回は Lambda を arm64（Apple Silicon ネイティブ）でビルドするため、x86 エミュレーション（Rosetta）は不要。

---

## 1. AWS アカウントの初期設定

ルートアカウントしか無い状態からの手順。

1. **ルートを保護**：コンソール右上 → 「セキュリティ認証情報」→ ルートに **MFA を有効化**。以後ルートは使わない。
2. **管理者 IAM ユーザーを作成**：IAM → ユーザー → 作成（例 `yuta-admin`）→ ポリシー **`AdministratorAccess`** をアタッチ（個人学習用。慣れたら最小権限へ）。
3. **アクセスキーを作成**：`yuta-admin` → 「セキュリティ認証情報」→ アクセスキー → ユースケース **CLI**。
   - Access Key ID（`AKIA…`）と Secret access key を控える（**Secret はこの画面でしか表示されない**）。
4. **ローカルに設定**（キーは自分で入力。他人・私には貼らない）:
```bash
aws configure
```
   - region＝**`ap-northeast-1`**（東京）、output＝`json`
5. **確認**：
```bash
aws sts get-caller-identity
```
   `yuta-admin` の ARN が返れば OK。

> ⚠️ **つまずき③：アクセスキー作成時の「代替案が推奨」警告**
> AWS は長期キーを一般に推奨しない旨を表示するが、**個人利用・自分の Mac 1 台なら「そのまま作成」で問題ない**。ローカル Docker ビルドが必要なので CLI 認証情報が要る。使い終わったらキーを無効化/削除、ルート MFA は有効に。
>
> ⚠️ **つまずき④：ダウンロードした CSV の扱い**
> `aws configure` に貼ったら CSV は不要。残すなら**パスワードマネージャ**へ。`~/Documents`（iCloud 同期）や `~/Downloads` に平文放置しない。紛失してもキーは再発行できる。

---

## 2. GitHub：`asb-vault` リポジトリと PAT

1. **private リポジトリ `asb-vault` を作成**（Vault の実体。空でよい）。
2. **fine-grained PAT** を発行：Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate。
   - Repository access：**Only select repositories → `asb-vault`**
   - Permissions → Repository → **Contents: Read and write**（Metadata: Read は自動）
   - 生成された `github_pat_...` を控える（一度だけ表示）。

---

## 3. ★重要：Vault リポジトリを「最初に」初期化する

**エンドポイントを叩く前に `asb-vault` に初期コミット（`main` ブランチ）を作っておくこと。** クラウド側は保存時に `main` ブランチの先頭を参照するため、**空リポジトリのままだと保存が 404 で失敗**する。

Vault は `~/Documents` 配下＝iCloud 同期対象なので、**`.git` 本体を iCloud の外に置く**（`--separate-git-dir`）。これで iCloud が git 内部データを壊さない。

```bash
git -C "/Users/<you>/Documents/ai-catchup/Vault" init --separate-git-dir "$HOME/asb-vault.git" -b main
git -C "/Users/<you>/Documents/ai-catchup/Vault" remote add origin git@github.com:<owner>/asb-vault.git
git -C "/Users/<you>/Documents/ai-catchup/Vault" add -A
git -C "/Users/<you>/Documents/ai-catchup/Vault" commit -m "Initial vault"
git -C "/Users/<you>/Documents/ai-catchup/Vault" push -u origin main
```
- リモートは SSH（`git@github.com:...`）が楽（既存の SSH 鍵で認証）。HTTPS でも可（PAT が要る）。
- Vault フォルダには小さな `.git` **ファイル**（ポインタ）だけが残り、実体は `~/asb-vault.git`。
- 画像込みでも数十 MB 程度。private repo なので問題ない。
- **モバイルの Obsidian からも読みたい場合**は、Vault を最初から
  `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/<Vault名>` に置くとよい
  （iOS 版 Obsidian はこのフォルダしか読めない）。あとから移動することもできる
  — 手順は [MOBILE_OBSIDIAN.md](MOBILE_OBSIDIAN.md)。

> ⚠️ **つまずき⑤：`cd "~/..."` は展開されない**
> ダブルクォートで囲むと `~` がホームに展開されず `cd` が失敗し、**別ディレクトリでコマンドが走って事故る**。`~` はクォートしない、または上のように**絶対パス（`/Users/<you>/...`）**で書く。
>
> ⚠️ **つまずき⑥：`.git` を iCloud に置くと壊れる**
> `--separate-git-dir` を使わずに Vault 直下に `.git` を作ると、iCloud が多数の git 内部ファイルを部分同期してリポジトリを破損させることがある。必ず `--separate-git-dir` で iCloud 外へ。

---

## 4. Secrets Manager：`asb/config`

**リージョンは `ap-northeast-1`**。4 つの値を 1 つのシークレットに入れる。

| キー | 値 |
| --- | --- |
| `OPENAI_API_KEY` | `sk-...`（ローカル `.env` と同じで可） |
| `GITHUB_TOKEN` | `github_pat_...` |
| `GITHUB_REPO` | `<owner>/asb-vault` |
| `ASB_AUTH_SECRET` | 合言葉。`openssl rand -hex 32` で生成 |

**方法A（コンソール・履歴に残らない/おすすめ）**：Secrets Manager → 新しいシークレット → 「その他のシークレット」→ キー/値で 4 つ入力 → 名前 `asb/config`。

**方法B（CLI・一時ファイル経由）**：
```bash
cd "$(mktemp -d)" && printf '%s' '{"OPENAI_API_KEY":"sk-...","GITHUB_TOKEN":"github_pat_...","GITHUB_REPO":"<owner>/asb-vault","ASB_AUTH_SECRET":"<64文字>"}' > s.json
aws secretsmanager create-secret --name asb/config --secret-string file://s.json && rm -f s.json
```
> `--secret-string` に値を直書きするとシェル履歴に残るので、ファイル経由が安全。

---

## 5. デプロイ

Docker Desktop を起動した状態で:
```bash
sam build -t infra/template.yaml
sam deploy --guided
```

`--guided` の推奨回答：

| 質問 | 回答 |
| --- | --- |
| Stack Name | `asb-serverless` |
| AWS Region | `ap-northeast-1` |
| Parameter SecretName | `asb/config` |
| Confirm changes before deploy | `y` |
| Allow SAM CLI IAM role creation | `Y` |
| Disable rollback | `N` |
| Create managed ECR repositories | `Y` |
| **…Function URL … no auth … Is this okay?** | **`y`**（意図通り。アプリ内で Bearer 認証） |
| Save arguments to configuration file | `Y` |

出力（Outputs）の **`FunctionUrl`** を控える。

**コードを更新したときの再デプロイ**（`git pull` のあと）：

```bash
export DOCKER_HOST=unix://$HOME/.docker/run/docker.sock
sam build -t infra/template.yaml
sam deploy
```

`sam build` には毎回 `-t infra/template.yaml` が必要（省くと `Template file not found at .../template.yml`）。`sam deploy` はビルド結果と `samconfig.toml` を自動で使うので引数不要。Function URL は変わらないので、ショートカットの修正は要らない。

> ⚠️ **つまずき⑦：`sam build` が「container runtime が無い」**
> Docker は動いているのに SAM が見つけない場合、macOS + Docker Desktop で既定ソケット `/var/run/docker.sock` が無いのが原因。次のどちらかで解決：
> ```bash
> export DOCKER_HOST=unix://$HOME/.docker/run/docker.sock   # そのターミナルで有効
> ```
> （恒久化は `echo 'export DOCKER_HOST=unix://$HOME/.docker/run/docker.sock' >> ~/.zshrc`）
> または Docker Desktop → Settings → Advanced → 「Allow the default Docker socket to be used」をオン。
>
> ⚠️ **つまずき⑧：`sam deploy` の ECR push がタイムアウト**
> 初回はイメージ（数百 MB）を ECR に push するため、回線次第で `timeout awaiting response headers` が出ることがある。**`sam deploy` を数回再実行**すれば、アップ済みレイヤーはスキップされて完了する（今回は 3 回目で成功）。作り直しは不要。安定した回線推奨。

---

## 6. 動作確認（curl）

```bash
curl -X POST "<FunctionUrl>" \
  -H "Authorization: Bearer <ASB_AUTH_SECRET>" \
  -H "Content-Type: application/json" \
  -d '{"input":"<好きな概念やURL>"}' \
  --output out.png -D -
open out.png
```
- `-D -` はレスポンスヘッダ表示。**`x-asb-commit: ...`** が返れば GitHub 保存まで成功。
- `asb-vault` に新しいコミット（ノート＋画像）が入る。
- `{"input":"...","guidance":"...","pages":2}` を受け付ける（`pages` は最大 3）。

> トラブル時：**401**＝合言葉不一致、**404 で publish 失敗**＝手順3（Vault 初期化）未実施、**500**＝生成/保存失敗（下記ログ）。
> ```bash
> sam logs --stack-name asb-serverless --start-time '20min ago'
> ```

---

## 7. iOS ショートカット（実機の入口）

「ショートカット」アプリで新規作成し、以下の 3 アクションを並べる。

1. **テキストを尋ねる**（無ければ次の `input` を「毎回尋ねる」にすれば代用可）
2. **URL の内容を取得**：
   - **URL**：`<FunctionUrl>`（★ここを「テキスト変数」ではなく **URL 文字列**にするのが要）
   - 方法：**POST**
   - ヘッダ：`Authorization` = `Bearer <ASB_AUTH_SECRET>` ／ `Content-Type` = `application/json`
   - 本文を要求：**JSON** → フィールド追加 `input`（値は手順1の入力、または「**毎回尋ねる**」）。任意で `pages`（数値）。
3. **クイックルック**（返ってきた「URL の内容」＝画像を表示）。任意で **「写真アルバムに保存」** を追加。

> ⚠️ **つまずき⑨：取得先 URL に変数が入っている**
> 「URL の内容を取得」の一番上が「（テキスト変数）の内容を取得」になっていると、変数を URL として POST してしまい失敗する。青い変数を消し、**Function URL を直接入力**する（「URL の内容を取得」と表示されれば正）。
>
> ⚠️ **つまずき⑩：ショートカットが約 60 秒でタイムアウト**
> iOS の「URL の内容を取得」は約 60 秒で打ち切られる（設定変更不可）。生成が長いと画像が表示されない（サーバー側は成功していて `asb-vault` には保存されている）。**本リポジトリではクラウド経路を高速化済み**：教育プランをスキップし（[Issue #42](https://github.com/ttk1010/ai-second-brain/issues/80)）、画像は `gpt-image-2` より約2倍速い `gpt-image-2.5-flare` の `high` で生成する（1枚約25秒、[Issue #45](https://github.com/ttk1010/ai-second-brain/issues/89)）。手元の CLI（`asb`）は引き続き `gpt-image-2`。

---

## 8. Mac への取り込み（ノートを Vault へ）

画像はショートカットで即見られる。ノート本文を Mac の Vault に反映したい時は:
```bash
git -C "/Users/<you>/Documents/ai-catchup/Vault" pull --ff-only
```
起動時の自動化（launchd）は、Vault をローカルでも編集するため「未コミットのローカル変更で pull が止まる」等の注意があり、堅牢な双方向同期はもう一段の設計が要る（後日整備）。まずは手動 pull で運用。

---

## 9. コスト・セキュリティ

- インフラは未使用時ゼロスケール。個人利用は概ね無料枠内、**課金は OpenAI の従量分（画像 1 枚数円）**のみ。1 リクエストのイラストは最大 3 枚。
- **課金アラーム**（CloudWatch Billing / Budgets）を設定推奨。
- **Function URL と合言葉のセットは公開しない**（URL 単体は認証で守られるが、両方揃うと誰でも叩ける）。
- 秘密のローテーション：Secrets Manager を更新 → `sam deploy` で反映。合言葉を変えたらショートカットの Bearer も更新。

## スコープ外（後続フェーズ）

会話しながらの生成（MCP コネクタ）、Telegram 連携、既存ノートのイラスト改善（#29）のリモート化、認証強化（IAM/OAuth）、起動時 launchd 自動 pull の堅牢化。
