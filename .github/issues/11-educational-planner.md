# Issue #11: Educational Planner（教育設計の中核）

Labels: core, planner
Milestone: Phase 2 — Educational Content

## Why
ARCHITECTURE で「システムの心臓」と位置づけられる Educational Planner が未実装（`backend/planner/` は空）。要約ではなく「何を説明し、何を図解し、どの前提知識を仮定するか」を決める層が無いため、イラスト生成も Background/Key Takeaways も方針を持てない。Phase 2 のイラスト系統の起点となる。

## Goal
Knowledge Object から「教育設計（Educational Plan）」を生成する。図解対象・視覚階層・aspect ratio・強調概念を決定し、後段の Illustration / Markdown 双方が同じ設計を入力にできるようにする。

## Tasks
- [ ] `backend/models/educational_plan.py` の既存スキーマを確認し、必要なら Planner 出力に合わせて拡張
- [ ] `backend/planner/` に Educational Planner を実装（KO → EducationalPlan）
- [ ] 図解すべき要素・視覚階層・強調概念を決定するロジック
- [ ] aspect ratio は既定 16:9。理解が向上する場合のみ別比率を選ぶ（Illustration Principles 準拠）
- [ ] LLM を使う場合はプロバイダ抽象越し（`LLMProvider`）。プロンプトは `backend/prompts/` のテンプレートに分離（PROMPT_STYLE_GUIDE 準拠）
- [ ] KO を `ko.educational_plan` に格納する経路（Builder もしくは Pipeline）を定義
- [ ] モック LLM を使った単体テスト（外部API非依存）

## Definition of Done
- Knowledge Object から妥当な Educational Plan が生成される
- aspect ratio の既定が 16:9 で、選択理由が説明可能
- コア層に OpenAI 依存が漏れない（プロバイダ差し替え可能）
- 外部APIに接続せずテストが通る

## Notes
- これ単体では出力は変わらない。後続 #12〜#14 のイラスト系統が本 Plan を消費する。
