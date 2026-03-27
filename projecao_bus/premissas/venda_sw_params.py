"""Parâmetros de negócio da BU Venda de Softwares."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VendaSoftwaresProjectionParams:
    fb_venda_softwares_2025: float
    n_func_venda_softwares: int
    fator_crescimento_real: float
    custo_func_2025: float
    ratio_incentivos_pct_rl: float
    ratio_outras_dir_pct_rl: float
    honorarios_adm_fixo: float
    custo_func_grau_livre_adicional: float


def default_venda_softwares_projection_params() -> VendaSoftwaresProjectionParams:
    return VendaSoftwaresProjectionParams(
        fb_venda_softwares_2025=7_722_610.43,
        n_func_venda_softwares=1,
        fator_crescimento_real=0.045,
        custo_func_2025=169_393.04,
        ratio_incentivos_pct_rl=(
            (40_771.81 / 2_645_872.52 + 157_306.64 / 5_002_292.92 + 168_010.36 / 6_353_758.49) / 3.0
        ),
        ratio_outras_dir_pct_rl=1_172_937.78 / 6_353_758.49,
        honorarios_adm_fixo=(322_500.0 + 330_000.0 + 330_000.0) / 3.0,
        custo_func_grau_livre_adicional=0.01,
    )
