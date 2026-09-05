# Issue #42: 外出先からの即時生成 — サーバーレス化 Phase 1（HTTP生成API＋SAM＋Git保存）

Labels: enhancement, infrastructure, services

## Why
現状はローカルファースト（ADR 0006）で、**Mac がオフだと外出先から生成できない**。課題の本質は「外出先で思いついた瞬間に、家の Mac 抜きでイラストを生成して見たい」という即時性。方針は [ADR 0015](../../docs/adr/0015-serverless-instant-generation.md)（Proposed）で決定済み：**ローカル経路を残したまま、AWS Lambda の常時稼働エンドポイントを1本足す。生成は OpenAI 直叩きのまま、AWS は実行＋配信だけを担う。**

構成図は [docs/architecture-diagrams.md](../../docs/architecture-diagrams.md) の図2。

## Goal（Phase 1 のスコープ）
外出先の iPhone から HTTP で概念/URL を送ると、**Lambda が既存 `backend/` パイプラインを実行 → 画像を即返信 → ノート＋画像を Git(Vault) に保存**する、最小構成を作る。認証は簡易、入口はまず iOS ショートカットのみ。Telegram / Claude MCP アダプタ、既存ノートのイラスト改善（#29 のリモート化）は後続フェーズ。

## 提案する設計
- **生成API（素の HTTP）**：`POST /generate {input, guidance?, pages?}` → `KnowledgePipeline.run(...)` を実行。生成物（画像バイト＋ノートのメタ）を返す。入口非依存にして、フロントはアダプタで後付け。
- **Git バックエンド保存**：ローカル `VaultWriter` のクラウド版として、生成ノート＋画像を private Git リポジトリに commit/push（`ImageProvider`/`VaultWriter` 抽象は再利用）。#39 の in-place 方針（名前維持）を踏襲。
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
1. **同期返信のタイムアウト**：`gpt-image-2` の生成は数十秒かかりうる。**API Gateway(HTTP API) は統合タイムアウト ~29 秒**の上限があるため、超過時は同期返信できない。**Lambda Function URL（最大 15 分）で同期返信**にするか、API Gateway＋非同期（即 ACK→後でプッシュ/Telegram 返信）にするか。← Phase 1 は Function URL 同期が最有力。
2. **Git 保存の実装**：Lambda 内で `git clone/commit/push`（/tmp 作業）か、**GitHub Contents API** 経由か。画像バイナリの扱い・冪等性・競合。
3. **Vault の Git 化範囲**：Vault 全体を1つの Git repo にするか、**生成分だけの別 repo**にして Mac 側で本 Vault にマージするか（既存 iCloud Vault との整合）。
4. **認証**：エンドポイント保護（簡易 API キーのヘッダ / 署名 / 自分の端末のみ）。Phase 1 は共有シークレット＋Secrets Manager で十分か。
5. **返信フォーマット**：画像バイト直返し / 署名付き URL（S3）/ Base64。iOS ショートカットで表示しやすい形。
6. **Lambda 設定**：メモリ・タイムアウト・イメージサイズの初期値、コスト上限（1 リクエストあたりの上限枚数など）。

## フェーズ / 扱い
ADR 0015 の Phase 1。以降：Phase 2＝Telegram / Claude MCP アダプタ・認証強化・エラー/コスト整流、Phase 3＝既存ノートのイラスト改善（#29）のリモート化。番号付きフェーズには束ねず、ADR 0015 に紐づく独立の enhancement。
