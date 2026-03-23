"""
Fluxo de caixa livre (FCFF) e caixa acumulado (payout 50% do LL).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import ANOS_PROJECAO, CAIXA_BASE_2025, PAYOUT_DIVIDENDOS


def montar_fluxo(
    df_consolidado: pd.DataFrame,
    df_ams: pd.DataFrame,
    df_bp: pd.DataFrame,
    df_ncgl: pd.DataFrame,
) -> pd.DataFrame:
    """
    NOPAT = EBIT_consolidado - IR_CSLL_AMS
    FCFF = NOPAT + D&A_Total - CapEx - delta_NCG
    Dividendos = LL_consolidado * 50%
    Caixa(t) = Caixa(t-1) + FCFF - Dividendos
    """
    cons = df_consolidado.set_index("ano")
    ams = df_ams.set_index("ano")
    bp = df_bp.set_index("ano")
    delta = df_ncgl[df_ncgl["ano"].isin(ANOS_PROJECAO)].set_index("ano")["delta_ncg"]

    caixa_ant = CAIXA_BASE_2025
    linhas: list[dict] = []

    for ano in ANOS_PROJECAO:
        ebit = float(cons.at[ano, "ebit"])
        ir_ams = float(ams.at[ano, "irpj_csll"])
        nopat = ebit - ir_ams

        da = float(bp.at[ano, "da_total"])
        capex = float(bp.at[ano, "capex"])
        dncg = float(delta.at[ano])

        fcff = nopat + da - capex - dncg

        ll = float(cons.at[ano, "lucro_liquido"])
        dividendos = ll * PAYOUT_DIVIDENDOS
        caixa = caixa_ant + fcff - dividendos

        linhas.append(
            {
                "ano": ano,
                "ebit": ebit,
                "ir_csll_ams": ir_ams,
                "nopat": nopat,
                "da_total": da,
                "capex": capex,
                "delta_ncg": dncg,
                "fcff": fcff,
                "lucro_liquido": ll,
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
