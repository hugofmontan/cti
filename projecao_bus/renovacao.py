"""
Projeção DRE Renovação (2026–2030) — plano_implementacao_renovacao.md
"""

import math
from typing import Iterable

import numpy as np
import pandas as pd

from .shared import ALIQUOTA_ISV, INFLACAO_FOCUS, _validar_anos, salvar_projecao_csv

FB_RENOVACAO_2025 = 3_385_238.39
CUSTO_FUNC_RENOVACAO_2025 = 305_489.82 / 3.0
N_FUNC_RENOVACAO = 3
SPREAD_REAJUSTE_RENOVACAO = 0.02
RATIO_REM_MC1_RENOVACAO = 0.065
RATIO_OUTRAS_ADM_PCT_RL_RENOVACAO = (
    (20_175.45 / 1_712_222.97 + 20_606.90 / 1_991_988.59 + 16_131.42 / 2_777_019.53) / 3.0
)
HONORARIOS_RENOVACAO_JANELA_INICIAL = [64_500.0, 66_000.0, 66_000.0]


def projetar_dre_renovacao(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "RENOVAÇÃO",
    *,
    spread_real: float | None = None,
    churn: float = 0.0,
) -> pd.DataFrame:
    """
    Fator 1 + inflação + spread real (soma), custo/func com inflação + 1% real,
    honorários em média móvel de 3 anos.

    Churn: taxa anual de perda de receita (0–1). Aplica-se ao FB após o reajuste:
    ``faturamento_bruto = fb_ant * fator_reajuste * (1 - churn)``.
    """
    anos_list = _validar_anos(anos)
    resultados: list[dict] = []

    spread = SPREAD_REAJUSTE_RENOVACAO if spread_real is None else spread_real

    fb_ant = FB_RENOVACAO_2025
    custo_func_ant = CUSTO_FUNC_RENOVACAO_2025
    janela_hon: list[float] = list(HONORARIOS_RENOVACAO_JANELA_INICIAL)

    for ano in anos_list:
        inflacao = INFLACAO_FOCUS[ano]
        fator_reajuste = 1.0 + inflacao + spread

        faturamento_bruto = fb_ant * fator_reajuste * (1.0 - churn)
        impostos_sv = faturamento_bruto * ALIQUOTA_ISV
        receita_liquida = faturamento_bruto - impostos_sv

        custo_por_func = custo_func_ant * (1.0 + inflacao + 0.01)
        gastos_pessoal = N_FUNC_RENOVACAO * custo_por_func

        incentivos = 0.0
        outras_desp_diretas = 0.0

        mc1 = receita_liquida - incentivos - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        remuneracao_socios = mc1 * RATIO_REM_MC1_RENOVACAO

        mc2 = mc1 - remuneracao_socios
        mc2_pct_rl = mc2 / receita_liquida if receita_liquida else math.nan

        custo_proprio_adm = receita_liquida * RATIO_OUTRAS_ADM_PCT_RL_RENOVACAO
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
                "n_funcionarios": N_FUNC_RENOVACAO,
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
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "RENOVAÇÃO",
):
    """Grava `projecoes/projecao_renovacao.csv` (mesmo diretório de `fopm.py`)."""
    df = projetar_dre_renovacao(anos=anos, bu=bu)
    return salvar_projecao_csv(df, nome_arquivo="projecao_renovacao.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_renovacao()
    print(f"Projeção Renovação salva em: {caminho}")
