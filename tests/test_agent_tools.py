from projecao_bus.orchestrator import resultado_para_json, run_simulation

from api.services.agent_tools import (
    build_pivot_table,
    get_margin_by_bu_year,
    get_margin_impact_consolidated,
    get_metric_by_bu_year,
    get_valuation_metrics,
)


def _sim_json() -> dict:
    return resultado_para_json(run_simulation(premissas={}))


def test_get_metric_by_bu_year_retorna_pontos() -> None:
    sim = _sim_json()
    rows = get_metric_by_bu_year(sim, metric="ebitda", year=2028)
    assert len(rows) >= 1
    assert rows[0]["metric"] == "ebitda"
    assert rows[0]["year"] == 2028


def test_build_pivot_table_estrutura() -> None:
    sim = _sim_json()
    pivot = build_pivot_table(sim, metric="ebitda", start_year=2026, end_year=2030)
    assert pivot["columns"][0] == "BU"
    assert len(pivot["columns"]) == 6
    assert len(pivot["rows"]) >= 1


def test_get_valuation_metrics_retorna_ev() -> None:
    sim = _sim_json()
    metrics = get_valuation_metrics(sim)
    assert "enterprise_value" in metrics


def test_get_margin_by_bu_year_retorna_itens() -> None:
    sim = _sim_json()
    rows = get_margin_by_bu_year(sim, year=2028)
    assert len(rows) >= 1
    assert "margin" in rows[0]


def test_get_margin_impact_consolidated_retorna_ranking() -> None:
    sim = _sim_json()
    impacts = get_margin_impact_consolidated(sim, start_year=2026, end_year=2030)
    assert len(impacts) >= 1
    assert "impact_pp" in impacts[0]
