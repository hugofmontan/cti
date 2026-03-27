"""Parâmetros operacionais da BU Data Science (capacidade e ratios DRE)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataScienceProjectionParams:
    horas_por_projeto: float
    horas_mes: float
    meses_ano: float
    ratio_incentivos_pct_rl: float
    ratio_outras_dir_pct_rl: float
    ratio_rem_socios_pct_mc1: float
    ratio_outras_adm_pct_rl: float
    custo_func_grau_livre_adicional: float


def default_data_science_projection_params() -> DataScienceProjectionParams:
    return DataScienceProjectionParams(
        horas_por_projeto=3840.0,
        horas_mes=160.0,
        meses_ano=12.0,
        ratio_incentivos_pct_rl=0.0285,
        ratio_outras_dir_pct_rl=0.0338,
        ratio_rem_socios_pct_mc1=0.1656,
        ratio_outras_adm_pct_rl=0.1277,
        custo_func_grau_livre_adicional=0.01,
    )
