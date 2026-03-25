"""Smoke golden: perguntas-alvo retornam resposta determinística."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "question",
    [
        "Quais BUs tiveram maior impacto positivo na margem EBITDA consolidada?",
        "Mostre uma tabela com EBITDA por BU em todos os anos",
        "Qual o múltiplo EV/EBITDA implícito no valuation?",
    ],
)
def test_golden_questions_deterministic(client: TestClient, monkeypatch: pytest.MonkeyPatch, question: str) -> None:
    monkeypatch.setenv("AGENT_ENABLED", "true")
    r = client.post("/api/agent/query", json={"question": question, "premissas": {}})
    assert r.status_code == 200
    body = r.json()
    assert body.get("response_source") == "deterministic"
    assert len(body.get("answer_markdown", "")) > 20
