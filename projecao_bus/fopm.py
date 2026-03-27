import math
from pathlib import Path
from typing import Iterable

import pandas as pd

from .context import SimulationContext, default_simulation_context
from .premissas.defaults import default_headcount_fopm, default_ociosidade_fopm
from .shared import ALIQUOTA_ISV, salvar_projecao_csv, sort_years_non_empty

# Compat legada (cópias estáticas — preferir SimulationContext).
HEADCOUNT_PLANEJADO = default_headcount_fopm()
OCIOSIDADE = default_ociosidade_fopm()


def projetar_dre_fopm_brasil(
    ctx: SimulationContext | None = None,
    anos: Iterable[int] | None = None,
    bu: str = "FOPM BRASIL",
    *,
    headcount_por_ano: dict[int, int] | None = None,
    ociosidade_por_ano: dict[int, float] | None = None,
) -> pd.DataFrame:
    """
    Projeta a DRE FOPM Brasil no horizonte configurado.
    """
    ctx = ctx if ctx is not None else default_simulation_context()
    dr = ctx.fopm_drivers
    anos_list = sort_years_non_empty(anos or ctx.year_config.projected_years)

    resultados: list[dict] = []

    ticket_ant = dr.ticket_base_projecao
    custo_func_ant = dr.custo_func_base
    honorarios_ant = dr.honorarios_base

    primeiro_ano_projetado = anos_list[0]

    for ano in anos_list:
        inflacao = ctx.inflacao_focus[int(ano)]
        n_funcionarios = (
            headcount_por_ano[ano]
            if headcount_por_ano is not None and ano in headcount_por_ano
            else ctx.headcount_fopm[int(ano)]
        )
        ociosidade = (
            ociosidade_por_ano[ano]
            if ociosidade_por_ano is not None and ano in ociosidade_por_ano
            else ctx.ociosidade_fopm[int(ano)]
        )

        total_horas = n_funcionarios * 160.0 * 12.0
        horas_alocadas = total_horas * (1.0 - ociosidade)
        horas_por_nf = dr.horas_por_nf
        total_nfs = horas_alocadas / horas_por_nf if horas_por_nf else math.nan

        if ano == primeiro_ano_projetado:
            ticket_medio = ticket_ant
        else:
            ticket_medio = ticket_ant * (1.0 + inflacao)

        faturamento_bruto = total_nfs * ticket_medio
        impostos_sv = faturamento_bruto * ALIQUOTA_ISV
        receita_liquida = faturamento_bruto - impostos_sv

        incentivos = receita_liquida * dr.ratio_incentivos_pct_rl

        custo_por_func = custo_func_ant * (1.0 + inflacao + 0.01)
        gastos_pessoal = n_funcionarios * custo_por_func

        outras_desp_diretas = receita_liquida * dr.ratio_outras_dir_pct_rl

        mc1 = receita_liquida - incentivos - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        remuneracao_socios = mc1 * dr.ratio_rem_socios_pct_mc1

        mc2 = mc1 - remuneracao_socios
        mc2_pct_rl = mc2 / receita_liquida if receita_liquida else math.nan

        custo_proprio_adm = receita_liquida * dr.ratio_outras_adm_pct_rl
        rateio_adm = 0.0

        honorarios_adm = honorarios_ant * (1.0 + inflacao)
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
                "ociosidade": ociosidade,
                "inflacao_focus": inflacao,
                "total_horas": total_horas,
                "horas_alocadas": horas_alocadas,
                "horas_por_nf": horas_por_nf,
                "total_nfs": total_nfs,
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
        honorarios_ant = honorarios_adm

    df = pd.DataFrame(resultados)

    colunas_ordenadas = [
        "bu",
        "ano",
        "n_funcionarios",
        "ociosidade",
        "inflacao_focus",
        "total_horas",
        "horas_alocadas",
        "horas_por_nf",
        "total_nfs",
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

    df = df[colunas_ordenadas]
    return df


def projetar_e_salvar(
    anos: Iterable[int] | None = None,
    bu: str = "FOPM BRASIL",
) -> Path:
    """Atalho para projetar a DRE e salvar diretamente o CSV na pasta `projecoes/`."""
    df = projetar_dre_fopm_brasil(anos=anos, bu=bu)
    return salvar_projecao_csv(df)


if __name__ == "__main__":
    df_projecao = projetar_dre_fopm_brasil()
    caminho = salvar_projecao_csv(df_projecao)
    print(f"Projeção salva em: {caminho}")
