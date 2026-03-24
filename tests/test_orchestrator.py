from projecao_bus.orchestrator import run_simulation


def test_run_simulation_retorna_chaves_esperadas() -> None:
    resultado = run_simulation()
    assert {"premissas_efetivas", "dre", "consolidado", "dcf"}.issubset(resultado.keys())
    assert not resultado["consolidado"].empty
