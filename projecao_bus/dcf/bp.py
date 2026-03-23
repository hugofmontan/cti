"""
Balanço patrimonial projetado (BP) — CapEx/D&A em cascata.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .constants import (
    ADIANTAMENTOS,
    ANOS_DEPRECIACAO_CAPEX,
    ANOS_PROJECAO,
    CAPEX_POR_FUNC_NOVO,
    CUSTOS_EXCL_PESSOAL_GABARITO,
    DEPR_ACUM_BASE_2025,
    DIAS_ANO,
    IMOBILIZADO_BASE_2025,
    IMPOSTOS_RECUPERAR,
    OUTRAS_OBRIGACOES,
    OUTROS_AC,
    PARTES_RELACIONADAS,
    PESSOAL_NAO_ALOCADO_ADM,
    PMCR_DIAS,
    PMIP_DIAS,
    RATIO_FORNECEDORES,
    RATIO_OBRIG_TRABALHISTAS,
    RATIO_PROVISOES,
    RECEITAS_DIFERIDAS,
    TAXA_DEPRECIACAO_CAPEX,
)


def _func_novos(total_func: dict[int, float], anos: Iterable[int]) -> dict[int, float]:
    out: dict[int, float] = {}
    anos_l = sorted(anos)
    for i, ano in enumerate(anos_l):
        if i == 0:
            ant = total_func.get(ano - 1, total_func[ano])
        else:
            ant = total_func[ano - 1]
        out[ano] = max(0.0, total_func[ano] - ant)
    return out


def _capex_por_ano(func_novos: dict[int, float]) -> dict[int, float]:
    return {a: func_novos[a] * CAPEX_POR_FUNC_NOVO for a in func_novos}


def _da_total_por_ano(capex_por_ano: dict[int, float]) -> dict[int, float]:
    """Cada safra de CapEx deprecia 20% a.a. por 5 anos (só anos 2026–2030 no horizonte)."""
    da: dict[int, float] = {a: 0.0 for a in ANOS_PROJECAO}
    for ano_capex, capex in capex_por_ano.items():
        if capex <= 0:
            continue
        for k in range(ANOS_DEPRECIACAO_CAPEX):
            t = ano_capex + k
            if t in da:
                da[t] += capex * TAXA_DEPRECIACAO_CAPEX
    return da


def montar_bp(
    df_consolidado: pd.DataFrame,
    total_func: dict[int, float],
    usar_custos_excl_gabarito: bool = True,
) -> pd.DataFrame:
    """
    df_consolidado: colunas receita_bruta, deducoes, gastos_pessoal, ...
    total_func: headcount operacional por ano (incluir 2025 para Func_Novos em 2026).
    """
    df = df_consolidado.set_index("ano")
    fn = _func_novos(total_func, ANOS_PROJECAO)
    capex = _capex_por_ano(fn)
    da_total = _da_total_por_ano(capex)

    imob_ant = IMOBILIZADO_BASE_2025
    depr_ant = DEPR_ACUM_BASE_2025

    linhas: list[dict] = []
    for ano in ANOS_PROJECAO:
        row = df.loc[ano]
        rb = float(row["receita_bruta"])
        impostos_sv = float(row["deducoes"])
        gp_bu = float(row["gastos_pessoal"])
        pessoal_nao = PESSOAL_NAO_ALOCADO_ADM[ano]
        custo_total_pessoal = gp_bu + pessoal_nao

        if usar_custos_excl_gabarito:
            custos_excl = CUSTOS_EXCL_PESSOAL_GABARITO[ano]
        else:
            custos_excl = (
                float(row["incentivos"])
                + float(row["outras_desp_diretas"])
                + float(row["outras_desp_adm"])
                + float(row["honorarios_adm"])
            )

        clientes = rb * PMCR_DIAS / DIAS_ANO
        fornecedores = custos_excl * RATIO_FORNECEDORES
        obrig_trab = custo_total_pessoal * RATIO_OBRIG_TRABALHISTAS
        obrig_fiscal = impostos_sv * PMIP_DIAS / DIAS_ANO
        provisoes = custo_total_pessoal * RATIO_PROVISOES
        contas_a_pagar = fornecedores + obrig_trab

        capex_ano = capex[ano]
        da_ano = da_total[ano]
        imobilizado = imob_ant + capex_ano
        depr_acum = depr_ant - da_ano

        linhas.append(
            {
                "ano": ano,
                "receita_bruta": rb,
                "total_impostos_sv": impostos_sv,
                "custo_total_pessoal": custo_total_pessoal,
                "custos_excl_pessoal": custos_excl,
                "func_novos": fn[ano],
                "capex": capex_ano,
                "da_total": da_ano,
                "clientes": clientes,
                "adiantamentos": ADIANTAMENTOS,
                "impostos_recuperar": IMPOSTOS_RECUPERAR,
                "outros_ac": OUTROS_AC,
                "partes_relacionadas": PARTES_RELACIONADAS,
                "imobilizado": imobilizado,
                "depr_acumulada": depr_acum,
                "fornecedores": fornecedores,
                "obrig_trabalhistas": obrig_trab,
                "obrig_fiscais": obrig_fiscal,
                "provisoes": provisoes,
                "contas_a_pagar": contas_a_pagar,
                "outras_obrigacoes": OUTRAS_OBRIGACOES,
                "receitas_diferidas": RECEITAS_DIFERIDAS,
            }
        )

        imob_ant = imobilizado
        depr_ant = depr_acum

    return pd.DataFrame(linhas)


def carregar_consolidado_csv(base_dir: Path | None = None) -> pd.DataFrame:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    return pd.read_csv(base_dir / "projecoes" / "projecao_consolidado.csv")
