"""
Balanço patrimonial projetado (BP) — CapEx/D&A em cascata.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Iterable

import pandas as pd

from ..administrativa import total_func_operacional_ref_from_csv
from ..historical_dre import load_historical_dre_bundle
from .constants import (
    ADIANTAMENTOS,
    ANOS_DEPRECIACAO_CAPEX,
    CAPEX_BASE_POR_FUNC_NOVO,
    DIAS_ANO,
    IMPOSTOS_RECUPERAR,
    OUTRAS_OBRIGACOES,
    OUTROS_AC,
    PARTES_RELACIONADAS,
    PMCR_DIAS,
    PMIP_DIAS,
    RATIO_FORNECEDORES,
    RATIO_OBRIG_TRABALHISTAS,
    RATIO_PROVISOES,
    RECEITAS_DIFERIDAS,
    TAXA_DEPRECIACAO_CAPEX,
)

if TYPE_CHECKING:
    from ..context import SimulationContext


def _mean_or_default(values: list[float], default: float) -> float:
    vals = [float(v) for v in values if pd.notna(v)]
    if not vals:
        return float(default)
    return float(sum(vals) / len(vals))


def _bp_premissas_dinamicas(ctx: SimulationContext) -> dict[str, float]:
    """
    Deriva premissas do BP com base no histórico disponível.
    Não depende de um ano fixo hardcoded (ex.: 2025).
    """
    bundle = load_historical_dre_bundle()
    hist_end = int(ctx.year_config.historical_year_end)
    bp_rows = [r for r in bundle.get("bp", []) if int(r.get("ano", 0)) <= hist_end]
    cons_rows = [r for r in bundle.get("consolidado", []) if int(r.get("ano", 0)) <= hist_end]
    bp_by_year = {int(r["ano"]): r for r in bp_rows if "ano" in r}
    cons_by_year = {int(r["ano"]): r for r in cons_rows if "ano" in r}
    years = sorted(set(bp_by_year.keys()) & set(cons_by_year.keys()))

    adiantamentos_s = [float(r.get("adiantamentos", 0.0)) for r in bp_rows if "adiantamentos" in r]
    impostos_rec_s = [float(r.get("impostos_recuperar", 0.0)) for r in bp_rows if "impostos_recuperar" in r]
    outros_ac_s = [float(r.get("outros_ac", 0.0)) for r in bp_rows if "outros_ac" in r]
    outras_obr_s = [float(r.get("outras_obrigacoes", 0.0)) for r in bp_rows if "outras_obrigacoes" in r]
    receitas_diff_s = [float(r.get("receitas_diferidas", 0.0)) for r in bp_rows if "receitas_diferidas" in r]

    ratio_forn_s: list[float] = []
    ratio_obr_trab_s: list[float] = []
    ratio_prov_s: list[float] = []
    for y in years:
        bp = bp_by_year[y]
        c = cons_by_year[y]
        incentivos = float(c.get("incentivos", 0.0))
        outras_desp_diretas = float(c.get("outras_desp_diretas", 0.0))
        outras_desp_adm = float(c.get("outras_desp_adm", 0.0))
        honorarios_adm = float(c.get("honorarios_adm", 0.0))
        rateio_adm = float(c.get("rateio_adm", 0.0))
        gastos_pessoal = float(c.get("gastos_pessoal", 0.0))

        # Fórmula do modelo parceiro para custos/despesas ex-pessoal.
        custos_excl = incentivos + outras_desp_diretas + outras_desp_adm - rateio_adm + honorarios_adm
        # Fórmula do modelo parceiro para custo total de pessoal.
        custo_total_pessoal = gastos_pessoal + rateio_adm

        fornecedores = float(bp.get("fornecedores", 0.0))
        obrig_trab = float(bp.get("obrig_trabalhistas", 0.0))
        provisoes = float(bp.get("provisoes", 0.0))

        if custos_excl > 0:
            ratio_forn_s.append(fornecedores / custos_excl)
        if custo_total_pessoal > 0:
            ratio_obr_trab_s.append(obrig_trab / custo_total_pessoal)
            ratio_prov_s.append(provisoes / custo_total_pessoal)

    return {
        "adiantamentos": _mean_or_default(adiantamentos_s, ADIANTAMENTOS),
        "impostos_recuperar": _mean_or_default(impostos_rec_s, IMPOSTOS_RECUPERAR),
        "outros_ac": _mean_or_default(outros_ac_s, OUTROS_AC),
        "outras_obrigacoes": _mean_or_default(outras_obr_s, OUTRAS_OBRIGACOES),
        "receitas_diferidas": _mean_or_default(receitas_diff_s, RECEITAS_DIFERIDAS),
        "ratio_fornecedores": _mean_or_default(ratio_forn_s, RATIO_FORNECEDORES),
        "ratio_obrig_trabalhistas": _mean_or_default(ratio_obr_trab_s, RATIO_OBRIG_TRABALHISTAS),
        "ratio_provisoes": _mean_or_default(ratio_prov_s, RATIO_PROVISOES),
    }


def total_func_operacional_com_historico(ctx: SimulationContext) -> dict[int, float]:
    """
    Headcount operacional por ano (inclui último ano histórico para cálculo de Δfunc).
    """
    ref = total_func_operacional_ref_from_csv()
    proj = list(ctx.year_config.projected_years)
    hist_end = ctx.year_config.historical_year_end
    proj_start = int(proj[0])
    y_max = max(proj)

    def _ref_at(y: int) -> float:
        if y in ref:
            return float(ref[y])
        le = sorted(k for k in ref if k <= y)
        if le:
            return float(ref[le[-1]])
        return float(ref[max(ref.keys())])

    base_hist = _ref_at(proj_start) - ctx.func_novos_primeiro_ano
    out: dict[int, float] = {hist_end: base_hist}

    for y in range(proj_start, y_max + 1):
        out[y] = _ref_at(y)
    return out


def total_func_operacional_com_2025(ctx: SimulationContext) -> dict[int, float]:
    """Nome legado — usar `total_func_operacional_com_historico`."""
    return total_func_operacional_com_historico(ctx)


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


def _capex_unitario_reajustado_por_ano(ctx: SimulationContext) -> dict[int, float]:
    prod = 1.0
    out: dict[int, float] = {}
    for ano in ctx.year_config.projected_years:
        prod *= 1.0 + ctx.inflacao_focus[int(ano)]
        out[int(ano)] = CAPEX_BASE_POR_FUNC_NOVO * prod
    return out


def _capex_por_ano(func_novos: dict[int, float], ctx: SimulationContext) -> dict[int, float]:
    units = _capex_unitario_reajustado_por_ano(ctx)
    return {a: func_novos[a] * units[a] for a in func_novos}


def _da_total_por_ano(capex_por_ano: dict[int, float], ctx: SimulationContext) -> dict[int, float]:
    da: dict[int, float] = {int(a): 0.0 for a in ctx.year_config.projected_years}
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
    ctx: SimulationContext,
    usar_custos_excl_gabarito: bool = True,
) -> pd.DataFrame:
    df = df_consolidado.set_index("ano")
    anos_proj = ctx.year_config.projected_years
    prem = _bp_premissas_dinamicas(ctx)
    fn = _func_novos(total_func, anos_proj)
    capex = _capex_por_ano(fn, ctx)
    da_total = _da_total_por_ano(capex, ctx)

    base = ctx.base_values
    imob_ant = base.imobilizado_base
    depr_ant = base.depr_acum_base

    linhas: list[dict] = []
    for ano in anos_proj:
        row = df.loc[ano]
        rb = float(row["receita_bruta"])
        impostos_sv = float(row["deducoes"])
        gp_bu = float(row["gastos_pessoal"])
        if "gastos_pessoal_nao_alocado" in row.index:
            pessoal_nao = float(row["gastos_pessoal_nao_alocado"])
        else:
            pessoal_nao = ctx.pessoal_nao_alocado_adm[int(ano)]
        custo_total_pessoal = gp_bu + pessoal_nao

        # Custos/despesas excluindo pessoal no modelo parceiro:
        # linha 12 + linha 23 - linha 24 + linha 37.
        # Mapeamento em DataFrame:
        # incentivos + outras_desp_diretas + outras_desp_adm - rateio_adm + honorarios_adm
        # (quando não houver rateio_adm explícito, assume 0.0).
        if usar_custos_excl_gabarito:
            rateio_adm = float(row["rateio_adm"]) if "rateio_adm" in row.index else 0.0
            custos_excl = (
                float(row["incentivos"])
                + float(row["outras_desp_diretas"])
                + float(row["outras_desp_adm"])
                - rateio_adm
                + float(row["honorarios_adm"])
            )
        else:
            custos_excl = (
                float(row["incentivos"])
                + float(row["outras_desp_diretas"])
                + float(row["outras_desp_adm"])
                + float(row["honorarios_adm"])
            )

        clientes = rb * PMCR_DIAS / DIAS_ANO
        fornecedores = custos_excl * prem["ratio_fornecedores"]
        obrig_trab = custo_total_pessoal * prem["ratio_obrig_trabalhistas"]
        obrig_fiscal = impostos_sv * PMIP_DIAS / DIAS_ANO
        provisoes = custo_total_pessoal * prem["ratio_provisoes"]
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
                "adiantamentos": prem["adiantamentos"],
                "impostos_recuperar": prem["impostos_recuperar"],
                "outros_ac": prem["outros_ac"],
                "partes_relacionadas": PARTES_RELACIONADAS,
                "imobilizado": imobilizado,
                "depr_acumulada": depr_acum,
                "fornecedores": fornecedores,
                "obrig_trabalhistas": obrig_trab,
                "obrig_fiscais": obrig_fiscal,
                "provisoes": provisoes,
                "contas_a_pagar": contas_a_pagar,
                "outras_obrigacoes": prem["outras_obrigacoes"],
                "receitas_diferidas": prem["receitas_diferidas"],
            }
        )

        imob_ant = imobilizado
        depr_ant = depr_acum

    return pd.DataFrame(linhas)


def fechar_balanco_completo(
    df_bp_operacional: pd.DataFrame,
    caixa_por_ano: dict[int, float],
    ctx: SimulationContext,
) -> pd.DataFrame:
    """
    Constrói o BP completo por ano com PL residual (plug em PL).
    """
    df = df_bp_operacional.set_index("ano")
    linhas: list[dict[str, float | int]] = []
    for ano in ctx.year_config.projected_years:
        r = df.loc[ano]
        caixa = float(caixa_por_ano.get(int(ano), 0.0))
        clientes = float(r["clientes"])
        partes_rel = float(r["partes_relacionadas"])
        adiantamentos = float(r["adiantamentos"])
        impostos_rec = float(r["impostos_recuperar"])
        outros_ac = float(r["outros_ac"])
        ativo_circulante_total = caixa + clientes + partes_rel + adiantamentos + impostos_rec + outros_ac

        ativo_fiscal_diferido = 0.0
        imobilizado = float(r["imobilizado"])
        depr_acumulada = float(r["depr_acumulada"])
        ativo_nao_circulante_total = ativo_fiscal_diferido + imobilizado + depr_acumulada
        total_ativo = ativo_circulante_total + ativo_nao_circulante_total

        contas_a_pagar = float(r["contas_a_pagar"])
        fornecedores = float(r["fornecedores"])
        obrig_trabalhistas = float(r["obrig_trabalhistas"])
        obrig_fiscais = float(r["obrig_fiscais"])
        provisoes = float(r["provisoes"])
        outras_obrigacoes = float(r["outras_obrigacoes"])
        passivo_circulante_total = (
            contas_a_pagar
            + obrig_fiscais
            + provisoes
            + outras_obrigacoes
        )

        receitas_diferidas = float(r["receitas_diferidas"])
        passivo_nao_circulante_total = receitas_diferidas
        total_passivo = passivo_circulante_total + passivo_nao_circulante_total

        pl = total_ativo - total_passivo
        total_passivo_pl = total_passivo + pl

        linhas.append(
            {
                "ano": int(ano),
                "caixa": caixa,
                "clientes": clientes,
                "partes_relacionadas": partes_rel,
                "adiantamentos": adiantamentos,
                "impostos_recuperar": impostos_rec,
                "outros_ac": outros_ac,
                "ativo_circulante_total": ativo_circulante_total,
                "ativo_fiscal_diferido": ativo_fiscal_diferido,
                "imobilizado": imobilizado,
                "depr_acumulada": depr_acumulada,
                "ativo_nao_circulante_total": ativo_nao_circulante_total,
                "total_ativo": total_ativo,
                "contas_a_pagar": contas_a_pagar,
                "fornecedores": fornecedores,
                "obrig_trabalhistas": obrig_trabalhistas,
                "obrig_fiscais": obrig_fiscais,
                "provisoes": provisoes,
                "outras_obrigacoes": outras_obrigacoes,
                "passivo_circulante_total": passivo_circulante_total,
                "receitas_diferidas": receitas_diferidas,
                "passivo_nao_circulante_total": passivo_nao_circulante_total,
                "pl": pl,
                "total_passivo_pl": total_passivo_pl,
                "capex": float(r["capex"]),
                "da_total": float(r["da_total"]),
            }
        )
    return pd.DataFrame(linhas)


def carregar_consolidado_csv(base_dir: Path | None = None) -> pd.DataFrame:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    return pd.read_csv(base_dir / "projecoes" / "projecao_consolidado.csv")
