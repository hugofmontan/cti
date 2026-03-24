"""
Orquestra BP → NCGL → Fluxo → DCF → sensibilidade.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .bp import carregar_consolidado_csv, montar_bp, total_func_operacional_com_2025
from .constants import ANOS_PROJECAO, G_PERPETUIDADE, WACC_FIXO
from .dcf_valuation import montar_tabela_dcf
from .fluxo import carregar_ams_csv, montar_fluxo
from .ncgl import montar_ncgl
from .sensitivity import cenarios_gabarito, matriz_wacc_g
from .wacc import beta_ponderado_por_ano, carregar_faturamentos_bu, faturamentos_bu_de_dfs, wacc_a_partir_de_beta


def run_dcf_pipeline_from_frames(
    df_consolidado: pd.DataFrame,
    df_ams: pd.DataFrame,
    dfs_bu: dict[str, pd.DataFrame] | None = None,
    *,
    wacc: float | None = None,
    g: float | None = None,
    base_dir: Path | None = None,
    salvar_csv: bool = False,
    out_subdir: str = "dcf_output",
) -> dict[str, Any]:
    """
    DCF a partir de DataFrames em memória (consolidado + AMS).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent

    total_func = total_func_operacional_com_2025()
    w = WACC_FIXO if wacc is None else wacc
    g_ = G_PERPETUIDADE if g is None else g

    df_bp = montar_bp(df_consolidado, total_func, usar_custos_excl_gabarito=True)
    df_ncgl = montar_ncgl(df_bp)
    df_fluxo = montar_fluxo(df_consolidado, df_bp, df_ncgl, df_ams)
    resultado_dcf = montar_tabela_dcf(df_fluxo, df_consolidado, wacc=w, g=g_)

    fcff_list = [float(df_fluxo[df_fluxo["ano"] == a]["fcff"].iloc[0]) for a in ANOS_PROJECAO]
    df_sens_mat = matriz_wacc_g(fcff_list)
    df_cenarios = cenarios_gabarito(fcff_list)

    if dfs_bu:
        fat = faturamentos_bu_de_dfs(dfs_bu, ANOS_PROJECAO)
    else:
        fat = carregar_faturamentos_bu(base_dir, ANOS_PROJECAO)
    betas_ano = beta_ponderado_por_ano(fat)

    out: dict[str, Any] = {
        "df_bp": df_bp,
        "df_ncgl": df_ncgl,
        "df_fluxo": df_fluxo,
        "dcf": resultado_dcf,
        "wacc_fixo": w,
        "beta_ponderado_por_ano": betas_ano,
        "wacc_dinamico_por_ano": {a: wacc_a_partir_de_beta(betas_ano[a]) for a in ANOS_PROJECAO},
        "matriz_sensibilidade": df_sens_mat,
        "cenarios": df_cenarios,
    }

    if salvar_csv:
        out_dir = base_dir / out_subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        df_bp.to_csv(out_dir / "bp.csv", index=False)
        df_ncgl.to_csv(out_dir / "ncgl.csv", index=False)
        df_fluxo.to_csv(out_dir / "fluxo.csv", index=False)
        df_cenarios.to_csv(out_dir / "cenarios.csv", index=False)
        df_sens_mat.to_csv(out_dir / "matriz_wacc_g.csv")
        resumo = pd.DataFrame(
            [
                {"metrica": "soma_vp_fcffs", "valor": resultado_dcf["soma_vp_fcffs"]},
                {"metrica": "vp_valor_terminal", "valor": resultado_dcf["vp_valor_terminal"]},
                {"metrica": "enterprise_value", "valor": resultado_dcf["enterprise_value"]},
                {"metrica": "equity_value", "valor": resultado_dcf["equity_value"]},
                {"metrica": "wacc", "valor": w},
                {"metrica": "g", "valor": g_},
            ]
        )
        resumo.to_csv(out_dir / "dcf_resumo.csv", index=False)
        vp = resultado_dcf["vp_fcff_por_ano"]
        pd.DataFrame([{"ano": k, "vp_fcff": v} for k, v in sorted(vp.items())]).to_csv(
            out_dir / "dcf_vp_fcff.csv", index=False
        )

    return out


def run_dcf_pipeline(
    base_dir: Path | None = None,
    salvar_csv: bool = True,
    out_subdir: str = "dcf_output",
) -> dict[str, Any]:
    """
    Executa a cadeia completa lendo CSVs e opcionalmente grava CSVs em ``base_dir/dcf_output/``.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent

    df_cons = carregar_consolidado_csv(base_dir)
    df_ams = carregar_ams_csv(base_dir)
    return run_dcf_pipeline_from_frames(
        df_cons,
        df_ams,
        wacc=None,
        g=None,
        base_dir=base_dir,
        salvar_csv=salvar_csv,
        out_subdir=out_subdir,
    )


if __name__ == "__main__":
    r = run_dcf_pipeline()
    print("Enterprise Value:", r["dcf"]["enterprise_value"])
    print("Equity Value:", r["dcf"]["equity_value"])
    print("Soma VP FCFFs:", r["dcf"]["soma_vp_fcffs"])
    print("\nCenários:\n", r["cenarios"])
    print("\nMúltiplos:", r["dcf"].get("multiplos"))
