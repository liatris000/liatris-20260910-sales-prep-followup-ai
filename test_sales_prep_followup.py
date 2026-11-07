"""anthropic の API 呼び出しをモックして、スキーマ構築〜パースの経路を検証するテスト。

実 API キーが無い環境でも `python3 -m pytest test_sales_prep_followup.py` で通る。
"""
from __future__ import annotations

from types import SimpleNamespace

from sales_prep_followup import Briefing, FollowupPlan, extract_followup, generate_briefing


class FakeToolUseBlock:
    def __init__(self, name: str, input_: dict):
        self.type = "tool_use"
        self.name = name
        self.input = input_


class FakeMessages:
    def __init__(self, tool_name: str, payload: dict):
        self._tool_name = tool_name
        self._payload = payload
        self.last_kwargs: dict | None = None

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.last_kwargs = kwargs
        return SimpleNamespace(content=[FakeToolUseBlock(self._tool_name, self._payload)])


class FakeClient:
    def __init__(self, tool_name: str, payload: dict):
        self.messages = FakeMessages(tool_name, payload)


def test_generate_briefing_parses_structured_output() -> None:
    payload = {
        "company_summary": "SaaS企業。従業員規模は非公開。",
        "talking_points": ["導入目的", "既存ツールとの棲み分け"],
        "questions": ["決裁フローを教えてください"],
        "risks": ["競合ツールを既に検証済みの可能性"],
    }
    client = FakeClient("submit_briefing", payload)

    result = generate_briefing(client, company_name="Acme Inc.", url="https://example.com", purpose="新規提案")

    assert isinstance(result, Briefing)
    assert result.company_summary == payload["company_summary"]
    assert result.talking_points == payload["talking_points"]
    # tool_choice で強制していることを確認(自由テキスト応答に倒れないため)
    assert client.messages.last_kwargs["tool_choice"] == {"type": "tool", "name": "submit_briefing"}
    assert "Acme Inc." in client.messages.last_kwargs["messages"][0]["content"]


def test_extract_followup_parses_structured_output() -> None:
    payload = {
        "decisions": ["来月の勉強会で正式導入を検討する"],
        "next_actions": ["見積もりを来週送付する"],
        "followup_email_subject": "本日はありがとうございました",
        "followup_email_body": "本日はお時間いただきありがとうございました。次回までに見積もりをお送りします。",
    }
    client = FakeClient("submit_followup_plan", payload)

    result = extract_followup(client, meeting_notes="来月の勉強会で導入検討。見積もりを来週送る約束。")

    assert isinstance(result, FollowupPlan)
    assert result.next_actions == payload["next_actions"]
    assert client.messages.last_kwargs["tool_choice"] == {"type": "tool", "name": "submit_followup_plan"}


def test_briefing_tool_schema_has_required_fields() -> None:
    from sales_prep_followup import _model_to_tool

    tool = _model_to_tool(Briefing, "submit_briefing", "desc")
    props = tool["input_schema"]["properties"]
    assert set(["company_summary", "talking_points", "questions"]).issubset(props.keys())
