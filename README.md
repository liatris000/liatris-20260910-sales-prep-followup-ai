# sales-prep-followup

商談前ブリーフィングと商談後フォローを、Claude API の構造化出力(tool use を強制する方式)1 本のスキーマ設計で作るサンプル実装。

記事: https://zenn.dev/liatris/articles/20260910-sales-prep-followup-ai

## 何をするか

- `brief`: 会社名 / URL / 商談目的 から、想定論点・質問リスト・懸念点を生成する
- `followup`: 商談後の自由記述メモから、決定事項・ネクストアクション・フォローメール下書きを生成する

## 前提

- Python 3(3.14.6 で確認。これより古い版は試していない)
- `requirements.txt` の依存(`anthropic` / `pydantic` / `pytest`)
- CLI を実際に動かすには Anthropic の API キー。テストはキーなしで動く

## 動かし方

```bash
git clone https://github.com/liatris000/liatris-20260910-sales-prep-followup-ai.git
cd liatris-20260910-sales-prep-followup-ai
pip install -r requirements.txt

# テスト(API キー不要。anthropic.Anthropic をモックして tool_use 応答を差し込む)
python3 -m pytest test_sales_prep_followup.py -v

# CLI(API キーが必要)
export ANTHROPIC_API_KEY=sk-ant-...
python3 sales_prep_followup.py brief \
  --company "Acme Inc." \
  --url "https://example.com" \
  --purpose "新規提案"
python3 sales_prep_followup.py followup --notes-file notes.txt
```

## 期待される出力

テスト:

```text
test_sales_prep_followup.py::test_generate_briefing_parses_structured_output PASSED [ 33%]
test_sales_prep_followup.py::test_extract_followup_parses_structured_output PASSED [ 66%]
test_sales_prep_followup.py::test_briefing_tool_schema_has_required_fields PASSED [100%]
============================== 3 passed ==============================
```

CLI は、`brief` なら想定論点・質問リスト・懸念点を、`followup` なら決定事項・ネクストアクション・フォローメール下書きを返す。

## 確かめていない範囲

- 実際の API キーを使った CLI の実行結果は、リポジトリに置いていない。テストで確かめているのは、tool 定義の組み立てと `tool_use` のパースまで
- 生成されるブリーフィングやメール下書きの質は検証していない
- API キーを設定せずに CLI を実行すると、`anthropic` SDK の認証エラーで止まる(API は呼ばれない)

## 設計メモ

商談前・商談後を別スクリプトにせず、1 つのファイルに `Briefing` / `FollowupPlan` という 2 つの Pydantic モデルとして定義し、共通のヘルパー(`_model_to_tool` / `_call_structured`)で tool use の JSON スキーマに変換している。理由や検証過程は記事本文を参照。

## ライセンス

MIT
