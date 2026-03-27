"""
Projecao DRE Venda de Softwares (2026-2030).
"""

from __future__ import annotations

import math
from typing import Iterable

import pandas as pd

from .context import SimulationContext, default_simulation_context
from .premissas.venda_sw_params import VendaSoftwaresProjectionParams, default_venda_softwares_projection_params
from .shared import ALIQUOTA_ISV, salvar_projecao_csv, sort_years_non_empty

_pv = default_venda_softwares_projection_params()
FB_VENDA_SOFTWARES_2025 = _pv.fb_venda_softwares_2025
N_FUNC_VENDA_SOFTWARES = _pv.n_func_venda_softwares
FATOR_CRESCIMENTO_REAL = _pv.fator_crescimento_real
CUSTO_FUNC_2025 = _pv.custo_func_2025
RATIO_INCENTIVOS_PCT_RL = _pv.ratio_incentivos_pct_rl
RATIO_OUTRAS_DIR_PCT_RL = _pv.ratio_outras_dir_pct_rl
HONORARIOS_ADM_FIXO = _pv.honorarios_adm_fixo


def projetar_dre_venda_softwares(
    ctx: SimulationContext | None = None,
    anos: Iterable[int] | None = None,
    bu: str = "VENDA SOFTWARES",
    *,
    fator_crescimento_real: float | None = None,
    params: VendaSoftwaresProjectionParams | None = None,
) -> pd.DataFrame:
    """
    Projeta a DRE da BU Venda de Softwares no horizonte configurado.
    """
    pr = params if params is not None else default_venda_softwares_projection_params()
    ctx = ctx if ctx is not None else default_simulation_context()
    anos_list = sort_years_non_empty(anos or ctx.year_config.projected_years)
    resultados: list[dict] = []

    fcr = pr.fator_crescimento_real if fator_crescimento_real is None else fator_crescimento_real

    base = ctx.base_values
    fb_ant = base.fb_venda_sw_base
    custo_func_ant = base.custo_func_venda_sw_base

    for ano in anos_list:
        inflacao = ctx.inflacao_focus[int(ano)]
        fator_nominal = 1.0 + fcr + inflacao

        faturamento_bruto = fb_ant * fator_nominal
        impostos_sv = faturamento_bruto * ALIQUOTA_ISV
        receita_liquida = faturamento_bruto - impostos_sv

        incentivos = receita_liquida * pr.ratio_incentivos_pct_rl

        custo_por_func = custo_func_ant * (1.0 + inflacao + pr.custo_func_grau_livre_adicional)
        gastos_pessoal = pr.n_func_venda_softwares * custo_por_func

        outras_desp_diretas = receita_liquida * pr.ratio_outras_dir_pct_rl

        mc1 = receita_liquida - incentivos - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        remuneracao_socios = 0.0
        mc2 = mc1
        mc2_pct_rl = mc1_pct_rl

        custo_proprio_adm = 0.0
        rateio_adm = 0.0
        honorarios_adm = pr.honorarios_adm_fixo
        outras_desp_adm = custo_proprio_adm + rateio_adm + honorarios_adm

        ebitda = mc2 - outras_desp_adm
        ebitda_pct_rl = ebitda / receita_liquida if receita_liquida else math.nan

        ebit = ebitda
        lair = ebit
        irpj_csll = 0.0
        lucro_liquido = lair

        resultados.append(
            {
                "bu": bu,
                "ano": ano,
                "n_funcionarios": pr.n_func_venda_softwares,
                "inflacao_focus": inflacao,
                "fator_nominal": fator_nominal,
                "custo_por_func": custo_por_func,
                "faturamento_bruto": faturamento_bruto,
                "impostos_sv": impostos_sv,
                "receita_liquida": receita_liquida,
                "incentivos": incentivos,
                "gastos_pessoal": gastos_pessoal,
                "outras_desp_diretas": outras_desp_diretas,
                "mc1": mc1,
                "mc1_pct_rl": mc1_pct_rl,
                "remuneracao_socios": remuneracao_socios,
                "mc2": mc2,
                "mc2_pct_rl": mc2_pct_rl,
                "custo_proprio_adm": custo_proprio_adm,
                "outras_desp_adm": outras_desp_adm,
                "rateio_adm": rateio_adm,
                "honorarios_adm": honorarios_adm,
                "ebitda": ebitda,
                "ebitda_pct_rl": ebitda_pct_rl,
                "ebit": ebit,
                "lair": lair,
                "irpj_csll": irpj_csll,
                "lucro_liquido": lucro_liquido,
            }
        )

        fb_ant = faturamento_bruto
        custo_func_ant = custo_por_func

    df = pd.DataFrame(resultados)
    colunas_ordenadas = [
        "bu",
        "ano",
        "n_funcionarios",
        "inflacao_focus",
        "fator_nominal",
        "custo_por_func",
        "faturamento_bruto",
        "impostos_sv",
        "receita_liquida",
        "incentivos",
        "gastos_pessoal",
        "outras_desp_diretas",
        "mc1",
        "mc1_pct_rl",
        "remuneracao_socios",
        "mc2",
        "mc2_pct_rl",
        "custo_proprio_adm",
        "outras_desp_adm",
        "rateio_adm",
        "honorarios_adm",
        "ebitda",
        "ebitda_pct_rl",
        "ebit",
        "lair",
        "irpj_csll",
        "lucro_liquido",
    ]
    return df[colunas_ordenadas]


def projetar_e_salvar_venda_softwares(
    anos: Iterable[int] | None = None,
    bu: str = "VENDA SOFTWARES",
):
    """Grava `projecoes/projecao_venda_softwares.csv`."""
    df = projetar_dre_venda_softwares(anos=anos, bu=bu)
    return salvar_projecao_csv(df, nome_arquivo="projecao_venda_softwares.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_venda_softwares()
    print(f"Projecao Venda Softwares salva em: {caminho}")
