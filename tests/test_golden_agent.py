"""Golden tests for agent v2: tool-based pipeline."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.services.openai_client import OpenAIClient


async def _fake_generate_with_tools(self, question, context, tools, tool_executor, dissertative_mode=False):
    """Simulates the LLM: calls query_data + build_artifact, returns structured answer."""
    query_result = tool_executor("query_data", {
        "source": "current",
        "metrics": ["ebitda"],
        "bus": ["consolidado"],
        "format": "timeseries",
    })

    current = query_result.get("current", {})
    tool_executor("build_artifact", {
        "artifact_type": "line",
        "title": "Evolução EBITDA Consolidado",
        "data": {
            "x": current.get("x", []),
            "series": current.get("series", []),
            "unit": "BRL",
        },
    })

    context["_tools_executed"] = ["query_data", "build_artifact"]
    return {
        "answer_markdown": "EBITDA consolidado cresce ao longo do período projetado.",
        "confidence": "high",
        "data_used": ["consolidado.ebitda"],
        "warnings": [],
    }


async def _fake_generate_kpi(self, question, context, tools, tool_executor, dissertative_mode=False):
    """Simulates the LLM returning a KPI panel."""
    tool_executor("build_artifact", {
        "artifact_type": "kpi_panel",
        "title": "Valuation (DCF)",
        "data": {
            "items": [
                {"label": "Enterprise Value", "value": "150M"},
                {"label": "EV/EBITDA", "value": "8.5x"},
            ],
        },
    })

    context["_tools_executed"] = ["build_artifact"]
    return {
        "answer_markdown": "O EV atual é de R$ 150M, implicando múltiplo EV/EBITDA de 8.5x.",
        "confidence": "high",
        "data_used": ["dcf.enterprise_value"],
        "warnings": [],
    }


def test_golden_chart_question(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr(OpenAIClient, "is_enabled", lambda self: True)
    monkeypatch.setattr(OpenAIClient, "generate_with_tools", _fake_generate_with_tools)

    r = client.post("/api/agent/query", json={"question": "Evolução do EBITDA consolidado", "premissas": {}})
    assert r.status_code == 200
    body = r.json()

    assert body["response_source"] == "openai"
    assert len(body["answer_markdown"]) > 10
    assert any(a.get("type") == "chart" for a in body.get("artifacts", []))


def test_golden_kpi_question(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr(OpenAIClient, "is_enabled", lambda self: True)
    monkeypatch.setattr(OpenAIClient, "generate_with_tools", _fake_generate_kpi)

    r = client.post("/api/agent/query", json={"question": "Qual o EV/EBITDA?", "premissas": {}})
    assert r.status_code == 200
    body = r.json()

    assert body["response_source"] == "openai"
    assert any(a.get("type") == "kpi_panel" for a in body.get("artifacts", []))


def test_llm_unavailable_returns_fallback(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_ENABLED", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    r = client.post("/api/agent/query", json={"question": "Qual o EV/EBITDA?", "premissas": {}})
    assert r.status_code == 200
    body = r.json()
    assert body["response_source"] == "fallback"


def test_llm_error_returns_fallback(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    async def _raise(self, question, context, tools, tool_executor, dissertative_mode=False):
        raise RuntimeError("Simulated OpenAI failure")

    monkeypatch.setattr(OpenAIClient, "is_enabled", lambda self: True)
    monkeypatch.setattr(OpenAIClient, "generate_with_tools", _raise)

    r = client.post("/api/agent/query", json={"question": "Mostre stress test", "premissas": {}})
    assert r.status_code == 200
    body = r.json()
    assert body["response_source"] == "fallback"
    assert len(body.get("warnings", [])) > 0
