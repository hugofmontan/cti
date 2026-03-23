"""
Necessidade de capital de giro (NCG) e variação.
"""

from __future__ import annotations

import math

import pandas as pd

from .constants import AC_OP_2025, ANOS_PROJECAO, NCG_BASE_2025, PC_OP_2025


def montar_ncgl(df_bp: pd.DataFrame) -> pd.DataFrame:
    """
    AC_op = Clientes + Adiantamentos + Impostos_recuperar + Outros_AC
    PC_op = Fornecedores + Obrig_Trab + Obrig_Fiscal + Provisoes
    NCG = AC_op - PC_op
    delta_NCG(t) = NCG(t) - NCG(t-1); base 2025 usa NCG_BASE_2025.
    """
    df = df_bp.set_index("ano")
    linhas: list[dict] = []

    ncg_ant = NCG_BASE_2025

    for ano in ANOS_PROJECAO:
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

    # Metadados 2025 (referência)
    meta = pd.DataFrame(
        [
            {
                "ano": 2025,
                "ac_op": AC_OP_2025,
                "pc_op": PC_OP_2025,
                "ncg": NCG_BASE_2025,
                "delta_ncg": math.nan,
            }
        ]
    )
    return pd.concat([meta, pd.DataFrame(linhas)], ignore_index=True)


def serie_delta_ncgl_projecao(df_ncgl: pd.DataFrame) -> pd.Series:
    """ΔNCG apenas para 2026–2030, indexado por ano."""
    d = df_ncgl[df_ncgl["ano"].isin(ANOS_PROJECAO)].set_index("ano")["delta_ncg"]
    return d.astype(float)
