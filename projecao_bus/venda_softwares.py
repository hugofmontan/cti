"""
Projecao DRE Venda de Softwares (2026-2030).
"""

import math
from typing import Iterable

import pandas as pd

from .shared import ALIQUOTA_ISV, INFLACAO_FOCUS, _validar_anos, salvar_projecao_csv

# Premissas fixas validadas no plano de implementacao.
FB_VENDA_SOFTWARES_2025 = 7_722_610.43
N_FUNC_VENDA_SOFTWARES = 1
FATOR_CRESCIMENTO_REAL = 0.045
CUSTO_FUNC_2025 = 169_393.04
RATIO_INCENTIVOS_PCT_RL = (
    (40_771.81 / 2_645_872.52 + 157_306.64 / 5_002_292.92 + 168_010.36 / 6_353_758.49)
    / 3.0
)
RATIO_OUTRAS_DIR_PCT_RL = 1_172_937.78 / 6_353_758.49
HONORARIOS_ADM_FIXO = (322_500.0 + 330_000.0 + 330_000.0) / 3.0


def projetar_dre_venda_softwares(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "VENDA SOFTWARES",
    *,
    fator_crescimento_real: float | None = None,
) -> pd.DataFrame:
    """
    Projeta a DRE da BU Venda de Softwares de 2026 a 2030.
    """
    anos_list = _validar_anos(anos)
    resultados: list[dict] = []

    fcr = FATOR_CRESCIMENTO_REAL if fator_crescimento_real is None else fator_crescimento_real

    fb_ant = FB_VENDA_SOFTWARES_2025
    custo_func_ant = CUSTO_FUNC_2025

    for ano in anos_list:
        inflacao = INFLACAO_FOCUS[ano]
        fator_nominal = 1.0 + fcr + inflacao

        faturamento_bruto = fb_ant * fator_nominal
        impostos_sv = faturamento_bruto * ALIQUOTA_ISV
        receita_liquida = faturamento_bruto - impostos_sv

        incentivos = receita_liquida * RATIO_INCENTIVOS_PCT_RL

        custo_por_func = custo_func_ant * (1.0 + inflacao + 0.01)
        gastos_pessoal = N_FUNC_VENDA_SOFTWARES * custo_por_func

        outras_desp_diretas = receita_liquida * RATIO_OUTRAS_DIR_PCT_RL

        mc1 = receita_liquida - incentivos - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        remuneracao_socios = 0.0
        mc2 = mc1
        mc2_pct_rl = mc1_pct_rl

        custo_proprio_adm = 0.0
        rateio_adm = 0.0
        honorarios_adm = HONORARIOS_ADM_FIXO
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
                "n_funcionarios": N_FUNC_VENDA_SOFTWARES,
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
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "VENDA SOFTWARES",
):
    """Grava `projecoes/projecao_venda_softwares.csv`."""
    df = projetar_dre_venda_softwares(anos=anos, bu=bu)
    return salvar_projecao_csv(df, nome_arquivo="projecao_venda_softwares.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_venda_softwares()
    print(f"Projecao Venda Softwares salva em: {caminho}")
