from projecao_bus.orchestrator import run_simulation
from projecao_bus.base_values import reset_base_values
from projecao_bus.year_config import reset_year_config, set_active_year_config


def test_run_simulation_retorna_chaves_esperadas() -> None:
    resultado = run_simulation()
    assert {"premissas_efetivas", "dre", "consolidado", "dcf", "simulation_context"}.issubset(
        resultado.keys()
    )
    assert not resultado["consolidado"].empty


def test_run_simulation_respeita_horizonte_dinamico() -> None:
    try:
        set_active_year_config(
            historical_year_start=2018,
            historical_year_end=2026,
            projected_years=(2027, 2028, 2029, 2030, 2031),
        )
        reset_base_values()
        resultado = run_simulation()
        anos = resultado["consolidado"]["ano"].tolist()
        assert anos == [2027, 2028, 2029, 2030, 2031]
    finally:
        reset_year_config()
        reset_base_values()
