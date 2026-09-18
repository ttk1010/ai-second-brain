# アーキテクチャ図（Before / After）

AI Second Brain の構成を図で示す。**図1が現行（local-first）**、**図2が計画中の Phase 1（AWS Lambda によるサーバーレス化）**である。図2は提案段階で、決定は ADR 0015（Proposed）で管理する。

GitHub / Zenn はいずれも Mermaid をネイティブ描画するため、下記はそのまま図として表示・再利用できる。

## 図1：現行アーキテクチャ（local-first / ADR 0006）

入口・生成・保存がすべて手元の Mac 上にあり、Vault は iCloud で iPhone に同期される（閲覧のみ）。**Mac が起動していないと生成できない**のが制約。

```mermaid
flowchart LR
  classDef ext fill:#E6F6F6,stroke:#0B8A8F,stroke-width:1.5px,color:#0a3d3f;
  classDef store fill:#EEF1F5,stroke:#55606E,stroke-width:1.5px,color:#1B2430;
  subgraph LOCAL["ローカル Mac（起動時のみ動作）"]
    ENTRY["入口<br/>asb / asb-inbox / asb-revise<br/>Telegram 受信"]
    subgraph PIPE["backend/ パイプライン"]
      P1["classify → extract → plan"]
      P2["Knowledge Object"]
      P3["illustrate"]
      P4["Markdown 生成"]
      P1 --> P2 --> P3 --> P4
    end
    ENTRY --> P1
    P4 --> VW["VaultWriter"]
    VW --> VAULT[("Obsidian Vault<br/>~/Documents · iCloud 同期")]
  end
  OAI["OpenAI API<br/>Chat gpt-5.4 / Images gpt-image-2"]
  P1 -.->|HTTPS| OAI
  P3 -.->|HTTPS| OAI
  VAULT -.->|"iCloud · 閲覧のみ"| IPH["iPhone"]
  class OAI ext
  class VAULT,IPH store
```

## 図2：Phase 1 アーキテクチャ（serverless / 提案・ADR 0015）

外出先の iPhone から **Lambda Function URL（HTTPS）**で Lambda を直接呼び、同じ `backend/` パイプラインを実行して**画像をその場で返信**する（同期。Function URL は最大 15 分で `gpt-image-2` の数十秒生成に耐える）。生成は **OpenAI 直叩きのまま**（`gpt-image-2` の絵柄・複数参照 edit・日本語ラベルを維持）で、AWS は「常時稼働の実行＋配信」だけを担う。ノートは **GitHub API のコミット**で Mac / iPhone の Obsidian に同期する。ローカル経路（図1）も併存する。

```mermaid
flowchart LR
  classDef ext fill:#E6F6F6,stroke:#0B8A8F,stroke-width:1.5px,color:#0a3d3f;
  classDef store fill:#EEF1F5,stroke:#55606E,stroke-width:1.5px,color:#1B2430;
  classDef aws fill:#FFF4EA,stroke:#EC7211,stroke-width:1.5px,color:#7a3b06;
  subgraph PHONE["iPhone（外出先）"]
    SC["入口<br/>iOS ショートカット<br/>POST /generate"]
  end
  subgraph CLOUD["AWS クラウド"]
    FURL["Lambda Function URL<br/>（HTTPS · 同期）"]
    subgraph LAM["Lambda（コンテナ · SAM デプロイ）"]
      PIPE["backend/ パイプライン<br/>classify → extract → plan → illustrate → markdown"]
    end
    SM["Secrets Manager<br/>OPENAI_API_KEY / GitHub PAT"]
    CW["CloudWatch Logs"]
  end
  OAI["OpenAI API<br/>gpt-5.4 / gpt-image-2<br/>直叩き・変更なし"]
  GIT[("GitHub リポジトリ<br/>Vault · private")]
  SC -->|"① 概念 / URL"| FURL
  FURL --> PIPE
  SM -.->|IAM| PIPE
  PIPE --> CW
  PIPE -.->|HTTPS| OAI
  PIPE -->|"② 画像を即返信"| SC
  PIPE -->|"③ GitHub APIでcommit"| GIT
  GIT -.->|pull| MAC["Mac（Obsidian Git）"]
  GIT -.->|pull| OBS["iPhone（Obsidian）"]
  class OAI ext
  class GIT,MAC,OBS store
  class FURL,SM,CW,PIPE aws
  style CLOUD fill:#fff9f3,stroke:#EC7211,color:#7a3b06
  style LAM fill:#fffdfb,stroke:#EC7211,color:#7a3b06
```

## 変わる点 / 変わらない点

| | 内容 |
| --- | --- |
| **変わる点** | 入口が iPhone → Lambda Function URL に（Mac 起動に非依存で即時生成）／実行は Lambda（未使用時ゼロスケール、個人利用は無料枠内）／保存は GitHub API コミット |
| **変わらない点** | 生成は OpenAI 直叩き（`gpt-image-2`）／`backend/` パイプラインと Knowledge Object 設計は無改修／プロバイダ抽象は維持（将来 `BedrockImageProvider` も差し替え可能）／ローカル経路も併存 |

## 補足

- **Bedrock は今回見送り**：Bedrock の画像モデルは Nova / Stability 系のみで `gpt-image-2` が無く、検証済みの絵柄・複数参照 edit・画像内日本語を失うため。プロバイダ抽象は残すので将来の選択肢としては保持する。
- 関連：[ADR 0005](adr/0005-knowledge-organization-cost-model.md)（コストモデル）、[ADR 0006](adr/0006-capture-interface-local-first.md)（capture local-first）、ADR 0015（serverless 化・Proposed）。
