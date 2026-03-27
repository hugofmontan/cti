from __future__ import annotations

import pytest

from projecao_bus.ams import (
    ANOS_DEPRECIACAO_AMS,
    RATIO_INCREMENTAL_FOPM,
    TAXA_DEPRECIACAO_AMS,
    projetar_dre_ams,
)
from projecao_bus.context import default_simulation_context
from projecao_bus.fopm import projetar_dre_fopm_brasil
from projecao_bus.year_config import get_projected_years


def _df_ams_default():
    ctx = default_simulation_context()
    df_fopm = projetar_dre_fopm_brasil(ctx)
    return projetar_dre_ams(df_fopm=df_fopm, ctx=ctx)


def test_ams_colunas_essenciais_e_anos() -> None:
    df = _df_ams_default()
    assert not df.empty
    assert df["ano"].tolist() == list(get_projected_years())
    assert {
        "incremental_fopm",
        "func_novos_ams",
        "capex_ams",
        "depreciacao_amort",
        "irpj_csll",
        "lair",
    }.issubset(df.columns)


def test_ams_incremental_fopm_respeita_taxa() -> None:
    ctx = default_simulation_context()
    df_fopm = projetar_dre_fopm_brasil(ctx)
    df = projetar_dre_ams(df_fopm=df_fopm, ctx=ctx, taxa_conversao_fopm=RATIO_INCREMENTAL_FOPM)
    fopm = df_fopm.set_index("ano")["faturamento_bruto"]
    for _, row in df.iterrows():
        ano = int(row["ano"])
        esperado = float(fopm.loc[ano]) * RATIO_INCREMENTAL_FOPM
        assert float(row["incremental_fopm"]) == pytest.approx(esperado, rel=0, abs=0.01)


def test_ams_horas_por_nf_cai_1pct_aa() -> None:
    df = _df_ams_default()
    horas = df["horas_por_nf"].tolist()
    for i in range(1, len(horas)):
        assert float(horas[i]) == pytest.approx(float(horas[i - 1]) * 0.99, rel=0, abs=1e-9)


def test_ams_da_por_vintages_consistente_com_capex() -> None:
    df = _df_ams_default().set_index("ano")
    anos = list(get_projected_years())
    capex = {a: float(df.loc[a, "capex_ams"]) for a in anos}

    for ano in anos:
        da_esperada = 0.0
        for ano_vintage in anos:
            if ano_vintage <= ano <= ano_vintage + (ANOS_DEPRECIACAO_AMS - 1):
                da_esperada += capex[ano_vintage] * TAXA_DEPRECIACAO_AMS
        assert float(df.loc[ano, "depreciacao_amort"]) == pytest.approx(da_esperada, rel=0, abs=0.01)


def test_ams_irpj_csll_34pct_do_lair() -> None:
    df = _df_ams_default()
    for _, row in df.iterrows():
        assert float(row["irpj_csll"]) == pytest.approx(float(row["lair"]) * 0.34, rel=0, abs=0.01)
