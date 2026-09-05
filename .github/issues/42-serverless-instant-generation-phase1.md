# Issue #42: 外出先からの即時生成 — サーバーレス化 Phase 1（HTTP生成API＋SAM＋Git保存）

Labels: enhancement, infrastructure, services

## Why
現状はローカルファースト（ADR 0006）で、**Mac がオフだと外出先から生成できない**。課題の本質は「外出先で思いついた瞬間に、家の Mac 抜きでイラストを生成して見たい」という即時性。方針は [ADR 0015](../../docs/adr/0015-serverless-instant-generation.md)（Proposed）で決定済み：**ローカル経路を残したまま、AWS Lambda の常時稼働エンドポイントを1本足す。生成は OpenAI 直叩きのまま、AWS は実行＋配信だけを担う。**

構成図は [docs/architecture-diagrams.md](../../docs/architecture-diagrams.md) の図2。

## Goal（Phase 1 のスコープ）
外出先の iPhone から HTTP で概念/URL を送ると、**Lambda が既存 `backend/` パイプラインを実行 → 画像を即返信 → ノート＋画像を Git(Vault) に保存**する、最小構成を作る。認証は簡易、入口はまず iOS ショートカットのみ。Telegram / Claude MCP アダプタ、既存ノートのイラスト改善（#29 のリモート化）は後続フェーズ。

## 決定事項（すり合わせ済み）
- **同期返信＝Lambda Function URL**（API Gateway の ~29 秒制限を回避。Function URL は最大 15 分で `gpt-image-2` の数十秒生成に耐える）。非同期（即 ACK→通知）は将来必要なら Phase 2。
- **Git 保存＝GitHub API（Git Data API）で 1 コミット**（clone 不要・軽量で Lambda 向き、Vault が画像で肥大しても重くならない）。ローカルは既存 `VaultWriter`、クラウドは `GitHubVaultWriter`（API commit）＝プロバイダ抽象の追加実装。

## 提案する設計
- **生成API（素の HTTP・Lambda Function URL 同期）**：`POST /generate {input, guidance?, pages?}` → `KnowledgePipeline.run(...)` を実行。生成物（画像バイト＋ノートのメタ）を返す。入口非依存にして、フロントはアダプタで後付け。
- **Git バックエンド保存（GitHub API）**：生成ノート＋画像を private GitHub リポジトリに **Git Data API で 1 コミット**（`VaultWriter` 抽象のクラウド実装）。#39 の in-place 方針（名前維持）を踏襲。
- **パッケージ/デプロイ**：`backend/` ＋依存をコンテナイメージ化（Dockerfile）。**AWS SAM** で Lambda（コンテナ）／エンドポイント／IAM ロール／Secrets 参照／CloudWatch を定義。`infra/`（新規トップレベル）に SAM テンプレートを置く。
- **Lambda は VPC 外**（OpenAI への外向き通信のため）。シークレット（`OPENAI_API_KEY`、Git 認証）は **Secrets Manager**。
- **入口**：iOS ショートカット（共有シート/1タップ→POST→画像表示）。手順を docs 化。

## Tasks
- [ ] `POST /generate` の Lambda ハンドラ（入力バリデーション→`build_pipeline` 相当→パイプライン実行→レスポンス整形）
- [ ] Git バックエンドの保存経路（ノート＋画像を commit/push、冪等、名前維持）
- [ ] Dockerfile（Lambda コンテナ）＋依存の同梱
- [ ] `infra/` に AWS SAM テンプレート（Lambda / エンドポイント / IAM / Secrets / Logs）
- [ ] Secrets（`OPENAI_API_KEY`・Git 認証）を Secrets Manager から読む配線
- [ ] iOS ショートカット導入手順を docs に追記
- [ ] 単体テスト（ハンドラ：モックパイプライン＋モック Git。外部API/ネットワーク非依存）
- [ ] README / architecture-diagrams に Phase 1 の使い方・デプロイ手順を追記、ADR 0015 を Accepted に更新

## Definition of Done
- iPhone から HTTP で送ると、数十秒以内に**イラストが返る**
- 生成ノート＋画像が **Git(Vault) に保存**され、Mac / iPhone の Obsidian が pull で受け取れる
- 生成は OpenAI 直叩きのまま（`backend/` 無改修で再利用）
- インフラは SAM で再現デプロイでき、シークレットはコードに含まれない
- 外部API/ネットワーク非依存でハンドラのテストが通る

## Open questions（実装前に決める）
1. ~~同期返信のタイムアウト~~ → **決定：Lambda Function URL 同期**。
2. ~~Git 保存の実装~~ → **決定：GitHub API（Git Data API）で 1 コミット**。
3. **Vault の Git 化範囲**：Vault 全体を1つの Git repo にするか、**生成分だけの別 repo**にして Mac 側で本 Vault にマージするか（既存 iCloud Vault との整合）。
4. **認証**：エンドポイント保護（簡易 API キーのヘッダ / 署名 / 自分の端末のみ）。Phase 1 は共有シークレット＋Secrets Manager で十分か。
5. **返信フォーマット**：画像バイト直返し / 署名付き URL（S3）/ Base64。iOS ショートカットで表示しやすい形。
6. **Lambda 設定**：メモリ・タイムアウト・イメージサイズの初期値、コスト上限（1 リクエストあたりの上限枚数など）。

## フェーズ / 扱い
ADR 0015 の Phase 1。以降：Phase 2＝Telegram / Claude MCP アダプタ・認証強化・エラー/コスト整流、Phase 3＝既存ノートのイラスト改善（#29）のリモート化。番号付きフェーズには束ねず、ADR 0015 に紐づく独立の enhancement。
