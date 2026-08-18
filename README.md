# sales-prep-followup

商談前ブリーフィングと商談後フォローを、Claude API の構造化出力(tool use を強制する方式)1本のスキーマ設計で作るサンプル実装。

## 何をするか

- `brief`: 会社名 / URL / 商談目的 から、想定論点・質問リスト・懸念点を生成する
- `followup`: 商談後の自由記述メモから、決定事項・ネクストアクション・フォローメール下書きを生成する

## セットアップ

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## 使い方

```bash
# 商談前ブリーフィング
python3 sales_prep_followup.py brief \
  --company "Acme Inc." \
  --url "https://example.com" \
  --purpose "新規提案"

# 商談後フォロー
python3 sales_prep_followup.py followup --notes-file notes.txt
```

## テスト

API キー無しで動く(`anthropic.Anthropic` クライアントをモックして tool_use 応答を差し込む)。

```bash
pip install pytest
python3 -m pytest test_sales_prep_followup.py -v
```

## 設計メモ

商談前・商談後を別スクリプトにせず、1つのファイルに `Briefing` / `FollowupPlan` という2つの Pydantic モデルとして定義し、共通のヘルパー(`_model_to_tool` / `_call_structured`)で tool use の JSON スキーマに変換している。理由や検証過程は記事本文を参照。
