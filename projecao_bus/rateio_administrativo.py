"""
Rateio administrativo (ADM!J39): pool cresce por inflação Focus; distribuição proporcional ao headcount
das BUs operacionais (ADM não entra no denominador).

Base 2025: |ADM!I39| = RATEIO_POOL_ABS_2025. Ver `data/historico/headcount_funcionarios_bu.csv`.
"""

from __future__ import annotations

import math
from typing import Iterable

import pandas as pd

from .context import SimulationContext
from .infrastructure.paths import data_historico_dir
from .shared import sort_years_non_empty
from .year_config import get_historical_year_end, get_projected_years

# Alinhado a `consolidado.CHAVES_BU_OPERACIONAIS` (evita import circular).
CHAVES_BU_OPERACIONAIS = ("fopm", "renovacao", "ams", "venda_sw", "data_science")

RATEIO_POOL_ABS_2025 = 5_047_539.09  # |ADM!I39| — mesmo valor em administrativa.RATEIO_TOTAL_2025


def load_headcount_funcionarios_bu_csv() -> pd.DataFrame:
    """Série 2018–2030: headcounts por BU e pool histórico (rateio_pool negativo, ADM)."""
    path = data_historico_dir() / "headcount_funcionarios_bu.csv"
    return pd.read_csv(path)


def headcount_row_for_ano(hc: pd.DataFrame, ano: int) -> pd.Series:
    """
    Retorna a linha de headcount para `ano`.

    Se o CSV não tiver esse ano (ex.: projeção vai até 2031 mas o arquivo só tem até 2030),
    usa a última linha com ano <= `ano` (carry-forward). Assim o horizonte de projeção
    não fica preso ao último ano presente no CSV.
    """
    if hc.empty or "ano" not in hc.columns:
        raise ValueError("headcount CSV vazio ou sem coluna 'ano'.")
    m = hc["ano"] == int(ano)
    if m.any():
        return hc.loc[m].iloc[0]
    prior = hc[hc["ano"] <= int(ano)]
    if prior.empty:
        prior = hc
    return prior.sort_values("ano").iloc[-1]


def serie_rateio_pool_negativo(ctx: SimulationContext, anos: Iterable[int]) -> dict[int, float]:
    """
    Linha ADM!J39 projetada: Rateio_pool[t] = Rateio_pool[t-1] × (1 + inflação), com sinal negativo.
    """
    anos_l = sort_years_non_empty(anos)
    pool_prev = RATEIO_POOL_ABS_2025
    out: dict[int, float] = {}
    for ano in anos_l:
        infl = ctx.inflacao_focus[int(ano)]
        rateio_neg = -(pool_prev * (1.0 + infl))
        out[ano] = rateio_neg
        pool_prev = abs(rateio_neg)
    return out


def distribuir_rateio_por_headcount(
    rateio_pool_negativo: float,
    func_por_bu: dict[str, float],
) -> dict[str, float]:
    """
    rateio_BU = (func_BU / total_func) * rateio_pool (pool negativo).

    Retorna valores positivos (magnitude de custo nas DREs das BUs), como na planilha.
    """
    total = sum(max(0.0, func_por_bu[k]) for k in CHAVES_BU_OPERACIONAIS)
    if total <= 0:
        raise ValueError("total_func operacional deve ser > 0 para distribuir rateio.")
    pool = float(rateio_pool_negativo)
    out: dict[str, float] = {}
    for k in CHAVES_BU_OPERACIONAIS:
        share = max(0.0, func_por_bu[k]) / total
        # pool negativo × share → negativo; magnitude para subtrair no EBITDA = abs
        out[k] = abs(pool * share)
    return out


def _loc_label_ano(df: pd.DataFrame, ano: int):
    """Índice de linha para o ano (coluna `ano` ou índice = ano)."""
    if "ano" in df.columns:
        m = df["ano"] == ano
        if not m.any():
            raise ValueError(f"Ano {ano} ausente na projeção.")
        return df.index[m][0]
    if ano not in df.index:
        raise ValueError(f"Ano {ano} ausente no índice da projeção.")
    return ano


def _n_func_por_bu_ano(dfs: dict[str, pd.DataFrame], ano: int) -> dict[str, float]:
    out: dict[str, float] = {}
    for k in CHAVES_BU_OPERACIONAIS:
        df = dfs[k]
        lab = _loc_label_ano(df, ano)
        out[k] = float(df.at[lab, "n_funcionarios"])
    return out


def aplicar_rateio_projetado_nas_dres(dfs: dict[str, pd.DataFrame], ctx: SimulationContext) -> None:
    """
    Preenche `rateio_adm` e recalcula EBITDA (e linhas abaixo) no horizonte ativo.
    Espera `dfs` com chaves fopm, renovacao, ams, venda_sw, data_science.
    """
    anos_proj = ctx.year_config.projected_years
    serie_pool = serie_rateio_pool_negativo(ctx, anos_proj)
    for ano in anos_proj:
        rateio_neg = serie_pool[ano]
        funcs = _n_func_por_bu_ano(dfs, ano)
        rateios = distribuir_rateio_por_headcount(rateio_neg, funcs)
        for k in CHAVES_BU_OPERACIONAIS:
            df = dfs[k]
            lab = _loc_label_ano(df, ano)
            df.at[lab, "rateio_adm"] = rateios[k]

        _recalcular_ebitda_apos_rateio(dfs, ano)


def _recalcular_ebitda_apos_rateio(dfs: dict[str, pd.DataFrame], ano: int) -> None:
    for k in CHAVES_BU_OPERACIONAIS:
        df = dfs[k]
        idx = _loc_label_ano(df, ano)
        mc2 = float(df.at[idx, "mc2"])
        custo_proprio = float(df.at[idx, "custo_proprio_adm"]) if "custo_proprio_adm" in df.columns else 0.0
        ra = float(df.at[idx, "rateio_adm"])
        ha = float(df.at[idx, "honorarios_adm"])
        rl = float(df.at[idx, "receita_liquida"])
        outras_desp_adm_total = custo_proprio + ra + ha
        df.at[idx, "outras_desp_adm"] = outras_desp_adm_total
        ebitda = mc2 - outras_desp_adm_total
        df.at[idx, "ebitda"] = ebitda
        df.at[idx, "ebitda_pct_rl"] = ebitda / rl if rl else math.nan

        if k == "ams":
            da = float(df.at[idx, "depreciacao_amort"])
            ebit = ebitda - da
            df.at[idx, "ebit"] = ebit
            rf = float(df.at[idx, "receita_financeira"])
            desp = float(df.at[idx, "despesa_financeira"])
            lair = ebit + rf - desp
            df.at[idx, "lair"] = lair
            irpj = lair * 0.34
            df.at[idx, "irpj_csll"] = irpj
            df.at[idx, "lucro_liquido"] = lair - irpj
        else:
            ebit = ebitda
            df.at[idx, "ebit"] = ebit
            df.at[idx, "lair"] = ebit
            df.at[idx, "irpj_csll"] = 0.0
            df.at[idx, "lucro_liquido"] = ebit


def total_func_operacional_de_dfs(
    dfs: dict[str, pd.DataFrame],
    anos_projecao: Iterable[int],
) -> dict[int, float]:
    """
    Headcount total operacional por ano para BP (inclui último ano histórico para Δfunc).
    ano_historico_final: soma do CSV histórico; projeção: soma dos `n_funcionarios` nas DREs.
    """
    anos_l = sorted(set(anos_projecao))
    hc = load_headcount_funcionarios_bu_csv()
    hist_end = get_historical_year_end()
    row_hist = headcount_row_for_ano(hc, hist_end)
    total_hist = (
        float(row_hist["func_fopm"])
        + float(row_hist["func_renovacao"])
        + float(row_hist["func_ams"])
        + float(row_hist["func_venda_sw"])
        + float(row_hist["func_data_science"])
    )
    projected_start = min(anos_l) if anos_l else hist_end + 1
    out: dict[int, float] = {hist_end: total_hist}
    for ano in anos_l:
        if ano < projected_start:
            continue
        t = 0.0
        for k in CHAVES_BU_OPERACIONAIS:
            df = dfs[k]
            lab = _loc_label_ano(df, ano)
            t += float(df.at[lab, "n_funcionarios"])
        out[ano] = t
    return out
