# ADR 0015: 外出先からの即時生成のためのサーバーレス（AWS Lambda）エンドポイント

- Status: Accepted
- Date: 2026-09-05
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

現状はローカルファースト（[ADR 0006](0006-capture-interface-local-first.md)）で、入口・生成・保存がすべて手元の Mac 上にある。Telegram / Inbox で外出先から投げても、**Mac が起動していないと生成されない**。実際の課題は「外出先で思い立った瞬間に、家の Mac 抜きでイラストを生成して見たい」という**即時性**である。これは ADR 0006（常時稼働サーバを持たない）と [ADR 0005](0005-knowledge-organization-cost-model.md)（固定費ゼロ）の前提に関わる。

選択肢とコストを調査した（2026-09 時点）:
- **常時稼働 VPS（Lightsail 等）**：月 $3.5〜5 の固定費。単純だが ADR 0005 に反する。
- **サーバーレス（AWS Lambda）**：無料枠（月 100 万リクエスト＋40 万 GB 秒が恒久）内で個人利用は**実質 $0/月**、未使用時ゼロスケール。
- **サーバーなしハイブリッド（iOS ショートカット→OpenAI 直＋iCloud Inbox）**：$0 だが即時画像が KO 設計を通らず、プロンプトを二重管理になる。
- 生成モデルの供給元：**OpenAI 直叩き** か **Amazon Bedrock** か。Bedrock の画像モデルは Nova / Stability 系のみで **`gpt-image-2` が無く**、検証済みの絵柄・複数参照 edit・画像内日本語を失う。

## Decision

**ローカル経路（ADR 0006）を残したまま、常時稼働の「サーバーレス・エンドポイント」を1本追加する。**

1. **AWS Lambda + HTTP エンドポイント**が既存の `backend/` パイプラインを実行し、生成画像を即返信する。ローカル CLI / Inbox / Telegram は併存（置き換えない）。
2. **生成は OpenAI 直叩きのまま**（`gpt-image-2`）。**Bedrock は採用しない**（`gpt-image-2` 非対応）。ただしプロバイダ抽象（`LLMProvider` / `ImageProvider`）は維持し、将来 `BedrockImageProvider` 等を差し替えられる余地は残す。
3. **Vault 同期は Git 経由**。Lambda（Linux）は iCloud を使えないため、生成ノート＋画像を private Git リポジトリに commit し、Mac / iPhone の Obsidian が pull で受け取る。
4. **IaC は AWS SAM、パッケージはコンテナイメージ、Lambda は VPC に入れない**（OpenAI への外向き通信のため）。シークレット（`OPENAI_API_KEY` 等）は **Secrets Manager**。
5. **入口はエンドポイントから分離**：Lambda は素の `POST /generate` を公開し、フロント（まず iOS ショートカット、将来 Telegram / Claude MCP）は**アダプタ**として後付けする。

### ADR 0005 / 0006 への影響
- ADR 0005（固定費ゼロ）を「**ほぼゼロ（無料枠内・ゼロスケール）**」へ緩める。VPS のような常時課金は避ける。
- ADR 0006（ローカルファースト）を**覆さない**。ローカル経路は維持し、常時稼働コンポーネントを1つ**追加**する位置づけ。両 ADR は書き換えず、本 ADR が補足する。

## Consequences

- 外出先から Mac 非依存で即時生成できる。個人利用ではインフラ費は実質ゼロ。
- 新規要素：AWS アカウント運用、Secrets Manager、SAM デプロイ、**Git バックエンドの保存経路**（既存 `VaultWriter` のクラウド版）。Vault を Git 管理にする必要がある。
- `backend/` パイプライン・KO 設計・プロンプト資産は**無改修で再利用**（Knowledge First / プロンプト単一管理を維持）。
- 技術的制約：`gpt-image-2` の生成は数十秒かかりうる。同期返信の経路（API Gateway か Lambda Function URL か）はタイムアウト上限に注意して選ぶ（Phase 1 Issue の Open questions で確定）。

## Alternatives considered

- **常時稼働 VPS**：単純だが月額固定費が発生し ADR 0005 に反する。サーバーレスの無料枠・ゼロスケールを優先。
- **Bedrock 採用**：AWS 内に閉じられるが `gpt-image-2` が無く絵柄を失う。OpenAI 直叩きを維持し、抽象で将来の選択肢は保持。
- **サーバーなしハイブリッド（iOS ショートカット直）**：$0・最速だが KO 設計を通らずプロンプト二重管理。即時プレビューの暫定策としては有効だが本命にはしない。
- **VPC 内 Lambda**：不要な NAT コスト・複雑さ。OpenAI 直叩きには VPC 外で十分。
