# クラウド生成ガイド（GitHub Actions + Secrets）

Claude のクラウドセッション（claude.ai/code）やモバイルから、ローカルマシンなしで
ノート＋イラストを生成する手順です。GitHub Actions のランナー上で `asb` を実行し、
生成物を Vault リポジトリに push します（Issue #43 / #84）。

この方式の要点は **OpenAI API キーが Actions Secrets の中に留まる**ことです。
クラウドセッション（LLM のコンテキスト）にはキーが一切渡らないため、プロンプト
インジェクション等でキーが漏れる経路がありません。ログ上も自動でマスクされます。

[サーバーレス即時生成](DEPLOY_SERVERLESS.md)（Issue #42）との使い分け：

| | Actions 経由（本ガイド） | Lambda 経由（#42） |
|---|---|---|
| 主な用途 | クラウドセッション・重い生成 | スマホからの即時生成 |
| 追加インフラ | なし（GitHub のみ） | AWS（SAM デプロイ） |
| 呼び出し側の認証 | GitHub 認証のみ | API エンドポイントの認証情報 |
| 実行時間の制約 | 緩い（複数ページ生成も可） | モバイルタイムアウトに合わせ最適化 |

## 1. 事前準備（初回のみ・手元で実施）

### 1-1. Vault 書き込み用 PAT の発行

GitHub の **Settings → Developer settings → Fine-grained personal access tokens** で
新規トークンを発行します：

- Repository access: **asb-vault のみ**
- Permissions: **Contents → Read and write** のみ
- 有効期限は運用に合わせて設定（失効したら再登録）

### 1-2. Secrets の登録

`ai-second-brain` リポジトリに 2 つの Secret を登録します（値を貼り付けるのは
自分のターミナルで行ってください）：

```bash
gh secret set OPENAI_API_KEY
```

```bash
gh secret set VAULT_PUSH_TOKEN
```

（それぞれ実行するとプロンプトが出るので、キー / PAT を貼り付けて Enter。）

## 2. 使い方

### クラウドセッション・ターミナルから

```bash
gh workflow run generate-note.yml -f input="Transformer"
```

オプション付きの例：

```bash
gh workflow run generate-note.yml \
  -f input="3次元スキャン" \
  -f guidance="ロボティクス向けに、LIOを中心に" \
  -f pages=3
```

比較ノート：

```bash
gh workflow run generate-note.yml -f input="GPT, Claude, Gemini" -f compare=true
```

その他の入力：`no_image=true`（イラスト省略・低コスト）、`overwrite=true`
（既存ノートの再生成）。フラグの意味は CLI（`uv run asb --help`）と同じです。

実行状況の確認：

```bash
gh run list --workflow=generate-note.yml --limit 3
gh run watch
```

### GitHub モバイルアプリから

リポジトリ → Actions → **Generate note** → Run workflow から、フォーム入力で
起動できます（Claude を介さない最小経路）。

## 3. 結果の受け取り

生成されたノート＋イラストは asb-vault の `main` に push されます。

- ローカル: Vault ディレクトリで `git pull`
- モバイル: Obsidian の Vault 同期経由（同期設定に依存）

## 4. 挙動の補足

- **冪等性**: 既存の概念/URL はスキップされ、その場合は何も push されません
  （再課金なし）。再生成したいときだけ `overwrite=true` を指定します。
- **同時実行**: ワークフローは 1 本ずつ実行され（concurrency）、push 直前に
  `git pull --rebase` するため、ローカルや Lambda 経由の push と衝突しません。
- **コスト**: 生成ごとに通常の OpenAI 課金（イラストが支配的）が発生します。
  GitHub Actions の実行時間もプライベートリポジトリでは無料枠を消費します。

## トラブルシューティング

- **`OPENAI_API_KEY` 関連で失敗する** — Secrets が未登録（手順 1-2）。
- **vault への push が 403** — `VAULT_PUSH_TOKEN` の期限切れ、または権限不足
  （asb-vault の Contents: Read and write が必要）。
- その他は [TROUBLESHOOTING.md](TROUBLESHOOTING.md) を参照。
