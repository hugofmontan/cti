"""
Projecao DRE Administrativa (2026-2030).
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .rateio_administrativo import (
    distribuir_rateio_por_headcount,
    headcount_row_for_ano,
    load_headcount_funcionarios_bu_csv,
    serie_rateio_pool_negativo,
)
from .year_config import get_projected_year_start
from .context import SimulationContext
from .shared import salvar_projecao_csv, sort_years_non_empty

# Drivers fixos conforme plano_implementacao_administrativa.md
RATIO_OUTRAS_ADM_PCT_RL_CONSOLIDADA = 0.12415802928103117
MC2_FIXO = 376_375.08
RATEIO_TOTAL_2025 = 5_047_539.09
HONORARIOS_ADM_FIXO = 1_310_000.0
HONORARIOS_RATEIO_FIXO = -1_222_000.0
N_FUNC_ADM = 0

def total_func_operacional_ref_from_csv() -> dict[int, float]:
    """Soma de headcounts por ano projetado — alinhado a `headcount_funcionarios_bu.csv`."""
    hc = load_headcount_funcionarios_bu_csv()
    out: dict[int, float] = {}
    pys = get_projected_year_start()
    for _, row in hc.iterrows():
        ano = int(row["ano"])
        if ano < pys:
            continue
        out[ano] = (
            float(row["func_fopm"])
            + float(row["func_renovacao"])
            + float(row["func_ams"])
            + float(row["func_venda_sw"])
            + float(row["func_data_science"])
        )
    return out


def projetar_dre_administrativa(
    ctx: SimulationContext,
    anos: Iterable[int] | None = None,
    bu: str = "ADMINISTRATIVA",
) -> pd.DataFrame:
    """
    Projeta a DRE da BU Administrativa com base em RL consolidada e rateio inflacionado.
    """
    anos_list = sort_years_non_empty(anos or ctx.year_config.projected_years)
    resultados: list[dict] = []

    rateio_total_ant = RATEIO_TOTAL_2025
    hc_tab = load_headcount_funcionarios_bu_csv()
    serie_pool_proj = serie_rateio_pool_negativo(ctx, anos_list)
    rl_ref = ctx.rl_consolidada_ref
    _rl_last_year = max(rl_ref.keys())
    _rl_last_val = rl_ref[_rl_last_year]

    for ano in anos_list:
        inflacao = ctx.inflacao_focus[int(ano)]
        rl_consolidada_ref = rl_ref.get(int(ano), _rl_last_val)


        # A BU Administrativa não tem receita operacional projetada no modelo.
        faturamento_bruto = 0.0
        impostos_sv = 0.0
        receita_liquida = 0.0
        incentivos = 0.0
        gastos_pessoal = 0.0

        outras_desp_adm = rl_consolidada_ref * RATIO_OUTRAS_ADM_PCT_RL_CONSOLIDADA
        rateio_adm_total = -(rateio_total_ant * (1.0 + inflacao))

        row_h = headcount_row_for_ano(hc_tab, ano)
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

        # Na planilha, a Administrativa carrega o "MC2" fixo e uma linha de
        # Outras Despesas Diretas negativa (que faz MC1=MC2).
        outras_desp_diretas = -MC2_FIXO
        mc1 = MC2_FIXO
        remuneracao_socios = 0.0

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
                "faturamento_bruto": faturamento_bruto,
                "impostos_sv": impostos_sv,
                "receita_liquida": receita_liquida,
                "incentivos": incentivos,
                "gastos_pessoal": gastos_pessoal,
                "outras_desp_diretas": outras_desp_diretas,
                "mc1": mc1,
                "remuneracao_socios": remuneracao_socios,
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
        "faturamento_bruto",
        "impostos_sv",
        "receita_liquida",
        "incentivos",
        "gastos_pessoal",
        "outras_desp_diretas",
        "mc1",
        "remuneracao_socios",
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
    ctx: SimulationContext,
    anos: Iterable[int] | None = None,
    bu: str = "ADMINISTRATIVA",
):
    """Grava `projecoes/projecao_administrativa.csv`."""
    df = projetar_dre_administrativa(ctx, anos=anos, bu=bu)
    return salvar_projecao_csv(df, nome_arquivo="projecao_administrativa.csv")


if __name__ == "__main__":
    from .base_values import default_base_values
    from .context import build_simulation_context
    from .year_config import get_active_year_config

    _ctx = build_simulation_context(
        year_config=get_active_year_config(),
        base_values=default_base_values(),
        premissas=None,
    )
    caminho = projetar_e_salvar_administrativa(_ctx)
    print(f"Projecao Administrativa salva em: {caminho}")
