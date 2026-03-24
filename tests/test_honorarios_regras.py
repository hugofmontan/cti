from __future__ import annotations

import pytest

from projecao_bus.administrativa import (
    HONORARIOS_ADM_FIXO,
    HONORARIOS_RATEIO_FIXO,
    projetar_dre_administrativa,
)
from projecao_bus.orchestrator import run_simulation


def test_honorarios_bu_regras_batem_gabarito() -> None:
    """
    Regras esperadas:
    - FOPM: cascata inflação Focus a partir de 2025=528.000
    - Renovação: rolling avg 3 anos
    - AMS: rolling avg 4 anos
    - Venda SW: fixo (média histórica 2023-2025)
    - Data Science: zero
    """
    r = run_simulation()
    years = [2026, 2027, 2028, 2029, 2030]

    exp = {
        "fopm": [548_961.6, 569_822.1408, 589_765.915728, 610_407.72277848, 631_771.9930757268],
        "renovacao": [65_500.0, 65_833.33333333333, 65_777.77777777777, 65_703.70370370371, 65_771.60493827161],
        "ams": [256_500.0, 260_625.0, 261_281.25, 260_601.5625, 259_751.953125],
        "venda_sw": [327_500.0, 327_500.0, 327_500.0, 327_500.0, 327_500.0],
        "data_science": [0.0, 0.0, 0.0, 0.0, 0.0],
    }

    for bu, seq in exp.items():
        s = r["dre"][bu].set_index("ano")["honorarios_adm"]
        for i, y in enumerate(years):
            assert float(s.loc[y]) == pytest.approx(seq[i], rel=0.0, abs=1e-6)


def test_honorarios_adm_fixos_na_projecao() -> None:
    df = projetar_dre_administrativa().set_index("ano")
    for ano in [2026, 2027, 2028, 2029, 2030]:
        assert float(df.loc[ano, "honorarios_adm"]) == HONORARIOS_ADM_FIXO
        assert float(df.loc[ano, "honorarios_rateio"]) == HONORARIOS_RATEIO_FIXO
