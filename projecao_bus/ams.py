import math
from typing import Iterable

import numpy as np
import pandas as pd

from fopm import INFLACAO_FOCUS, projetar_dre_fopm_brasil, salvar_projecao_csv


ALIQUOTA_ISV_AMS = 0.123  # 12,30%

# FB AMS 2025 usado como base para a parcela "Base Retida"
FB_AMS_2025 = 15_293_573.83

# Incremental AMS como % do FB FOPM
RATIO_INCREMENTAL_FOPM = 0.0958  # 9,58%

# Ticket médio base (média 2023–2025) e cascata pela inflação
TICKET_AMS_BASE = 18_246.57

# Custo por funcionário base (média 2023–2025) e cascata inflação+1%
CUSTO_FUNC_AMS_BASE = 145_370.0

# Horas por NF (média 2023–2025)
HORAS_POR_NF_AMS = 105.363

# Ratio de D&A por hora (somente 2025)
RATIO_DA_AMS_POR_HORA = 2.6509

# Ratios de despesas em % da RL
RATIO_OUTRAS_DIR_PCT_RL_AMS = 0.01880
RATIO_REM_SOCIOS_PCT_MC1_AMS = 0.11046
RATIO_OUTRAS_ADM_PCT_RL_AMS = 0.01219

# Rateio administrativo AMS - valores já calculados na planilha
RATEIO_ADM_AMS = {
    2026: 2_579_968.0,
    2027: 2_609_915.0,
    2028: 2_660_970.0,
    2029: 2_649_267.0,
    2030: 2_692_591.0,
}

# Honorários ADM Sócios Diretores históricos (para média móvel 4 anos)
HONORARIOS_AMS_HIST = {
    2022: 240_000.0,
    2023: 258_000.0,
    2024: 264_000.0,
    2025: 264_000.0,
}

# Receita / Despesa financeira históricas
RECEITA_FIN_AMS_HIST = {
    2023: 109_000.0,
    2024: 50_000.0,
    2025: 84_000.0,
}

DESPESA_FIN_AMS_CONST = 56_667.0  # média 2023–2025


def _validar_anos(anos: Iterable[int]) -> list[int]:
    anos_list = list(anos)
    if not anos_list:
        raise ValueError("Lista de anos não pode ser vazia.")
    for ano in anos_list:
        if ano not in INFLACAO_FOCUS:
            raise ValueError(f"Ano {ano} não possui premissas cadastradas.")
    return sorted(anos_list)


def projetar_dre_ams(
    df_fopm: pd.DataFrame,
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
    bu: str = "AMS",
    *,
    taxa_conversao_fopm: float | None = None,
    churn: float = 0.0,
) -> pd.DataFrame:
    """
    Projeta a DRE da BU AMS de 2026 a 2030 seguindo o plano de implementação AMS.

    A projeção depende do FB da FOPM já projetado para cada ano, recebido em `df_fopm`.

    taxa_conversao_fopm: fração do FB FOPM que vira receita incremental AMS (default RATIO_INCREMENTAL_FOPM).
    churn: perda anual da base recorrente (0–1). Aplica-se após reajuste da base retida e antes do incremental:
    ``rec_gross = base_ant * fator_reajuste``; ``base_retida = rec_gross * (1 - churn)``;
    ``FB = base_retida + incremental``; estado seguinte ``base_ant = rec_gross``.
    """
    anos_list = _validar_anos(anos)
    ratio_inc = RATIO_INCREMENTAL_FOPM if taxa_conversao_fopm is None else taxa_conversao_fopm

    # Mapa ano → FB FOPM projetado
    fb_fopm_por_ano = (
        df_fopm.set_index("ano")["faturamento_bruto"].to_dict()
        if "ano" in df_fopm.columns and "faturamento_bruto" in df_fopm.columns
        else {}
    )

    resultados: list[dict] = []

    ticket_ant = TICKET_AMS_BASE
    custo_func_ant = CUSTO_FUNC_AMS_BASE

    # Série para média móvel de honorários (4 anos)
    anos_honor_hist = sorted(HONORARIOS_AMS_HIST.keys())
    honor_series = [HONORARIOS_AMS_HIST[a] for a in anos_honor_hist]

    # Série para média móvel da Receita Financeira (4 anos)
    anos_rec_fin_hist = sorted(RECEITA_FIN_AMS_HIST.keys())
    rec_fin_series = [RECEITA_FIN_AMS_HIST[a] for a in anos_rec_fin_hist]

    # A base retida deve evoluir sobre ela mesma. Nao usar o FB total,
    # para nao capitalizar o incremental FOPM no ciclo seguinte.
    base_retida_ant = FB_AMS_2025

    for ano in anos_list:
        if ano not in fb_fopm_por_ano:
            raise ValueError(f"Faturamento Bruto FOPM para {ano} não encontrado em df_fopm.")

        inflacao = INFLACAO_FOCUS[ano]

        # 1) Base retida (bruta pós-reajuste; churn reduz apenas a parcela recorrente do ano)
        fator_reajuste = (1.0 + inflacao) * (1.0 + 0.02)
        rec_gross = base_retida_ant * fator_reajuste
        base_retida = rec_gross * (1.0 - churn)

        # 2) Incremental FOPM
        incremental = fb_fopm_por_ano[ano] * ratio_inc

        # 3) Faturamento Bruto
        faturamento_bruto = base_retida + incremental

        # 4) Ticket Médio (cascata sobre a média histórica)
        ticket_medio = ticket_ant * (1.0 + inflacao)

        # 5) NFs e Horas Totais
        nfs_projetadas = faturamento_bruto / ticket_medio if ticket_medio else math.nan
        horas_por_nf = HORAS_POR_NF_AMS
        horas_totais = nfs_projetadas * horas_por_nf

        # 6) N.º Funcionários (derivado)
        n_funcionarios = horas_totais / (160.0 * 12.0)

        # 7) Impostos sobre Venda
        impostos_sv = faturamento_bruto * ALIQUOTA_ISV_AMS

        # 8) Receita Líquida
        receita_liquida = faturamento_bruto - impostos_sv

        # 10) Incentivos de Prospecção e Vendas — zerados
        incentivos = 0.0

        # 11) Gastos com Pessoal (cascata)
        custo_por_func = custo_func_ant * (1.0 + inflacao + 0.01)
        gastos_pessoal = n_funcionarios * custo_por_func

        # 12) Outras Despesas Diretas
        outras_desp_diretas = receita_liquida * RATIO_OUTRAS_DIR_PCT_RL_AMS

        # 13) Margem Contribuição I
        mc1 = receita_liquida - gastos_pessoal - outras_desp_diretas
        mc1_pct_rl = mc1 / receita_liquida if receita_liquida else math.nan

        # 14) Remuneração Direta dos Sócios
        remuneracao_socios = mc1 * RATIO_REM_SOCIOS_PCT_MC1_AMS

        # 15) Margem Contribuição II
        mc2 = mc1 - remuneracao_socios
        mc2_pct_rl = mc2 / receita_liquida if receita_liquida else math.nan

        # 16) Outras Despesas Administrativas
        outras_desp_adm = receita_liquida * RATIO_OUTRAS_ADM_PCT_RL_AMS

        # 17) Rateio Administrativo
        rateio_adm = RATEIO_ADM_AMS[ano]

        # 18) Honorários ADM Sócios Diretores (média móvel 4 anos)
        honorarios_adm = float(np.mean(honor_series[-4:]))
        honor_series.append(honorarios_adm)

        # 19) EBITDA
        ebitda = mc2 - outras_desp_adm - rateio_adm - honorarios_adm
        ebitda_pct_rl = ebitda / receita_liquida if receita_liquida else math.nan

        # 20) Depreciação / Amortização
        depreciacao_amort = horas_totais * RATIO_DA_AMS_POR_HORA

        # 21) EBIT
        ebit = ebitda - depreciacao_amort

        # 22) Receita Financeira (média móvel 4 anos, começando pela média 2023–2025)
        if len(rec_fin_series) < 4:
            receita_financeira = float(np.mean(rec_fin_series))
        else:
            receita_financeira = float(np.mean(rec_fin_series[-4:]))
        rec_fin_series.append(receita_financeira)

        # 23) Despesa Financeira (constante)
        despesa_financeira = DESPESA_FIN_AMS_CONST

        # 24) LAIR
        lair = ebit + receita_financeira - despesa_financeira

        # 25) IRPJ / CSLL (34% do LAIR)
        irpj_csll = lair * 0.34

        # 26) Lucro Líquido
        lucro_liquido = lair - irpj_csll

        resultados.append(
            {
                "bu": bu,
                "ano": ano,
                "n_funcionarios": n_funcionarios,
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
                "outras_desp_adm": outras_desp_adm,
                "rateio_adm": rateio_adm,
                "honorarios_adm": honorarios_adm,
                "ebitda": ebitda,
                "ebitda_pct_rl": ebitda_pct_rl,
                "depreciacao_amort": depreciacao_amort,
                "ebit": ebit,
                "receita_financeira": receita_financeira,
                "despesa_financeira": despesa_financeira,
                "lair": lair,
                "irpj_csll": irpj_csll,
                "lucro_liquido": lucro_liquido,
            }
        )

        # Próximo ano: ancora na base bruta reajustada (antes do churn), como no modelo sem churn.
        base_retida_ant = rec_gross
        ticket_ant = ticket_medio
        custo_func_ant = custo_por_func

    df = pd.DataFrame(resultados)

    colunas_ordenadas = [
        "bu",
        "ano",
        "n_funcionarios",
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
        "outras_desp_adm",
        "rateio_adm",
        "honorarios_adm",
        "ebitda",
        "ebitda_pct_rl",
        "depreciacao_amort",
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
    anos: Iterable[int] = (2026, 2027, 2028, 2029, 2030),
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

