#!/usr/bin/env python3
"""商談準備ブリーフィングと商談後フォローを1本のパイプラインにするCLI。

サブコマンド:
  brief    会社名 / URL / 商談目的 から想定論点・質問リストを生成する
  followup 商談後の自由記述メモから決定事項・ネクストアクション・フォローメール下書きを生成する

どちらも Claude API の構造化出力(tool use を強制する方式)で
Pydantic モデルに直接デシリアライズできる JSON を受け取る。
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pydantic import BaseModel, Field

MODEL = "claude-sonnet-5"


class Briefing(BaseModel):
    company_summary: str = Field(description="会社概要(事業内容・規模感など事実ベースで3〜5文)")
    talking_points: list[str] = Field(description="想定される商談の論点(3〜5個)")
    questions: list[str] = Field(description="先方に投げる質問リスト(3〜5個)")
    risks: list[str] = Field(default_factory=list, description="事前に把握しておくべき懸念点(あれば)")


class FollowupPlan(BaseModel):
    decisions: list[str] = Field(description="商談メモから抽出した決定事項")
    next_actions: list[str] = Field(description="ネクストアクション(担当・期限がメモにあれば含める)")
    followup_email_subject: str = Field(description="フォローメールの件名")
    followup_email_body: str = Field(description="フォローメールの本文(挨拶〜締めまで)")


def _model_to_tool(model: type[BaseModel], name: str, description: str) -> dict[str, Any]:
    schema = model.model_json_schema()
    schema.pop("title", None)
    return {"name": name, "description": description, "input_schema": schema}


def _call_structured(client: Any, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
    """構造化出力を1つの tool_use ブロックとして強制取得する共通処理。"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": user}],
    )
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == tool["name"]:
            return block.input
    raise RuntimeError("tool_use ブロックが返らなかった(モデル or プロンプトを確認)")


def generate_briefing(client: Any, *, company_name: str, url: str, purpose: str = "") -> Briefing:
    tool = _model_to_tool(Briefing, "submit_briefing", "商談前ブリーフィングを提出する")
    user = (
        f"次の商談相手について、Web検索の結果と一般知識をもとにブリーフィングを作成して。\n"
        f"会社名: {company_name}\nURL: {url}\n商談の目的: {purpose or '(未指定)'}\n"
        "事実と推測は分けて書くこと。不明な点は無理に埋めず risks に書く。"
    )
    data = _call_structured(
        client,
        system="あなたはB2B営業の商談準備を支援するアシスタントです。事実ベースで簡潔に書きます。",
        user=user,
        tool=tool,
    )
    return Briefing.model_validate(data)


def extract_followup(client: Any, *, meeting_notes: str) -> FollowupPlan:
    tool = _model_to_tool(FollowupPlan, "submit_followup_plan", "商談後のフォロー計画を提出する")
    user = f"次の商談メモから決定事項とネクストアクションを抽出し、フォローメールの下書きを作って。\n\n---\n{meeting_notes}\n---"
    data = _call_structured(
        client,
        system="あなたはB2B営業のフォローアップを支援するアシスタントです。メモにない情報は書き足しません。",
        user=user,
        tool=tool,
    )
    return FollowupPlan.model_validate(data)


def _build_client():
    import anthropic

    return anthropic.Anthropic()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_brief = sub.add_parser("brief", help="商談前ブリーフィングを生成する")
    p_brief.add_argument("--company", required=True)
    p_brief.add_argument("--url", required=True)
    p_brief.add_argument("--purpose", default="")

    p_followup = sub.add_parser("followup", help="商談後フォローを生成する")
    p_followup.add_argument("--notes-file", required=True, type=argparse.FileType("r", encoding="utf-8"))

    args = parser.parse_args(argv)
    client = _build_client()

    if args.command == "brief":
        result = generate_briefing(client, company_name=args.company, url=args.url, purpose=args.purpose)
    else:
        result = extract_followup(client, meeting_notes=args.notes_file.read())

    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
