"""
Projecao DRE Data Science (2026-2030).
"""

import math
from typing import Iterable

import pandas as pd

from .shared import ALIQUOTA_ISV, INFLACAO_FOCUS, _validar_anos, salvar_projecao_csv

N_FUNCIONARIOS_DS = {
    2026: 5,
    2027: 8,
    2028: 10,
    2029: 15,
    2030: 17,
}

TOTAL_PROJETOS_DS = {
    2026: 2,
    2027: 3,
    2028: 4,
    2029: 5,
    2030: 7,
}

HORAS_POR_PROJETO = 3840.0
OCIOSIDADE = 0.15
HORAS_MES = 160.0
MESES_ANO = 12.0

TICKET_BASE_2026 = 1_300_000.0
# Para reproduzir o gabarito do plano, a cascata do ticket usa 1,0397 em todos os anos > 2026.
FATOR_CASCATA_TICKET = 1.0 + INFLACAO_FOCUS[2026]
CUSTO_FUNC_BASE_2026 = 153_654.72

RATIO_INCENTIVOS_PCT_RL = 0.0285
RATIO_OUTRAS_DIR_PCT_RL = 0.0338
RATIO_REM_SOCIOS_PCT_MC1 = 0.1656
RATIO_OUTRAS_ADM_PCT_RL = 0.1277

def projetar_dre_data_science(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "DATA SCIENCE",
    *,
    total_projetos_por_ano: dict[int, int] | None = None,
) -> pd.DataFrame:
    """
    Projeta a DRE da BU Data Science de 2026 a 2030.
    """
    anos_list = _validar_anos(anos)
    resultados: list[dict] = []

    ticket_ant = TICKET_BASE_2026
    custo_func_ant = CUSTO_FUNC_BASE_2026

    for ano in anos_list:
        n_funcionarios = N_FUNCIONARIOS_DS[ano]
        total_projetos = (
            total_projetos_por_ano[ano]
            if total_projetos_por_ano is not None and ano in total_projetos_por_ano
            else TOTAL_PROJETOS_DS[ano]
        )

        horas_alocadas = n_funcionarios * HORAS_MES * MESES_ANO * (1.0 - OCIOSIDADE)
        capacidade_projetos = horas_alocadas / HORAS_POR_PROJETO

        if ano == 2026:
            ticket_medio = ticket_ant
            inflacao_fator_cascata = 0.0
        else:
            ticket_medio = ticket_ant * FATOR_CASCATA_TICKET
            inflacao_fator_cascata = FATOR_CASCATA_TICKET - 1.0

        faturamento_bruto = total_projetos * ticket_medio
        impostos_sv = faturamento_bruto * ALIQUOTA_ISV
        receita_liquida = faturamento_bruto - impostos_sv

        incentivos = receita_liquida * RATIO_INCENTIVOS_PCT_RL

        inflacao_ano = INFLACAO_FOCUS[ano]
        if ano == 2026:
            custo_por_func = custo_func_ant
        else:
            custo_por_func = custo_func_ant * (1.0 + inflacao_ano + 0.01)
        gastos_pessoal = n_funcionarios * custo_por_func

        outras_desp_diretas = receita_liquida * RATIO_OUTRAS_DIR_PCT_RL

        mc1 = receita_liquida - incentivos - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        remuneracao_socios = mc1 * RATIO_REM_SOCIOS_PCT_MC1
        mc2 = mc1 - remuneracao_socios
        mc2_pct_rl = mc2 / receita_liquida if receita_liquida else math.nan

        custo_proprio_adm = receita_liquida * RATIO_OUTRAS_ADM_PCT_RL
        rateio_adm = 0.0
        honorarios_adm = 0.0
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
                "n_funcionarios": n_funcionarios,
                "total_projetos": total_projetos,
                "horas_alocadas": horas_alocadas,
                "capacidade_projetos": capacidade_projetos,
                "inflacao_fator_cascata": inflacao_fator_cascata,
                "ticket_medio": ticket_medio,
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

        ticket_ant = ticket_medio
        custo_func_ant = custo_por_func

    df = pd.DataFrame(resultados)
    colunas_ordenadas = [
        "bu",
        "ano",
        "n_funcionarios",
        "total_projetos",
        "horas_alocadas",
        "capacidade_projetos",
        "inflacao_fator_cascata",
        "ticket_medio",
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


def projetar_e_salvar_data_science(
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "DATA SCIENCE",
):
    """Grava `projecoes/projecao_data_science.csv`."""
    df = projetar_dre_data_science(anos=anos, bu=bu)
    return salvar_projecao_csv(df, nome_arquivo="projecao_data_science.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_data_science()
    print(f"Projecao Data Science salva em: {caminho}")
