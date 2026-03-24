"""
Rateio administrativo (ADM!J39): pool cresce por inflação Focus; distribuição proporcional ao headcount
das BUs operacionais (ADM não entra no denominador).

Base 2025: |ADM!I39| = RATEIO_POOL_ABS_2025. Ver `data/historico/headcount_funcionarios_bu.csv`.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import pandas as pd

from .shared import INFLACAO_FOCUS, _validar_anos

# Alinhado a `consolidado.CHAVES_BU_OPERACIONAIS` (evita import circular).
CHAVES_BU_OPERACIONAIS = ("fopm", "renovacao", "ams", "venda_sw", "data_science")
ANOS_RATEIO_PROJECAO = (2026, 2027, 2028, 2029, 2030)

RATEIO_POOL_ABS_2025 = 5_047_539.09  # |ADM!I39| — mesmo valor em administrativa.RATEIO_TOTAL_2025


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_headcount_funcionarios_bu_csv() -> pd.DataFrame:
    """Série 2018–2030: headcounts por BU e pool histórico (rateio_pool negativo, ADM)."""
    path = _repo_root() / "data" / "historico" / "headcount_funcionarios_bu.csv"
    return pd.read_csv(path)


def serie_rateio_pool_negativo(anos: Iterable[int]) -> dict[int, float]:
    """
    Linha ADM!J39 projetada: Rateio_pool[t] = Rateio_pool[t-1] × (1 + inflação), com sinal negativo.
    """
    anos_l = _validar_anos(anos)
    pool_prev = RATEIO_POOL_ABS_2025
    out: dict[int, float] = {}
    for ano in anos_l:
        infl = INFLACAO_FOCUS[ano]
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


def aplicar_rateio_projetado_nas_dres(dfs: dict[str, pd.DataFrame]) -> None:
    """
    Preenche `rateio_adm` e recalcula EBITDA (e linhas abaixo) para 2026–2030.
    Espera `dfs` com chaves fopm, renovacao, ams, venda_sw, data_science.
    """
    serie_pool = serie_rateio_pool_negativo(ANOS_RATEIO_PROJECAO)
    for ano in ANOS_RATEIO_PROJECAO:
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
    Headcount total operacional por ano para BP (inclui 2025 para Δfunc em 2026).
    2025: soma do CSV histórico; 2026+: soma dos `n_funcionarios` projetados nas DREs.
    """
    anos_l = sorted(set(anos_projecao))
    hc = load_headcount_funcionarios_bu_csv()
    row25 = hc[hc["ano"] == 2025].iloc[0]
    total_2025 = (
        float(row25["func_fopm"])
        + float(row25["func_renovacao"])
        + float(row25["func_ams"])
        + float(row25["func_venda_sw"])
        + float(row25["func_data_science"])
    )
    out: dict[int, float] = {2025: total_2025}
    for ano in anos_l:
        if ano < 2026:
            continue
        t = 0.0
        for k in CHAVES_BU_OPERACIONAIS:
            df = dfs[k]
            lab = _loc_label_ano(df, ano)
            t += float(df.at[lab, "n_funcionarios"])
        out[ano] = t
    return out
