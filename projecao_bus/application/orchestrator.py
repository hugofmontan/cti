"""
Orquestra projeções das BUs em memória e DCF (sem gravar CSVs).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from projecao_bus.administrativa import projetar_dre_administrativa
from projecao_bus.ams import RATIO_INCREMENTAL_FOPM, projetar_dre_ams
from projecao_bus.base_values import BaseValues
from projecao_bus.base_year_extractor import extract_base_year_values
from projecao_bus.config.year_config import YearConfig, get_active_year_config
from projecao_bus.consolidado import projetar_dre_consolidado_de_dfs
from projecao_bus.application.context import SimulationContext, build_simulation_context
from projecao_bus.data_science import projetar_dre_data_science
from projecao_bus.dcf.bp import fechar_balanco_completo
from projecao_bus.dcf.constants import G_PERPETUIDADE, WACC_FIXO
from projecao_bus.dcf.pipeline import run_dcf_pipeline_from_frames
from projecao_bus.fopm import projetar_dre_fopm_brasil
from projecao_bus.infrastructure.historical_dre import load_historical_dre_bundle
from projecao_bus.infrastructure.paths import projecao_bus_package_root
from projecao_bus.rateio_administrativo import aplicar_rateio_projetado_nas_dres
from projecao_bus.renovacao import SPREAD_REAJUSTE_RENOVACAO, projetar_dre_renovacao
from projecao_bus.shared import merge_float_year_dict, merge_int_year_dict
from projecao_bus.venda_softwares import FATOR_CRESCIMENTO_REAL, projetar_dre_venda_softwares


def resolve_base_values(year_config: YearConfig) -> BaseValues:
    """Âncoras de balanço e BUs coerentes com o último ano histórico configurado."""
    bundle = load_historical_dre_bundle()
    return extract_base_year_values(bundle, year_config.historical_year_end)


def _deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and k in out and isinstance(out[k], dict):
            out[k] = _deep_merge(out[k], v)  # type: ignore[assignment]
        else:
            out[k] = v
    return out


def premissas_padrao(ctx: SimulationContext) -> dict[str, Any]:
    """Valores espelhando o estado do contexto (chaves de ano como string para JSON)."""
    anos = list(ctx.projected_years)
    return {
        "inflacao_focus_por_ano": {str(y): float(ctx.inflacao_focus[y]) for y in anos},
        "selic_focus_por_ano": {str(y): float(ctx.selic_focus[y]) for y in anos},
        "fopm": {
            "headcount_por_ano": {str(y): ctx.headcount_fopm[y] for y in anos},
            "ociosidade_por_ano": {str(y): ctx.ociosidade_fopm[y] for y in anos},
        },
        "renovacao": {"spread_real": SPREAD_REAJUSTE_RENOVACAO, "churn": 0.0},
        "ams": {"taxa_conversao_fopm": RATIO_INCREMENTAL_FOPM, "churn": 0.0},
        "venda_softwares": {"fator_crescimento_real": FATOR_CRESCIMENTO_REAL},
        "data_science": {
            "headcount_por_ano": {str(y): ctx.headcount_ds[y] for y in anos},
            "ociosidade_por_ano": {str(y): ctx.data_science_ociosidade_padrao for y in anos},
        },
        "dcf": {
            "wacc": WACC_FIXO,
            "g": G_PERPETUIDADE,
            "func_novos_primeiro_ano": ctx.func_novos_primeiro_ano,
        },
    }


def run_simulation(
    premissas: dict[str, Any] | None = None,
    base_dir: Path | None = None,
    *,
    year_config: YearConfig | None = None,
    base_values: BaseValues | None = None,
) -> dict[str, Any]:
    """
    Executa FOPM → Renovação → AMS → Venda SW → Data Science → Consolidado → DCF.

    `year_config` e `base_values` opcionais evitam depender apenas do estado global
    quando fornecidos explicitamente (ex.: testes de concorrência).
    """
    if base_dir is None:
        base_dir = projecao_bus_package_root()

    yc = year_config if year_config is not None else get_active_year_config()
    bv = base_values if base_values is not None else resolve_base_values(yc)

    ctx = build_simulation_context(year_config=yc, base_values=bv, premissas=premissas)
    p = _deep_merge(premissas_padrao(ctx), premissas or {})

    ANOS = list(ctx.projected_years)

    fc = p["fopm"]
    headcount_por_ano = merge_int_year_dict(
        {y: ctx.headcount_fopm[y] for y in ANOS},
        fc.get("headcount_por_ano"),
    )
    ociosidade_por_ano = merge_float_year_dict(
        {y: ctx.ociosidade_fopm[y] for y in ANOS},
        fc.get("ociosidade_por_ano"),
    )

    df_fopm = projetar_dre_fopm_brasil(
        ctx,
        anos=ANOS,
        headcount_por_ano=headcount_por_ano,
        ociosidade_por_ano=ociosidade_por_ano,
    )

    ren = p["renovacao"]
    spread = ren.get("spread_real")
    if spread is not None:
        spread = float(spread)
    df_renov = projetar_dre_renovacao(
        ctx,
        anos=ANOS,
        spread_real=spread,
        churn=float(ren.get("churn", 0.0)),
    )

    ams_p = p["ams"]
    tc = ams_p.get("taxa_conversao_fopm")
    if tc is not None:
        tc = float(tc)
    df_ams = projetar_dre_ams(
        df_fopm,
        ctx,
        anos=ANOS,
        taxa_conversao_fopm=tc,
        churn=float(ams_p.get("churn", 0.0)),
    )

    vs = p["venda_softwares"]
    fcr = vs.get("fator_crescimento_real")
    if fcr is not None:
        fcr = float(fcr)
    df_vsw = projetar_dre_venda_softwares(ctx, anos=ANOS, fator_crescimento_real=fcr)

    ds = p["data_science"]
    hc_ds_def = {y: ctx.headcount_ds[y] for y in ANOS}
    oc_ds_def = {y: ctx.data_science_ociosidade_padrao for y in ANOS}
    headcount_ds = merge_int_year_dict(hc_ds_def, ds.get("headcount_por_ano"))
    headcount_ds = {k: int(v) for k, v in headcount_ds.items()}
    ociosidade_ds = merge_float_year_dict(oc_ds_def, ds.get("ociosidade_por_ano"))
    ociosidade_ds = {k: float(v) for k, v in ociosidade_ds.items()}
    df_ds = projetar_dre_data_science(
        ctx,
        anos=ANOS,
        headcount_por_ano=headcount_ds,
        ociosidade_por_ano=ociosidade_ds,
    )

    df_adm = projetar_dre_administrativa(ctx, anos=ANOS)

    dfs = {
        "fopm": df_fopm,
        "renovacao": df_renov,
        "ams": df_ams,
        "venda_sw": df_vsw,
        "data_science": df_ds,
        "administrativa": df_adm,
    }

    aplicar_rateio_projetado_nas_dres(dfs, ctx)

    df_cons = projetar_dre_consolidado_de_dfs(dfs, ctx, anos=ANOS)

    dcf_p = p["dcf"]
    wacc = dcf_p.get("wacc")
    g = dcf_p.get("g")
    if wacc is not None:
        wacc = float(wacc)
    if g is not None:
        g = float(g)

    dcf_bundle = run_dcf_pipeline_from_frames(
        df_cons,
        df_ams,
        dfs_bu={k: dfs[k] for k in ("fopm", "renovacao", "ams", "venda_sw", "data_science")},
        ctx=ctx,
        wacc=wacc,
        g=g,
        base_dir=base_dir,
        salvar_csv=False,
    )
    caixa_por_ano = {int(r["ano"]): float(r["caixa"]) for _, r in df_cons.iterrows()}
    df_bp_completo = fechar_balanco_completo(dcf_bundle["df_bp"], caixa_por_ano, ctx)
    dcf_bundle["df_bp_completo"] = df_bp_completo
    bp_historico = load_historical_dre_bundle().get("bp", [])

    return {
        "premissas_efetivas": p,
        "dre": dfs,
        "consolidado": df_cons,
        "dcf": dcf_bundle,
        "bp_historico": bp_historico,
        "simulation_context": ctx,
    }


def resultado_para_json(resultado: dict[str, Any]) -> dict[str, Any]:
    """Converte DataFrames em listas de dicts para resposta JSON."""

    def df_to_records(df: pd.DataFrame) -> list[dict]:
        import numpy as np

        return df.replace({np.nan: None}).to_dict(orient="records")

    ctx: SimulationContext = resultado["simulation_context"]
    out: dict[str, Any] = {
        "premissas_efetivas": resultado["premissas_efetivas"],
        "dre": {k: df_to_records(v) for k, v in resultado["dre"].items()},
        "consolidado": df_to_records(resultado["consolidado"]),
        "bp": df_to_records(resultado["dcf"]["df_bp_completo"]),
        "bp_historico": resultado.get("bp_historico", []),
        "fluxo": df_to_records(resultado["dcf"]["df_fluxo"]),
        "dcf": {
            "wacc": float(resultado["dcf"]["dcf"]["wacc"]),
            "g": float(resultado["dcf"]["dcf"]["g"]),
            "enterprise_value": float(resultado["dcf"]["dcf"]["enterprise_value"]),
            "equity_value": float(resultado["dcf"]["dcf"]["equity_value"]),
            "soma_vp_fcffs": float(resultado["dcf"]["dcf"]["soma_vp_fcffs"]),
            "vp_fcff_por_ano": {
                str(k): float(v) for k, v in resultado["dcf"]["dcf"]["vp_fcff_por_ano"].items()
            },
            "multiplos": {
                k: float(v) for k, v in resultado["dcf"]["dcf"]["multiplos"].items()
            },
        },
        "warnings": _warnings(resultado),
    }

    sens_df = resultado.get("dcf", {}).get("matriz_sensibilidade")
    if isinstance(sens_df, pd.DataFrame):
        sens_filled = sens_df.fillna(0.0)
        row_values = [float(v) for v in sens_filled.index]
        col_values = [float(v) for v in sens_filled.columns]
        matrix = [[float(x) for x in row] for row in sens_filled.to_numpy()]
        out["dcf"]["sensitivity_matrix"] = {
            "row_param": "wacc",
            "col_param": "g",
            "row_values": row_values,
            "col_values": col_values,
            "matrix": matrix,
        }
    else:
        out["dcf"]["sensitivity_matrix"] = None

    yc = ctx.year_config
    out["year_config"] = {
        "historical_year_start": yc.historical_year_start,
        "historical_year_end": yc.historical_year_end,
        "projected_year_start": yc.projected_years[0],
        "projected_years": list(yc.projected_years),
    }
    return out


def _warnings(resultado: dict[str, Any]) -> list[str]:
    w: list[str] = []
    ren = resultado["premissas_efetivas"].get("renovacao", {})
    ams = resultado["premissas_efetivas"].get("ams", {})
    if float(ren.get("churn", 0)) > 0.5:
        w.append("Churn Renovação acima de 50% pode distorcer o modelo.")
    if float(ams.get("churn", 0)) > 0.5:
        w.append("Churn AMS acima de 50% pode distorcer o modelo.")
    return w
