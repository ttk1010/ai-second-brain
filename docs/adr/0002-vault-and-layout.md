# ADR 0002: Vault location, Git tracking scope, and backend layout

- Status: Accepted
- Date: 2026-06-26
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

初期ドキュメントは Obsidian Vault をコードリポジトリ内の `vault/` ディレクトリに置く前提で書かれていた。しかしプロジェクトの方針として、Vault は **リポジトリ外のユーザー所有の Obsidian Vault** を指すことが確定した（`config/settings.example.toml` の `vault_path` が外部絶対パスを取ることと一致する）。

この決定により、以下のドキュメントが現状と矛盾する:

- `README.md` — リポジトリ構造に `vault/` を含み、「Knowledge lives inside the Vault」と記述
- `CLAUDE.md` — リポジトリ構造と責務一覧に `vault/` を含む
- `docs/ARCHITECTURE.md` — リポジトリレイアウトに `vault/` を含み、パイプライン図末尾の「Vault → Git → GitHub」がコードリポジトリの Git と混同されうる

また `backend/` 内部のモジュール構成が正式に採択されていなかった。

本 ADR は Vault の配置・Git 追跡範囲・`backend/` 内部レイアウトを確定する。データモデル・コンポーネント境界は ADR 0001 を参照。

## Decision

### A. Vault is external; this repository tracks only code and docs

Obsidian Vault はこのコードリポジトリの**外部**に存在し、設定 `vault_path`（絶対パス）で指定される。生成された Knowledge Node はその外部 Vault 配下に保存される。

このコードリポジトリが Git で追跡するのは **`backend/` / `docs/` / `scripts/` / `tests/`** のみとする。`vault/` ディレクトリはリポジトリ構造から除外する。

### B. Adopt the backend/ internal layout

`backend/` の内部レイアウトとして、ARCHITECTURE.md が示す以下のモジュール構成を正式採択する:

```
backend/
    parser/      # 入力分類・抽出 (Concept / News)
    planner/     # Educational Plan の生成
    prompts/     # プロンプトテンプレート (コードに埋め込まない)
    image/       # イラスト生成 (ImageProvider 抽象越し)
    markdown/    # Markdown 生成
    linker/      # 関係性の付与
    storage/     # 外部 Vault / Git 永続化
    services/    # パイプライン統合 (オーケストレーション)
    models/      # Knowledge Object / Node のデータ構造
    config/      # 設定の読み込みと検証 (横断的関心事; Issue #5 で追加)
```

CLAUDE.md のフラットなトップレベル構成（backend/ docs/ scripts/ tests/）はそのままに、「`backend/` 内部の構成は ARCHITECTURE.md で定義」と注記する。

### C. Reinterpret the "Vault → Git → GitHub" flow

パイプライン図末尾の「Vault → Git → GitHub」は、**外部 Vault 自身の任意のバージョン管理**を指す。すなわち、外部 Vault が Git 管理下に置かれている場合に、設定 `auto_commit` が有効なら生成ノートをコミットする、という意味である。これは**このコードリポジトリの Git とは別物**であり、ドキュメント上でその旨を明記する。

## Consequences

- リポジトリ構造が `backend/ docs/ scripts/ tests/` の4ディレクトリに整理され、ユーザーの知識データがコードの版管理に混入しない。
- `backend/` の内部レイアウトが確定し、Issue #3 以降の実装が従う土台になる。
- Storage 層（Issue #9）は外部 `vault_path` への書き込みとして実装され、`auto_commit` は外部 Vault の Git 操作として扱われる。
- ユーザーは Vault の同期・バックアップ（Obsidian Sync や独自 Git リポジトリ等）を自分で選択できる。

## Alternatives considered

- **Vault をリポジトリ内 `vault/` に置く**: コードと知識データが同一リポジトリに混在し、知識の肥大化がコードの版管理に影響する。また Obsidian の実体 Vault と二重管理になるため不採用。
- **`vault/` をリポジトリ内に置き、外部 Vault へシンボリックリンクする**: 構成が複雑になり「意図的に単純な構造」という方針に反するため不採用。外部パス参照（`vault_path`）に一本化する。
