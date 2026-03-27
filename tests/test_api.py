from fastapi.testclient import TestClient
from projecao_bus.year_config import reset_year_config, set_active_year_config


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_simulate_retorna_json_basico(client: TestClient) -> None:
    response = client.post("/api/simulate", json={"premissas": {}})
    assert response.status_code == 200
    body = response.json()
    assert "consolidado" in body
    assert "bp" in body
    assert isinstance(body["consolidado"], list)
    assert isinstance(body["bp"], list)


def test_historical_dre_retorna_estrutura(client: TestClient) -> None:
    response = client.get("/api/historical-dre")
    assert response.status_code == 200
    body = response.json()
    assert "consolidado" in body
    assert "dre" in body
    assert "bp" in body
    assert body.get("historical_year_end") == 2025
    assert isinstance(body["consolidado"], list)
    assert len(body["consolidado"]) >= 1


def test_defaults_expoe_inflacao_focus_por_ano_dinamico(client: TestClient) -> None:
    try:
        set_active_year_config(
            historical_year_start=2018,
            historical_year_end=2026,
            projected_years=(2027, 2028, 2029, 2030, 2031),
        )
        response = client.get("/api/defaults")
        assert response.status_code == 200
        body = response.json()
        assert "inflacao_focus_por_ano" in body
        assert "selic_focus_por_ano" in body
        anos = sorted(int(k) for k in body["inflacao_focus_por_ano"].keys())
        anos_selic = sorted(int(k) for k in body["selic_focus_por_ano"].keys())
        assert anos == [2027, 2028, 2029, 2030, 2031]
        assert anos_selic == [2027, 2028, 2029, 2030, 2031]
    finally:
        reset_year_config()


def test_agent_query_retorna_resposta_estruturada(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_ENABLED", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/api/agent/query",
        json={"question": "Mostre uma tabela com EBITDA por BU em todos os anos", "premissas": {}},
    )
    assert response.status_code == 200
    body = response.json()
    assert "answer_markdown" in body
    assert "artifacts" in body
    assert isinstance(body["artifacts"], list)
