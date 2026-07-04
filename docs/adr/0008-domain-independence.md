# ADR 0008: ドメイン非依存化（AIをデフォルト重点分野とする）

- Status: Accepted
- Date: 2026-07-05
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

これまで本プロダクトは「AI関連の知識」を前提に設計されていた。モデル・パイプライン・Markdown テンプレート・フォルダ構成の多くは既に汎用だが、**プロンプト**が AI 固有だった（例：「AI knowledge base」「AI concept を software engineer 向けに説明」「AI-related news」）。プロダクトオーナーは、AI に限らずユーザーがインプットした**あらゆる分野の知識**を Knowledge Object 化して Obsidian に蓄積したい（Issue #34）。

汎用化の度合い・ドメインの扱い・対象読者の決め方などを決める必要がある。名称「AI Second Brain」ブランドは維持する。

## Decision

### A. 汎用化の度合い — AIをデフォルト重点分野として残す

完全なドメイン中立ではなく、**AI をデフォルト（参照）ドメイン**に据えつつ任意分野を扱えるようにする。プロンプトは分野を入力から推定し、AI と判断できる場合は自然に AI として扱う。既存の AI 用途は劣化させない（回帰なし）。

### B. 対象読者/トーン — 固定デフォルト読者＋分野で用語の深さを調整

全分野共通のデフォルト読者を一つ置く：「知的好奇心のある一般の学習者（その話題の初学者）」。従来の「software engineer」固定を廃し、`backend/prompts/domain.py` の `DEFAULT_READER` に一元化して concept / news / comparison / planning の全 system prompt で共有する。LLM には分野を推定させ、その分野に応じて用語の深さだけ調整させる。ユーザーによる都度指定（「高校生向けに」等）は将来の生成時ガイダンス（#32）で上乗せする。

### C. ドメインは軽いメタデータにする

`Metadata.domain: str | None` を追加する。抽出スキーマに `domain` を加え（AI 関連なら "AI"、それ以外は分野名、不明なら空）、Builder が正規化して格納する。Markdown では frontmatter の `domain:` 行と、先頭タグ（`#<domain>`）として出力する。空のときは一切出力しない（既存ノートに影響なし）。

### D. フォルダ taxonomy は当面据え置き（型ベースのまま）

「AI とそれ以外」を物理フォルダで分ける案（例 `AI/06 News`）は、既存ノートの移動と冪等判定（#24 の `find_existing`）の破綻リスクが大きく、DoD「回帰なし」に反する。今回は**型ベースの平坦なフォルダ（01 Concepts / 04 Comparisons / 06 News / 07 Papers）を維持**し、分野は `domain` メタデータ＋タグで表現する。分野別フォルダ振り分けは、必要になった時点で別 Issue として扱う。

## Consequences

- concept / news / comparison / planning のプロンプトから AI 固有前提が外れ、任意分野の入力で適切なトーン・対象読者の Knowledge Object が生成される。
- `Metadata.domain` により分野がタグ・frontmatter・将来のフィルタ/フォルダ振り分けに使える。空の既存挙動は不変。
- 対象読者が全プロンプトで一元管理され、トーンの一貫性が保たれる。
- フォルダは変わらないため、既存 Vault と冪等生成に影響しない。

## Alternatives considered

- **完全ドメイン中立**：AI という参照点を失い、AI 記事の質が落ちるリスク。AI をデフォルト重点に残す案を採用。
- **読者を毎回 LLM に全自動推定させる（案A）**：手間ゼロだがノート間で読者像がブレる。固定デフォルト＋分野調整（案B）で一貫性を優先。
- **分野別フォルダに即再編（案 D の対）**：ユーザーの折れ線的整理には合うが、既存ノート移動と冪等判定の破綻リスクが高い。メタデータ先行で段階導入する。
- **domain を概念タグで代替**：分野と概念が混ざり、将来のフィルタ/フォルダ振り分けに使いづらい。明示メタデータにする。
