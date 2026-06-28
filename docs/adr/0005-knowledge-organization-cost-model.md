# ADR 0005: 知識 organization — コストモデル、リンカー設計、KO 非永続化

- Status: Accepted
- Date: 2026-06-28
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

Phase 3 で「孤立したノートをつながった知識にする」（関連ノート検出・バックリンク・概念リレーション）を実装するにあたり、コストを最小化したいという強い要件があった。

関連付けは方式次第でコストが激変する: ノート総当たりの LLM 比較は O(n²) で高価、OpenAI 埋め込みは課金、ローカル埋め込みは重い依存。一方ユーザーは Claude Pro サブスクを保有しており、「Claude Code を使えば追加課金なしで賢い処理ができる」点を活かしたい。

あわせて、以前から保留していた「Knowledge Object 自体を JSON 等で永続化すべきか」も決める必要がある。

## Decision

### A. 生成は OpenAI、organization の知能は Claude Code

コストの基本方針を次のとおり定める:

- **1件ごとの生成**（概念/ニュースの抽出・教育設計・イラスト）は従来どおり OpenAI API を使う。
- **Vault 横断の「賢い」処理**（意味的な関連付け等）は **OpenAI API を呼ばず、Claude Code のスキルとして実行**し、ユーザーの Claude サブスク内で行う（追加の従量課金なし）。

この方針の具体例が Phase 3 の `asb-relink` スキルであり、Phase 4 の Claude Code Channels も同じ思想（賢い処理を Claude 側へ寄せる）に立つ。

### B. リンカーは「決定論的な機構」と「LLM の判断」を分離

- **機構（決定論的 Python・無料・テスト可能）**: Vault 索引（frontmatter 読み取り）と「Related Notes セクションのみを安全・冪等に書き換える」処理（`backend/linker/`、`asb-link` CLI）。
- **判断（Claude）**: どのノートが関連し、関係型が何か。`asb-relink` スキルが索引を読んで判断し、機構経由で書き込む。

書き込みは **Related Notes セクションに限定**し、既存ノートの他部分は変更しない。逆方向リンク（バックリンク）は **Obsidian ネイティブ機能に委ね**、ノートを二重に書き換えない。

### C. Knowledge Object は別途永続化しない

Knowledge Object は実行時のメモリ表現に留め、JSON 等での永続化は行わない。**Markdown frontmatter（title / id / tags / source_type 等）を正本**とし、organization に必要な構造化データはそこから索引で復元する。

### D. 埋め込み / ベクトル検索は先送り

OpenAI 埋め込みやベクトル検索（課金・依存増）は Phase 6 まで導入しない。必要性が明確になった時点で再検討する。

## Consequences

- 知識の organization が **追加の OpenAI 課金ゼロ**で回る。ノートが増えるほどグラフが育つ一方、定常コストは増えない。
- 機構/判断の分離により、ファイル破損リスクを Python 側で抑えつつ、表記揺れや概念的近さは Claude が拾える。再実行は冪等。
- KO 非永続化により二重管理（Markdown と KO JSON の同期ずれ）を避けられる。一方、frontmatter に無い情報は organization で使えないため、必要なら frontmatter 側を拡張する（ADR 0001 の `outputs` は参照のみの方針を維持）。
- 「賢い処理は Claude Code」という方針は Claude サブスクの存在を前提とする。サブスクがない環境では決定論的機構（`asb-link`）のみで縮退利用する形になる。

## Alternatives considered

- **関連付けを OpenAI API（LLM 総当たり or 埋め込み）で行う**: コストが O(n²) または従量課金で増大し、最小コスト要件に反するため不採用。Claude Code（サブスク内）に寄せる。
- **Knowledge Object を JSON で永続化**: Markdown と二重管理になり同期ずれリスクが増える。frontmatter から復元できるため不要と判断。
- **バックリンクを明示的にファイルへ書き込む**: 既存ノートを広範に書き換えることになり破損リスクが上がる。Obsidian ネイティブのバックリンクで足りるため不採用。
