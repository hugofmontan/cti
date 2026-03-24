from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_simulate_retorna_json_basico(client: TestClient) -> None:
    response = client.post("/api/simulate", json={"premissas": {}})
    assert response.status_code == 200
    body = response.json()
    assert "consolidado" in body
    assert isinstance(body["consolidado"], list)


def test_historical_dre_retorna_estrutura(client: TestClient) -> None:
    response = client.get("/api/historical-dre")
    assert response.status_code == 200
    body = response.json()
    assert "consolidado" in body
    assert "dre" in body
    assert body.get("historical_year_end") == 2025
    assert isinstance(body["consolidado"], list)
    assert len(body["consolidado"]) >= 1
