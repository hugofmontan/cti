"""
Projecao DRE Data Science.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Iterable

import pandas as pd

from .context import DATA_SCIENCE_OCIOSIDADE_PADRAO, default_simulation_context
from .premissas.data_science_params import DataScienceProjectionParams, default_data_science_projection_params
from .premissas.defaults import default_headcount_ds
from .shared import ALIQUOTA_ISV, salvar_projecao_csv, sort_years_non_empty

if TYPE_CHECKING:
    from .context import SimulationContext

N_FUNCIONARIOS_DS = default_headcount_ds()

OCIOSIDADE = DATA_SCIENCE_OCIOSIDADE_PADRAO

_pd = default_data_science_projection_params()
HORAS_POR_PROJETO = _pd.horas_por_projeto
HORAS_MES = _pd.horas_mes
MESES_ANO = _pd.meses_ano
RATIO_INCENTIVOS_PCT_RL = _pd.ratio_incentivos_pct_rl
RATIO_OUTRAS_DIR_PCT_RL = _pd.ratio_outras_dir_pct_rl
RATIO_REM_SOCIOS_PCT_MC1 = _pd.ratio_rem_socios_pct_mc1
RATIO_OUTRAS_ADM_PCT_RL = _pd.ratio_outras_adm_pct_rl


def total_projetos_de_capacidade(
    n_funcionarios: int,
    ociosidade: float,
    *,
    params: DataScienceProjectionParams | None = None,
) -> int:
    """
    Projetos inteiros cabíveis na equipe, dado HC e ociosidade (mesma base da planilha).
    """
    pr = params if params is not None else default_data_science_projection_params()
    if n_funcionarios <= 0:
        return 0
    oc_eff = min(max(float(ociosidade), 0.0), 0.999)
    horas_alocadas = n_funcionarios * pr.horas_mes * pr.meses_ano * (1.0 - oc_eff)
    cap = horas_alocadas / pr.horas_por_projeto
    return max(0, int(math.floor(cap)))


def projetar_dre_data_science(
    ctx: SimulationContext | None = None,
    anos: Iterable[int] | None = None,
    bu: str = "DATA SCIENCE",
    *,
    headcount_por_ano: dict[int, int] | None = None,
    ociosidade_por_ano: dict[int, float] | None = None,
    params: DataScienceProjectionParams | None = None,
) -> pd.DataFrame:
    pr = params if params is not None else default_data_science_projection_params()
    ctx = ctx if ctx is not None else default_simulation_context()
    anos_list = sort_years_non_empty(anos or ctx.year_config.projected_years)
    resultados: list[dict] = []

    ticket_ant = ctx.data_science_ticket_base
    custo_func_ant = ctx.data_science_custo_func_base
    primeiro_ano_projetado = anos_list[0]
    fator_cascata = ctx.fator_cascata_ticket_data_science()

    for ano in anos_list:
        n_funcionarios = (
            headcount_por_ano[ano]
            if headcount_por_ano is not None and ano in headcount_por_ano
            else ctx.headcount_ds[int(ano)]
        )
        oc = (
            float(ociosidade_por_ano[ano])
            if ociosidade_por_ano is not None and ano in ociosidade_por_ano
            else ctx.data_science_ociosidade_padrao
        )
        oc_eff = min(max(oc, 0.0), 0.999)
        horas_alocadas = n_funcionarios * pr.horas_mes * pr.meses_ano * (1.0 - oc_eff)
        capacidade_projetos = horas_alocadas / pr.horas_por_projeto
        total_projetos = total_projetos_de_capacidade(n_funcionarios, oc, params=pr)

        if ano == primeiro_ano_projetado:
            ticket_medio = ticket_ant
            inflacao_fator_cascata = 0.0
        else:
            ticket_medio = ticket_ant * fator_cascata
            inflacao_fator_cascata = fator_cascata - 1.0

        faturamento_bruto = total_projetos * ticket_medio
        impostos_sv = faturamento_bruto * ALIQUOTA_ISV
        receita_liquida = faturamento_bruto - impostos_sv

        incentivos = receita_liquida * pr.ratio_incentivos_pct_rl

        inflacao_ano = ctx.inflacao_focus[int(ano)]
        if ano == primeiro_ano_projetado:
            custo_por_func = custo_func_ant
        else:
            custo_por_func = custo_func_ant * (1.0 + inflacao_ano + pr.custo_func_grau_livre_adicional)
        gastos_pessoal = n_funcionarios * custo_por_func

        outras_desp_diretas = receita_liquida * pr.ratio_outras_dir_pct_rl

        mc1 = receita_liquida - incentivos - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        remuneracao_socios = mc1 * pr.ratio_rem_socios_pct_mc1
        mc2 = mc1 - remuneracao_socios
        mc2_pct_rl = mc2 / receita_liquida if receita_liquida else math.nan

        custo_proprio_adm = receita_liquida * pr.ratio_outras_adm_pct_rl
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
    anos: Iterable[int] | None = None,
    bu: str = "DATA SCIENCE",
):
    df = projetar_dre_data_science(anos=anos, bu=bu)
    return salvar_projecao_csv(df, nome_arquivo="projecao_data_science.csv")


if __name__ == "__main__":
    caminho = projetar_e_salvar_data_science()
    print(f"Projecao Data Science salva em: {caminho}")
