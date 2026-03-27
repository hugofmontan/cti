"""Regressão do motor: cenário padrão, horizonte variável e concorrência."""

from __future__ import annotations

import threading

import pytest

from projecao_bus.orchestrator import run_simulation
from projecao_bus.year_config import reset_year_config, set_active_year_config

# Golden do cenário padrão (data/original + horizonte 2026–2030). Atualize se o modelo mudar de propósito.
_GOLDEN_EV = 128_464_240.4353634
_GOLDEN_EQ = 130_756_202.4353634
_GOLDEN_SVP = 53_941_768.29888047


def test_golden_cenario_padrao_dcf() -> None:
    r = run_simulation()
    dcf = r["dcf"]["dcf"]
    assert float(dcf["enterprise_value"]) == pytest.approx(_GOLDEN_EV, rel=0, abs=0.02)
    assert float(dcf["equity_value"]) == pytest.approx(_GOLDEN_EQ, rel=0, abs=0.02)
    assert float(dcf["soma_vp_fcffs"]) == pytest.approx(_GOLDEN_SVP, rel=0, abs=0.02)


@pytest.mark.parametrize(
    "n_years,last_year",
    [(3, 2028), (5, 2030), (7, 2032)],
)
def test_horizonte_projecao_variavel(n_years: int, last_year: int) -> None:
    try:
        proj = tuple(range(2026, 2026 + n_years))
        set_active_year_config(2018, 2025, proj)
        r = run_simulation()
        anos = r["consolidado"]["ano"].tolist()
        assert anos == list(proj)
        assert anos[-1] == last_year
        assert len(r["dcf"]["df_fluxo"]) == n_years
    finally:
        reset_year_config()


def test_concorrencia_duas_threads_premissas_distintas() -> None:
    out: dict[str, dict] = {}

    def work(key: str, prem: dict) -> None:
        out[key] = run_simulation(premissas=prem)

    t1 = threading.Thread(target=work, args=("high", {"dcf": {"wacc": 0.22}}))
    t2 = threading.Thread(target=work, args=("low", {"dcf": {"wacc": 0.14}}))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    ev1 = float(out["high"]["dcf"]["dcf"]["enterprise_value"])
    ev2 = float(out["low"]["dcf"]["dcf"]["enterprise_value"])
    assert out["high"]["dcf"]["dcf"]["wacc"] == pytest.approx(0.22)
    assert out["low"]["dcf"]["dcf"]["wacc"] == pytest.approx(0.14)
    # Maior WACC → tipicamente menor EV (verificação fraca mas detecta mistura de estado)
    assert ev1 != ev2
