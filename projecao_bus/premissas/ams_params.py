"""Parâmetros de negócio da BU AMS (fonte única para defaults e testes)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AMSProjectionParams:
    aliquota_isv_ams: float
    fb_ams_2025: float
    ratio_incremental_fopm: float
    ticket_ams_base: float
    custo_func_ams_base: float
    horas_por_nf_ams: float
    capex_por_func_novo_ams: float
    taxa_depreciacao_ams: float
    anos_depreciacao_ams: int
    ratio_outras_dir_pct_rl_ams: float
    ratio_rem_socios_pct_mc1_ams: float
    ratio_outras_adm_pct_rl_ams: float
    honorarios_ams_hist: dict[int, float]
    receita_fin_ams_hist: dict[int, float]
    despesa_fin_ams_const: float
    spread_real_base_retida: float
    aliquota_ir_csll: float
    custo_func_grau_livre_adicional: float  # ex.: +1% real sobre custo/func
    horas_por_nf_decay: float  # fator ano a ano (ex.: 0.99)


def default_ams_projection_params() -> AMSProjectionParams:
    return AMSProjectionParams(
        aliquota_isv_ams=0.123,
        fb_ams_2025=15_293_573.83,
        ratio_incremental_fopm=0.0958,
        ticket_ams_base=18_246.57,
        custo_func_ams_base=145_370.0,
        horas_por_nf_ams=105.363,
        capex_por_func_novo_ams=15_000.0,
        taxa_depreciacao_ams=0.20,
        anos_depreciacao_ams=5,
        ratio_outras_dir_pct_rl_ams=0.01880,
        ratio_rem_socios_pct_mc1_ams=0.11046,
        ratio_outras_adm_pct_rl_ams=0.01219,
        honorarios_ams_hist={
            2022: 240_000.0,
            2023: 258_000.0,
            2024: 264_000.0,
            2025: 264_000.0,
        },
        receita_fin_ams_hist={
            2023: 109_000.0,
            2024: 50_000.0,
            2025: 84_000.0,
        },
        despesa_fin_ams_const=56_667.0,
        spread_real_base_retida=0.02,
        aliquota_ir_csll=0.34,
        custo_func_grau_livre_adicional=0.01,
        horas_por_nf_decay=0.99,
    )
