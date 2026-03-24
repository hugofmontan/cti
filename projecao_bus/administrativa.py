"""
Projecao DRE Administrativa (2026-2030).
"""

from typing import Iterable

import pandas as pd

from .rateio_administrativo import (
    ANOS_RATEIO_PROJECAO,
    distribuir_rateio_por_headcount,
    load_headcount_funcionarios_bu_csv,
    serie_rateio_pool_negativo,
)
from .shared import INFLACAO_FOCUS, _validar_anos, salvar_projecao_csv

# Drivers fixos conforme plano_implementacao_administrativa.md
RATIO_OUTRAS_ADM_PCT_RL_CONSOLIDADA = 0.12415802928103117
MC2_FIXO = 376_375.08
RATEIO_TOTAL_2025 = 5_047_539.09
HONORARIOS_ADM_FIXO = 1_310_000.0
HONORARIOS_RATEIO_FIXO = -1_222_000.0
N_FUNC_ADM = 0

# Referencias consolidadas da operacao (inclui Data Science).
RL_CONSOLIDADA_REF = {
    2026: 46_939_343.0,
    2027: 51_109_974.0,
    2028: 55_569_432.0,
    2029: 60_162_741.0,
    2030: 67_191_035.0,
}


def _total_func_operacional_ref_from_csv() -> dict[int, float]:
    """Soma de headcounts por ano (2026+) — alinhado a `headcount_funcionarios_bu.csv`."""
    hc = load_headcount_funcionarios_bu_csv()
    out: dict[int, float] = {}
    for _, row in hc.iterrows():
        ano = int(row["ano"])
        if ano < 2026:
            continue
        out[ano] = (
            float(row["func_fopm"])
            + float(row["func_renovacao"])
            + float(row["func_ams"])
            + float(row["func_venda_sw"])
            + float(row["func_data_science"])
        )
    return out


# Usado por `dcf.bp.total_func_operacional_com_2025` quando não há DataFrames em memória.
TOTAL_FUNC_OPERACIONAL_REF = _total_func_operacional_ref_from_csv()


def projetar_dre_administrativa(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "ADMINISTRATIVA",
) -> pd.DataFrame:
    """
    Projeta a DRE da BU Administrativa com base em RL consolidada e rateio inflacionado.
    """
    anos_list = _validar_anos(anos)
    resultados: list[dict] = []

    rateio_total_ant = RATEIO_TOTAL_2025
    hc_tab = load_headcount_funcionarios_bu_csv()
    serie_pool_proj = serie_rateio_pool_negativo(ANOS_RATEIO_PROJECAO)

    for ano in anos_list:
        inflacao = INFLACAO_FOCUS[ano]
        rl_consolidada_ref = RL_CONSOLIDADA_REF[ano]

        outras_desp_adm = rl_consolidada_ref * RATIO_OUTRAS_ADM_PCT_RL_CONSOLIDADA
        rateio_adm_total = -(rateio_total_ant * (1.0 + inflacao))

        row_h = hc_tab[hc_tab["ano"] == ano].iloc[0]
        funcs = {
            "fopm": float(row_h["func_fopm"]),
            "renovacao": float(row_h["func_renovacao"]),
            "ams": float(row_h["func_ams"]),
            "venda_sw": float(row_h["func_venda_sw"]),
            "data_science": float(row_h["func_data_science"]),
        }
        total_func_operacional = sum(funcs.values())
        rp = row_h.get("rateio_pool")
        if pd.isna(rp):
            rateio_neg = serie_pool_proj[ano]
        else:
            rateio_neg = float(rp)
        rdist = distribuir_rateio_por_headcount(rateio_neg, funcs)
        rateio_fopm = rdist["fopm"]
        rateio_renovacao = rdist["renovacao"]
        rateio_ams = rdist["ams"]
        rateio_venda_sw = rdist["venda_sw"]
        rateio_data_science = rdist["data_science"]

        ebitda = (
            MC2_FIXO
            - outras_desp_adm
            - rateio_adm_total
            - HONORARIOS_ADM_FIXO
            - HONORARIOS_RATEIO_FIXO
        )
        ebit = ebitda
        lair = ebit
        lucro_liquido = lair

        resultados.append(
            {
                "bu": bu,
                "ano": ano,
                "mc2": MC2_FIXO,
                "outras_desp_adm": outras_desp_adm,
                "rl_consolidada_ref": rl_consolidada_ref,
                "rateio_adm_total": rateio_adm_total,
                "honorarios_adm": HONORARIOS_ADM_FIXO,
                "honorarios_rateio": HONORARIOS_RATEIO_FIXO,
                "ebitda": ebitda,
                "ebit": ebit,
                "lair": lair,
                "lucro_liquido": lucro_liquido,
                "n_funcionarios_adm": N_FUNC_ADM,
                "rateio_fopm": rateio_fopm,
                "rateio_renovacao": rateio_renovacao,
                "rateio_ams": rateio_ams,
                "rateio_venda_sw": rateio_venda_sw,
                "rateio_data_science": rateio_data_science,
                "total_func_operacional": total_func_operacional,
            }
        )

        rateio_total_ant = abs(rateio_adm_total)

    df = pd.DataFrame(resultados)
    colunas_ordenadas = [
        "bu",
        "ano",
        "mc2",
        "outras_desp_adm",
        "rl_consolidada_ref",
        "rateio_adm_total",
        "honorarios_adm",
        "honorarios_rateio",
        "ebitda",
        "ebit",
        "lair",
        "lucro_liquido",
        "n_funcionarios_adm",
        "rateio_fopm",
        "rateio_renovacao",
        "rateio_ams",
        "rateio_venda_sw",
        "rateio_data_science",
        "total_func_operacional",
    ]
    return df[colunas_ordenadas]


def projetar_e_salvar_administrativa(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "ADMINISTRATIVA",
):
    """Grava `projecoes/projecao_administrativa.csv`."""
    df = projetar_dre_administrativa(anos=anos, bu=bu)
    return salvar_projecao_csv(df, nome_arquivo="projecao_administrativa.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_administrativa()
    print(f"Projecao Administrativa salva em: {caminho}")
