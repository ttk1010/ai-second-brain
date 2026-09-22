# 生成経路の使い分け

ASB には、ノート＋イラストを生成する経路が 4 つあります。中身はどれも同じ `backend/`
パイプライン（Knowledge Object → Markdown＋イラスト）で、違うのは**どこから起動し、どこで
動き、結果をどう受け取るか**です。

## 早見表

| | ① CLI（Mac） | ② Telegram | ③ iOS ショートカット | ④ Claude クラウドセッション |
|---|---|---|---|---|
| 起動する場所 | Mac のターミナル／Claude Code | Telegram の bot | iPhone のショートカット | claude.ai/code・Claude モバイルアプリ |
| 動く場所 | Mac | Mac（Claude Code） | AWS Lambda | GitHub Actions |
| **Mac の起動** | 必要 | 必要（Claude Code を起動しておく） | **不要** | **不要** |
| **会話で擦り合わせ** | できる（Claude Code 上なら） | できる | できない（一発生成） | できる |
| 結果の受け取り | その場で Vault に保存 | bot の返信＋Vault に保存 | **画像がその場で iPhone に表示**＋asb-vault にコミット | asb-vault に push |
| 所要時間の目安 | 約 1 分 | 約 1 分＋会話 | 約 50 秒 | 数分（ランナーの準備を含む） |
| 画像モデル | gpt-image-2（medium） | gpt-image-2（medium） | gpt-image-2.5-flare（high） | gpt-image-2（medium） |
| 使えるオプション | すべて | すべて（Claude が `asb` を実行） | 実質 1 ページ、教育設計は省略 | `guidance` / `pages` / `compare` / `no_image` / `overwrite` |
| 追加の準備 | なし（[クイックスタート](../README.ja.md#クイックスタート)） | Claude Pro＋bot 作成（[TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)） | AWS へのデプロイ（[DEPLOY_SERVERLESS.md](DEPLOY_SERVERLESS.md)） | Actions Secrets の登録（[CLOUD_GENERATION.md](CLOUD_GENERATION.md)） |

費用は経路によらずほぼ同じで、1 ノート約 $0.07〜0.08 です（[README の費用の目安](../README.ja.md#1ノートあたりの費用の目安)）。
ほかに GitHub Actions の実行時間（④）と AWS の無料枠（③）を使いますが、個人利用ならほぼゼロです。

## 使い分けの目安

| こんなとき | おすすめ |
|---|---|
| 家で、じっくり作りたい・複数ページにしたい・既存ノートを手直ししたい | ① CLI |
| 読みためた URL をまとめてノートにしたい | ① CLI の Inbox キュー（`asb-inbox`） |
| Mac は起動しているが、手元にない（外出先から Mac に頼みたい） | ② Telegram |
| 外出先で、思いついた概念や記事をすぐ絵で見たい | ③ iOS ショートカット |
| 外出先で、Mac なしで相談しながら作りたい・複数ページにしたい | ④ Claude クラウドセッション |

迷ったら、**すぐ見たいなら ③、相談したいなら ④（Mac が起動していれば ②）、じっくりなら ①** です。

## 各経路の特徴

### ① CLI（Mac）

- `uv run asb "LLM"` のように Mac で直接実行します。Mac の Claude Code に頼めば、相談しながら生成もできます。
- **すべての機能が使えるのはこの経路だけ**です：複数ページ（`--pages`）、トーンの指示（`--guidance`）、
  比較（`--compare`）、再生成（`--overwrite`）、ログインが必要な記事の持ち込み（`--captured-from`）、
  既存ノートの手直し（`asb-revise`）。
- **Inbox キュー**：Obsidian から `00 Inbox/` に URL や概念のメモを置いておき、`uv run asb-inbox` で
  まとめてノートにできます。スマホで読みためたものを、あとで Mac で一括処理する使い方に向いています。

### ② Telegram（Claude Code Channels）

- Telegram の bot にメッセージを送ると、**Mac の Claude Code** が `asb` を実行して返信します。
- Claude と会話できるので、「この記事を高校生向けに」「3 ページに分けて」などを擦り合わせてから生成できます。
- 処理は Mac で動くため、**Mac と Claude Code のセッションが起動している必要があります**。
- 生成は Mac 上なので、画像モデルや使える機能は ① と同じです。

### ③ iOS ショートカット（AWS Lambda）

- iPhone のショートカットから Lambda を呼び、**Mac が止まっていても**生成できます。画像はその場で
  iPhone に表示され、写真に保存することもできます。
- iOS ショートカットの約 60 秒の制限に収めるため、速度を優先した設定になっています。
  - 画像は `gpt-image-2.5-flare` の `high`（約 25 秒）。手描き調を明示した絵柄指示で、ほかの経路と
    絵柄をそろえています（[ADR 0016](adr/0016-cloud-image-model.md)）。
  - 教育設計（Educational Planner）は省略します。
  - 複数ページにすると 1 ページあたり約 30 秒増えて 60 秒を超え、画像が表示されません
    （サーバー側では生成・保存されます）。複数ページは ① か ④ で。
- 会話はできません。入力を送ったら、それがそのまま生成されます。

### ④ Claude クラウドセッション（GitHub Actions）

- claude.ai/code や Claude モバイルアプリのクラウドセッションから、GitHub Actions のワークフローを起動します。
  GitHub モバイルアプリのフォームから起動することもできます。
- **Mac なしで会話しながら**作れます。時間の制約がゆるいので、複数ページも使えます。
- OpenAI API キーは Actions Secrets の中に留まり、クラウドセッションには渡りません。
- 結果はその場では表示されず、asb-vault に push されます。

## 結果が Obsidian に届くまで

① と ② は、Mac の Vault に直接書き込みます（`auto_commit` / `auto_push` を有効にしていれば asb-vault にも push されます）。

③ と ④ は、asb-vault（GitHub）にコミットされます。Mac で `git pull` すると Vault に取り込まれ、
iCloud 経由で iPhone の Obsidian からも見られるようになります（[MOBILE_OBSIDIAN.md](MOBILE_OBSIDIAN.md)）。
Mac が止まっている間は、Obsidian にはまだ現れません。③ で生成した画像は、その場で iPhone に表示されます。

どの経路も、同じ入力を再度送るとスキップされ、再課金はありません。作り直したいときは `overwrite` を指定します。
