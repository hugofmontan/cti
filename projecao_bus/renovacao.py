"""
Projeção DRE Renovação (2026–2030) — plano_implementacao_renovacao.md
"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd

from .context import SimulationContext, default_simulation_context
from .premissas.renovacao_params import RenovacaoProjectionParams, default_renovacao_projection_params
from .shared import ALIQUOTA_ISV, salvar_projecao_csv, sort_years_non_empty

_p = default_renovacao_projection_params()
FB_RENOVACAO_2025 = _p.fb_renovacao_2025
CUSTO_FUNC_RENOVACAO_2025 = _p.custo_func_renovacao_2025
N_FUNC_RENOVACAO = _p.n_func_renovacao
SPREAD_REAJUSTE_RENOVACAO = _p.spread_reajuste_default
RATIO_REM_MC1_RENOVACAO = _p.ratio_rem_mc1_renovacao
RATIO_OUTRAS_ADM_PCT_RL_RENOVACAO = _p.ratio_outras_adm_pct_rl_renovacao
HONORARIOS_RENOVACAO_JANELA_INICIAL = list(_p.honorarios_janela_inicial)


def projetar_dre_renovacao(
    ctx: SimulationContext | None = None,
    anos: Iterable[int] | None = None,
    bu: str = "RENOVAÇÃO",
    *,
    spread_real: float | None = None,
    churn: float = 0.0,
    params: RenovacaoProjectionParams | None = None,
) -> pd.DataFrame:
    """
    Fator 1 + inflação + spread real (soma), custo/func com inflação + 1% real,
    honorários em média móvel de 3 anos.

    Churn: taxa anual de perda de receita (0–1). Aplica-se ao FB após o reajuste:
    ``faturamento_bruto = fb_ant * fator_reajuste * (1 - churn)``.
    """
    pr = params if params is not None else default_renovacao_projection_params()
    ctx = ctx if ctx is not None else default_simulation_context()
    anos_list = sort_years_non_empty(anos or ctx.year_config.projected_years)
    resultados: list[dict] = []

    spread = pr.spread_reajuste_default if spread_real is None else spread_real

    base = ctx.base_values
    fb_ant = base.fb_renovacao_base
    custo_func_ant = base.custo_func_renovacao_base
    janela_hon: list[float] = list(pr.honorarios_janela_inicial)

    for ano in anos_list:
        inflacao = ctx.inflacao_focus[int(ano)]
        fator_reajuste = 1.0 + inflacao + spread

        faturamento_bruto = fb_ant * fator_reajuste * (1.0 - churn)
        impostos_sv = faturamento_bruto * ALIQUOTA_ISV
        receita_liquida = faturamento_bruto - impostos_sv

        custo_por_func = custo_func_ant * (1.0 + inflacao + pr.custo_func_grau_livre_adicional)
        gastos_pessoal = pr.n_func_renovacao * custo_por_func

        incentivos = 0.0
        outras_desp_diretas = 0.0

        mc1 = receita_liquida - incentivos - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        remuneracao_socios = mc1 * pr.ratio_rem_mc1_renovacao

        mc2 = mc1 - remuneracao_socios
        mc2_pct_rl = mc2 / receita_liquida if receita_liquida else math.nan

        custo_proprio_adm = receita_liquida * pr.ratio_outras_adm_pct_rl_renovacao
        rateio_adm = 0.0

        honorarios_adm = float(np.mean(janela_hon))
        janela_hon = janela_hon[1:] + [honorarios_adm]
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
                "n_funcionarios": pr.n_func_renovacao,
                "inflacao_focus": inflacao,
                "fator_reajuste": fator_reajuste,
                "spread_real": spread,
                "churn": churn,
                "custo_por_func": custo_por_func,
                "fb_ant": fb_ant,
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
        "fator_reajuste",
        "spread_real",
        "churn",
        "custo_por_func",
        "fb_ant",
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


def projetar_e_salvar_renovacao(
    anos: Iterable[int] | None = None,
    bu: str = "RENOVAÇÃO",
):
    """Grava `projecoes/projecao_renovacao.csv` (mesmo diretório de `fopm.py`)."""
    df = projetar_dre_renovacao(anos=anos, bu=bu)
    return salvar_projecao_csv(df, nome_arquivo="projecao_renovacao.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_renovacao()
    print(f"Projeção Renovação salva em: {caminho}")
