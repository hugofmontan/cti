"""
Fluxo de caixa livre (FCFF) e caixa acumulado (payout 50% do LL).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import MESES_RESERVA_CAIXA
from ..context import SimulationContext


def _irpj_csll_ams_por_ano(df_ams: pd.DataFrame) -> pd.Series:
    """IRPJ/CSLL da DRE AMS (única BU com IR projetado no modelo); base = LAIR AMS × 34%."""
    if "ano" in df_ams.columns:
        return df_ams.set_index("ano")["irpj_csll"]
    return df_ams["irpj_csll"]


def montar_fluxo(
    df_consolidado: pd.DataFrame,
    df_bp: pd.DataFrame,
    df_ncgl: pd.DataFrame,
    df_ams: pd.DataFrame,
    ctx: SimulationContext,
) -> pd.DataFrame:
    """
    NOPAT = EBIT_consolidado − IRPJ/CSLL_AMS (planilha FLUXO!B25; não é 34% sobre EBIT consolidado).
    FCFF = NOPAT + D&A_Consolidada - CapEx - delta_NCG
    Dividendos = LL_consolidado * 50%
    Caixa(t) = Caixa(t-1) + FCFF - Dividendos

    Deve reproduzir o mesmo encadeamento do consolidado (receita fin. usa caixa t-1).
    """
    cons = df_consolidado.set_index("ano")
    bp = df_bp.set_index("ano")
    anos_proj = ctx.year_config.projected_years
    delta = df_ncgl[df_ncgl["ano"].isin(anos_proj)].set_index("ano")["delta_ncg"]
    ir_ams = _irpj_csll_ams_por_ano(df_ams)

    caixa_ant = ctx.base_values.caixa_base
    linhas: list[dict] = []

    for ano in anos_proj:
        ebit = float(cons.at[ano, "ebit"])
        ir_csll_nopat = float(ir_ams.loc[ano])
        # Campo legado na API: valor usado no NOPAT (IR/CSLL AMS), não Ebit × 34%.
        ir_sobre_ebit = ir_csll_nopat
        nopat = ebit - ir_csll_nopat

        if "da_consolidada" in cons.columns:
            da = float(cons.at[ano, "da_consolidada"])
        else:
            da = float(bp.at[ano, "da_total"])
        capex = float(bp.at[ano, "capex"])
        dncg = float(delta.at[ano])

        fcff = nopat + da - capex - dncg

        ll = float(cons.at[ano, "lucro_liquido"])
        # Política do modelo Excel:
        # FLUXO!B20 = (CONSOLIDADO!K11 + CONSOLIDADO!K18) * 4/12
        # K11 = incentivos + gastos_pessoal + outras_desp_diretas
        # K18 = remuneracao_socios + outras_desp_adm + rateio_adm + honorarios_adm + incentivos
        # Observação: incentivos entra duas vezes (K11 e K18), conforme planilha.
        rateio_adm = float(cons.at[ano, "rateio_adm"]) if "rateio_adm" in cons.columns else 0.0
        k11 = (
            float(cons.at[ano, "incentivos"])
            + float(cons.at[ano, "gastos_pessoal"])
            + float(cons.at[ano, "outras_desp_diretas"])
        )
        k18 = (
            float(cons.at[ano, "remuneracao_socios"])
            + float(cons.at[ano, "outras_desp_adm"])
            + rateio_adm
            + float(cons.at[ano, "honorarios_adm"])
            + float(cons.at[ano, "incentivos"])
        )
        custos_despesas_totais = k11 + k18
        caixa_minimo = custos_despesas_totais * (MESES_RESERVA_CAIXA / 12.0)
        caixa_antes_dividendos = caixa_ant + fcff
        dividendos = max(caixa_antes_dividendos - caixa_minimo, 0.0)
        caixa = caixa_antes_dividendos - dividendos

        linhas.append(
            {
                "ano": ano,
                "ebit": ebit,
                "ir_sobre_ebit": ir_sobre_ebit,
                "nopat": nopat,
                "da_total": da,
                "capex": capex,
                "delta_ncg": dncg,
                "fcff": fcff,
                "lucro_liquido": ll,
                "caixa_minimo": caixa_minimo,
                "dividendos": dividendos,
                "caixa_final": caixa,
            }
        )
        caixa_ant = caixa

    return pd.DataFrame(linhas)


def carregar_ams_csv(base_dir: Path | None = None) -> pd.DataFrame:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    return pd.read_csv(base_dir / "projecoes" / "projecao_ams.csv")
