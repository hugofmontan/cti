"""
Necessidade de capital de giro (NCG) e variação.
"""

from __future__ import annotations

import math

import pandas as pd

from ..context import SimulationContext


def montar_ncgl(df_bp: pd.DataFrame, ctx: SimulationContext) -> pd.DataFrame:
    """
    AC_op = Clientes + Adiantamentos + Impostos_recuperar + Outros_AC
    PC_op = Fornecedores + Obrig_Trab + Obrig_Fiscal + Provisoes
    NCG = AC_op - PC_op
    delta_NCG(t) = NCG(t) - NCG(t-1); base usa NCG/base do ano-1.
    """
    df = df_bp.set_index("ano")
    linhas: list[dict] = []

    base = ctx.base_values
    ncg_ant = base.ncg_base

    anos_proj = ctx.year_config.projected_years
    for ano in anos_proj:
        r = df.loc[ano]
        ac_op = (
            float(r["clientes"])
            + float(r["adiantamentos"])
            + float(r["impostos_recuperar"])
            + float(r["outros_ac"])
        )
        pc_op = (
            float(r["fornecedores"])
            + float(r["obrig_trabalhistas"])
            + float(r["obrig_fiscais"])
            + float(r["provisoes"])
        )
        ncg = ac_op - pc_op
        delta = ncg - ncg_ant
        linhas.append(
            {
                "ano": ano,
                "ac_op": ac_op,
                "pc_op": pc_op,
                "ncg": ncg,
                "delta_ncg": delta,
            }
        )
        ncg_ant = ncg

    # Metadados do base_year (referência)
    meta = pd.DataFrame(
        [
            {
                "ano": base.base_year,
                "ac_op": base.ac_op_base,
                "pc_op": base.pc_op_base,
                "ncg": base.ncg_base,
                "delta_ncg": math.nan,
            }
        ]
    )
    return pd.concat([meta, pd.DataFrame(linhas)], ignore_index=True)


def serie_delta_ncgl_projecao(df_ncgl: pd.DataFrame) -> pd.Series:
    """ΔNCG apenas para 2026–2030, indexado por ano."""
    anos_proj = get_projected_years()
    d = df_ncgl[df_ncgl["ano"].isin(anos_proj)].set_index("ano")["delta_ncg"]
    return d.astype(float)
