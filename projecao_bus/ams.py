from __future__ import annotations

import math
from typing import TYPE_CHECKING, Iterable

import numpy as np
import pandas as pd

from .context import default_simulation_context
from .fopm import projetar_dre_fopm_brasil
from .premissas.ams_params import AMSProjectionParams, default_ams_projection_params
from .shared import salvar_projecao_csv, sort_years_non_empty

if TYPE_CHECKING:
    from .context import SimulationContext

_default_ams = default_ams_projection_params()

# Reexports estáveis para orchestrator e testes (valores = defaults)
ALIQUOTA_ISV_AMS = _default_ams.aliquota_isv_ams
FB_AMS_2025 = _default_ams.fb_ams_2025
RATIO_INCREMENTAL_FOPM = _default_ams.ratio_incremental_fopm
TICKET_AMS_BASE = _default_ams.ticket_ams_base
CUSTO_FUNC_AMS_BASE = _default_ams.custo_func_ams_base
HORAS_POR_NF_AMS = _default_ams.horas_por_nf_ams
CAPEX_POR_FUNC_NOVO_AMS = _default_ams.capex_por_func_novo_ams
TAXA_DEPRECIACAO_AMS = _default_ams.taxa_depreciacao_ams
ANOS_DEPRECIACAO_AMS = _default_ams.anos_depreciacao_ams
RATIO_OUTRAS_DIR_PCT_RL_AMS = _default_ams.ratio_outras_dir_pct_rl_ams
RATIO_REM_SOCIOS_PCT_MC1_AMS = _default_ams.ratio_rem_socios_pct_mc1_ams
RATIO_OUTRAS_ADM_PCT_RL_AMS = _default_ams.ratio_outras_adm_pct_rl_ams
HONORARIOS_AMS_HIST = _default_ams.honorarios_ams_hist
RECEITA_FIN_AMS_HIST = _default_ams.receita_fin_ams_hist
DESPESA_FIN_AMS_CONST = _default_ams.despesa_fin_ams_const


def projetar_dre_ams(
    df_fopm: pd.DataFrame,
    ctx: SimulationContext | None = None,
    anos: Iterable[int] | None = None,
    bu: str = "AMS",
    *,
    taxa_conversao_fopm: float | None = None,
    churn: float = 0.0,
    params: AMSProjectionParams | None = None,
) -> pd.DataFrame:
    """
    Projeta a DRE da BU AMS no horizonte configurado.

    A projeção depende do FB da FOPM já projetado para cada ano, recebido em `df_fopm`.

    taxa_conversao_fopm: fração do FB FOPM que vira receita incremental AMS (default params.ratio_incremental_fopm).
    churn: perda anual da base recorrente (0–1). Aplica-se após reajuste da base retida e antes do incremental:
    ``rec_gross = FB_AMS(t-1) * fator_reajuste``; ``base_retida = rec_gross * (1 - churn)``;
    ``FB = base_retida + incremental``; estado seguinte ``FB_AMS(t-1) = FB``.
    """
    p = params if params is not None else default_ams_projection_params()
    ctx = ctx if ctx is not None else default_simulation_context()
    anos_list = sort_years_non_empty(anos or ctx.year_config.projected_years)
    ratio_inc = p.ratio_incremental_fopm if taxa_conversao_fopm is None else taxa_conversao_fopm

    # Mapa ano → FB FOPM projetado
    fb_fopm_por_ano = (
        df_fopm.set_index("ano")["faturamento_bruto"].to_dict()
        if "ano" in df_fopm.columns and "faturamento_bruto" in df_fopm.columns
        else {}
    )

    resultados: list[dict] = []

    base = ctx.base_values
    ticket_ant = base.ticket_ams_base
    custo_func_ant = base.custo_func_ams_base

    # Série para média móvel de honorários (4 anos)
    anos_honor_hist = sorted(p.honorarios_ams_hist.keys())
    honor_series = [p.honorarios_ams_hist[a] for a in anos_honor_hist]

    # Série para média móvel da Receita Financeira (4 anos)
    anos_rec_fin_hist = sorted(p.receita_fin_ams_hist.keys())
    rec_fin_series = [p.receita_fin_ams_hist[a] for a in anos_rec_fin_hist]

    fb_ams_ant_total = base.fb_ams_base
    fator_acum_ant = 1.0
    horas_por_nf_ant = base.horas_por_nf_ams
    hc_ano_anterior = (
        (base.fb_ams_base / base.ticket_ams_base) * base.horas_por_nf_ams / (160.0 * 12.0)
        if base.ticket_ams_base
        else 0.0
    )
    fator_capex_infl_acum = 1.0
    da_por_vintage: dict[int, float] = {}

    for ano in anos_list:
        if ano not in fb_fopm_por_ano:
            raise ValueError(f"Faturamento Bruto FOPM para {ano} não encontrado em df_fopm.")

        inflacao = ctx.inflacao_focus[int(ano)]
        spread_real = p.spread_real_base_retida

        fator_marginal = 1.0 + inflacao + spread_real
        fator_acum_atual = fator_acum_ant * fator_marginal
        fator_reajuste = fator_acum_atual / fator_acum_ant
        rec_gross = fb_ams_ant_total * fator_reajuste
        base_retida = rec_gross * (1.0 - churn)

        incremental = fb_fopm_por_ano[ano] * ratio_inc

        faturamento_bruto = base_retida + incremental

        ticket_medio = ticket_ant * (1.0 + inflacao)

        nfs_projetadas = faturamento_bruto / ticket_medio if ticket_medio else math.nan
        horas_por_nf = horas_por_nf_ant * p.horas_por_nf_decay
        horas_totais = nfs_projetadas * horas_por_nf

        n_funcionarios = horas_totais / (160.0 * 12.0)

        impostos_sv = faturamento_bruto * p.aliquota_isv_ams

        receita_liquida = faturamento_bruto - impostos_sv

        incentivos = 0.0

        custo_por_func = custo_func_ant * (1.0 + inflacao + p.custo_func_grau_livre_adicional)
        gastos_pessoal = n_funcionarios * custo_por_func

        outras_desp_diretas = receita_liquida * p.ratio_outras_dir_pct_rl_ams

        mc1 = receita_liquida - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        remuneracao_socios = mc1 * p.ratio_rem_socios_pct_mc1_ams

        mc2 = mc1 - remuneracao_socios
        mc2_pct_rl = mc2 / receita_liquida if receita_liquida else math.nan

        custo_proprio_adm = receita_liquida * p.ratio_outras_adm_pct_rl_ams

        rateio_adm = 0.0

        honorarios_adm = float(np.mean(honor_series[-4:]))
        honor_series.append(honorarios_adm)
        outras_desp_adm = custo_proprio_adm + rateio_adm + honorarios_adm

        ebitda = mc2 - outras_desp_adm
        ebitda_pct_rl = ebitda / receita_liquida if receita_liquida else math.nan

        func_novos_ams = max(0.0, n_funcionarios - hc_ano_anterior)
        fator_capex_infl_acum *= 1.0 + inflacao
        capex_unitario_ams = p.capex_por_func_novo_ams * fator_capex_infl_acum
        capex_ams = func_novos_ams * capex_unitario_ams
        da_por_vintage[ano] = capex_ams * p.taxa_depreciacao_ams
        da_total_ams = 0.0
        for ano_vintage, da_anual in da_por_vintage.items():
            if ano >= ano_vintage and ano <= ano_vintage + (p.anos_depreciacao_ams - 1):
                da_total_ams += da_anual
        depreciacao_amort = da_total_ams

        ebit = ebitda - depreciacao_amort

        if len(rec_fin_series) < 4:
            receita_financeira = float(np.mean(rec_fin_series))
        else:
            receita_financeira = float(np.mean(rec_fin_series[-4:]))
        rec_fin_series.append(receita_financeira)

        despesa_financeira = p.despesa_fin_ams_const

        lair = ebit + receita_financeira - despesa_financeira

        irpj_csll = lair * p.aliquota_ir_csll

        lucro_liquido = lair - irpj_csll

        resultados.append(
            {
                "bu": bu,
                "ano": ano,
                "n_funcionarios": n_funcionarios,
                "func_novos_ams": func_novos_ams,
                "inflacao_focus": inflacao,
                "nfs_projetadas": nfs_projetadas,
                "horas_por_nf": horas_por_nf,
                "horas_totais": horas_totais,
                "ticket_medio": ticket_medio,
                "custo_por_func": custo_por_func,
                "base_retida": base_retida,
                "rec_gross_pos_reajuste": rec_gross,
                "taxa_conversao_fopm": ratio_inc,
                "churn": churn,
                "incremental_fopm": incremental,
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
                "depreciacao_amort": depreciacao_amort,
                "capex_ams": capex_ams,
                "capex_unitario_ams": capex_unitario_ams,
                "fator_capex_infl_acum": fator_capex_infl_acum,
                "ebit": ebit,
                "receita_financeira": receita_financeira,
                "despesa_financeira": despesa_financeira,
                "lair": lair,
                "irpj_csll": irpj_csll,
                "lucro_liquido": lucro_liquido,
            }
        )

        fb_ams_ant_total = faturamento_bruto
        fator_acum_ant = fator_acum_atual
        ticket_ant = ticket_medio
        custo_func_ant = custo_por_func
        horas_por_nf_ant = horas_por_nf
        hc_ano_anterior = n_funcionarios

    df = pd.DataFrame(resultados)

    colunas_ordenadas = [
        "bu",
        "ano",
        "n_funcionarios",
        "func_novos_ams",
        "inflacao_focus",
        "nfs_projetadas",
        "horas_por_nf",
        "horas_totais",
        "ticket_medio",
        "custo_por_func",
        "base_retida",
        "rec_gross_pos_reajuste",
        "taxa_conversao_fopm",
        "churn",
        "incremental_fopm",
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
        "depreciacao_amort",
        "capex_ams",
        "capex_unitario_ams",
        "fator_capex_infl_acum",
        "ebit",
        "receita_financeira",
        "despesa_financeira",
        "lair",
        "irpj_csll",
        "lucro_liquido",
    ]

    df = df[colunas_ordenadas]
    return df


def projetar_e_salvar_ams(
    anos: Iterable[int] | None = None,
    bu: str = "AMS",
):
    """
    Atalho para projetar a DRE AMS (dependendo do FB FOPM projetado)
    e salvar o CSV `projecoes/projecao_ams.csv`.
    """
    df_fopm = projetar_dre_fopm_brasil(anos=anos, bu="FOPM BRASIL")
    df_ams = projetar_dre_ams(df_fopm=df_fopm, anos=anos, bu=bu)
    return salvar_projecao_csv(df_ams, nome_arquivo="projecao_ams.csv")


if __name__ == "__main__":
    df_fopm = projetar_dre_fopm_brasil()
    df_ams = projetar_dre_ams(df_fopm=df_fopm)
    caminho = salvar_projecao_csv(df_ams, nome_arquivo="projecao_ams.csv")
    print(f"Projeção AMS salva em: {caminho}")
