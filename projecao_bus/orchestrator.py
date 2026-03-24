"""
Orquestra projeções das BUs em memória e DCF (sem gravar CSVs).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .ams import RATIO_INCREMENTAL_FOPM, projetar_dre_ams
from .consolidado import ANOS_PADRAO, projetar_dre_consolidado_de_dfs
from .data_science import TOTAL_PROJETOS_DS, projetar_dre_data_science
from .dcf.constants import G_PERPETUIDADE, WACC_FIXO
from .dcf.pipeline import run_dcf_pipeline_from_frames
from .rateio_administrativo import aplicar_rateio_projetado_nas_dres
from .fopm import HEADCOUNT_PLANEJADO, OCIOSIDADE, projetar_dre_fopm_brasil
from .renovacao import SPREAD_REAJUSTE_RENOVACAO, projetar_dre_renovacao
from .venda_softwares import FATOR_CRESCIMENTO_REAL, projetar_dre_venda_softwares

ANOS = list(ANOS_PADRAO)


def _merge_int_year_dict(
    default: dict[int, Any],
    override: dict[str, Any] | dict[int, Any] | None,
) -> dict[int, Any]:
    out = dict(default)
    if not override:
        return out
    for k, v in override.items():
        out[int(k)] = v
    return out


def premissas_padrao() -> dict[str, Any]:
    """Valores espelhando constantes dos módulos (chaves de ano como string para JSON)."""
    return {
        "fopm": {
            "headcount_por_ano": {str(y): HEADCOUNT_PLANEJADO[y] for y in ANOS},
            "ociosidade_por_ano": {str(y): OCIOSIDADE[y] for y in ANOS},
        },
        "renovacao": {"spread_real": SPREAD_REAJUSTE_RENOVACAO, "churn": 0.0},
        "ams": {"taxa_conversao_fopm": RATIO_INCREMENTAL_FOPM, "churn": 0.0},
        "venda_softwares": {"fator_crescimento_real": FATOR_CRESCIMENTO_REAL},
        "data_science": {
            "total_projetos_por_ano": {str(y): TOTAL_PROJETOS_DS[y] for y in ANOS},
        },
        "dcf": {"wacc": WACC_FIXO, "g": G_PERPETUIDADE},
    }


def _deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and k in out and isinstance(out[k], dict):
            out[k] = _deep_merge(out[k], v)  # type: ignore[assignment]
        else:
            out[k] = v
    return out


def run_simulation(
    premissas: dict[str, Any] | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Executa FOPM → Renovação → AMS → Venda SW → Data Science → Consolidado → DCF.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent

    p = premissas_padrao()
    if premissas:
        p = _deep_merge(p, premissas)

    fc = p["fopm"]
    hc_def = {y: HEADCOUNT_PLANEJADO[y] for y in ANOS}
    oc_def = {y: OCIOSIDADE[y] for y in ANOS}
    headcount_por_ano = _merge_int_year_dict(hc_def, fc.get("headcount_por_ano"))
    ociosidade_por_ano = _merge_int_year_dict(oc_def, fc.get("ociosidade_por_ano"))

    df_fopm = projetar_dre_fopm_brasil(
        anos=ANOS,
        headcount_por_ano=headcount_por_ano,
        ociosidade_por_ano=ociosidade_por_ano,
    )

    ren = p["renovacao"]
    spread = ren.get("spread_real")
    if spread is not None:
        spread = float(spread)
    df_renov = projetar_dre_renovacao(
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
        anos=ANOS,
        taxa_conversao_fopm=tc,
        churn=float(ams_p.get("churn", 0.0)),
    )

    vs = p["venda_softwares"]
    fcr = vs.get("fator_crescimento_real")
    if fcr is not None:
        fcr = float(fcr)
    df_vsw = projetar_dre_venda_softwares(anos=ANOS, fator_crescimento_real=fcr)

    ds = p["data_science"]
    tp_def = {y: TOTAL_PROJETOS_DS[y] for y in ANOS}
    total_projetos = _merge_int_year_dict(tp_def, ds.get("total_projetos_por_ano"))
    total_projetos = {k: int(v) for k, v in total_projetos.items()}
    df_ds = projetar_dre_data_science(anos=ANOS, total_projetos_por_ano=total_projetos)

    dfs = {
        "fopm": df_fopm,
        "renovacao": df_renov,
        "ams": df_ams,
        "venda_sw": df_vsw,
        "data_science": df_ds,
    }

    aplicar_rateio_projetado_nas_dres(dfs)

    df_cons = projetar_dre_consolidado_de_dfs(dfs, anos=ANOS)

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
        dfs_bu=dfs,
        wacc=wacc,
        g=g,
        base_dir=base_dir,
        salvar_csv=False,
    )

    return {
        "premissas_efetivas": p,
        "dre": dfs,
        "consolidado": df_cons,
        "dcf": dcf_bundle,
    }


def resultado_para_json(resultado: dict[str, Any]) -> dict[str, Any]:
    """Converte DataFrames em listas de dicts para resposta JSON."""

    def df_to_records(df: pd.DataFrame) -> list[dict]:
        import numpy as np

        return df.replace({np.nan: None}).to_dict(orient="records")

    out: dict[str, Any] = {
        "premissas_efetivas": resultado["premissas_efetivas"],
        "dre": {k: df_to_records(v) for k, v in resultado["dre"].items()},
        "consolidado": df_to_records(resultado["consolidado"]),
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
