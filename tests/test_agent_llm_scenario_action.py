"""Agent v2: tests for tool-based scenario execution via the API endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.services.openai_client import OpenAIClient


async def _fake_generate_with_tools_scenario(
    self,
    question,
    context,
    tools,
    tool_executor,
    dissertative_mode=False,
):
    """Simulates the LLM calling run_simulation + compare_scenarios + build_artifact."""
    sim_result = tool_executor("run_simulation", {
        "premissa_changes": {"renovacao.churn": 0.25},
        "label": "churn_25pct",
    })
    scenario_id = sim_result["scenario_id"]
    base_id = context["scenario_id"]

    tool_executor("compare_scenarios", {
        "base_scenario_id": base_id,
        "alt_scenario_id": scenario_id,
        "metrics": ["ebitda", "enterprise_value"],
    })

    tool_executor("build_artifact", {
        "artifact_type": "kpi_panel",
        "title": "Impacto do Churn",
        "data": {
            "items": [
                {"label": "EV base", "value": "150M"},
                {"label": "EV alternativo", "value": "130M", "delta": "-13%"},
            ],
        },
    })

    context["_tools_executed"] = ["run_simulation", "compare_scenarios", "build_artifact"]
    return {
        "answer_markdown": "Com churn de 25%, o EV cai ~13%.",
        "confidence": "high",
        "data_used": ["dcf.enterprise_value"],
        "warnings": [],
    }


def test_agent_executes_scenario_via_tools(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    monkeypatch.setattr(OpenAIClient, "is_enabled", lambda self: True)
    monkeypatch.setattr(OpenAIClient, "generate_with_tools", _fake_generate_with_tools_scenario)

    r = client.post(
        "/api/agent/query",
        json={
            "question": "E se o churn da renovação subir pra 25%?",
            "premissas": {},
            "history": [],
        },
    )
    assert r.status_code == 200
    body = r.json()

    assert body["response_source"] == "openai"
    assert "25%" in body["answer_markdown"] or "churn" in body["answer_markdown"].lower()
    assert len(body["artifacts"]) >= 1
    assert "run_simulation" in body.get("tools_executed", [])


async def _fake_generate_simple(self, question, context, tools, tool_executor, dissertative_mode=False):
    context["_tools_executed"] = []
    return {
        "answer_markdown": "O FCFF é calculado como NOPAT + D&A - CAPEX - ΔNCG.",
        "confidence": "high",
        "data_used": [],
        "warnings": [],
    }


def test_agent_simple_question_no_tools(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    monkeypatch.setattr(OpenAIClient, "is_enabled", lambda self: True)
    monkeypatch.setattr(OpenAIClient, "generate_with_tools", _fake_generate_simple)

    r = client.post(
        "/api/agent/query",
        json={
            "question": "Como é calculado o FCFF?",
            "premissas": {},
            "history": [],
        },
    )
    assert r.status_code == 200
    body = r.json()

    assert body["response_source"] == "openai"
    assert "FCFF" in body["answer_markdown"] or "fcff" in body["answer_markdown"].lower()
    assert len(body.get("artifacts", [])) == 0
    assert body.get("tools_executed", []) == []
