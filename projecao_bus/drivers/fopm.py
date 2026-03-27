"""Drivers FOPM derivados de CSV histórico (sem IO no import — chame explicitamente)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd

from ..infrastructure.paths import data_historico_dir


@dataclass(frozen=True)
class FOPMDrivers:
    ratio_incentivos_pct_rl: float
    ratio_outras_dir_pct_rl: float
    ratio_rem_socios_pct_mc1: float
    ratio_outras_adm_pct_rl: float
    custo_func_base: float
    horas_por_nf: float
    ticket_base_projecao: float
    honorarios_base: float


def _carregar_historico_csv(
    caminho_csv: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    if caminho_csv is None:
        caminho_csv = data_historico_dir() / "dre_fopm_historico.csv"

    df = pd.read_csv(caminho_csv)
    if "linha" not in df.columns:
        raise ValueError("CSV histórico deve ter a coluna 'linha'.")

    df = df.set_index("linha")
    return df


def _media_ratio_seguro(numerador: np.ndarray, denominador: np.ndarray) -> float:
    numerador = np.asarray(numerador, dtype="float64")
    denominador = np.asarray(denominador, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(denominador == 0, np.nan, numerador / denominador)
    return float(np.nanmean(ratio))


def calcular_drivers_fopm_from_csv(
    caminho_csv: Optional[Union[str, Path]] = None,
    janela_anos: int = 3,
) -> FOPMDrivers:
    """
    Calcula ratios e âncoras a partir do CSV histórico FOPM.
    """
    df = _carregar_historico_csv(caminho_csv)

    col_anos = [c for c in df.columns if isinstance(c, str) and c.isdigit()]
    if not col_anos:
        raise ValueError("CSV histórico não possui colunas de anos numéricos (ex: '2023').")
    col_anos_ordenados = sorted(col_anos)

    anos_base = col_anos_ordenados[-janela_anos:]

    def linha_valores(label: str) -> np.ndarray:
        if label not in df.index:
            raise KeyError(f"Linha '{label}' não encontrada no histórico.")
        return df.loc[label, anos_base].to_numpy(dtype="float64")

    rl = linha_valores("RECEITA LÍQUIDA")
    incentivos = linha_valores("INCENTIVOS DE PROSPECÇÃO E VENDAS")
    ratio_incentivos_pct_rl = _media_ratio_seguro(incentivos, rl)

    outras_dir = linha_valores("OUTRAS DESPESAS DIRETAS")
    ratio_outras_dir_pct_rl = _media_ratio_seguro(outras_dir, rl)

    mc1 = linha_valores("MARGEM CONTRIBUIÇÃO I")
    rem_socios = linha_valores("REMUNERAÇÃO DIRETA DOS SÓCIOS")
    ratio_rem_socios_pct_mc1 = _media_ratio_seguro(rem_socios, mc1)

    outras_adm = linha_valores("OUTRAS DESPESAS ADMINISTRATIVAS")
    ratio_outras_adm_pct_rl = _media_ratio_seguro(outras_adm, rl)

    try:
        gastos_pessoal = linha_valores("GASTOS COM PESSOAL")
        n_func_hist = linha_valores("# Funcionários - Média")
        with np.errstate(divide="ignore", invalid="ignore"):
            custo_func_anos = np.where(n_func_hist == 0, np.nan, gastos_pessoal / n_func_hist)
        custo_func_base = float(np.nanmean(custo_func_anos))
    except KeyError:
        custo_func_base = 144998.0

    horas_alocadas_hist = {
        2023: 67830.0,
        2024: 63130.0,
        2025: 65280.0,
    }
    nfs_hist = {
        2023: 216.0,
        2024: 258.0,
        2025: 249.0,
    }
    anos_premissas_horas = sorted(horas_alocadas_hist.keys())
    anos_premissas_janela = anos_premissas_horas[-janela_anos:]

    horas_por_nf_anos = []
    for ano in anos_premissas_janela:
        h = horas_alocadas_hist[ano]
        nfs = nfs_hist.get(ano, 0.0)
        horas_por_nf_anos.append(h / nfs if nfs else np.nan)
    horas_por_nf = float(np.nanmean(np.array(horas_por_nf_anos, dtype="float64")))

    ticket_2024 = 95_237.0
    ticket_2025 = 91_514.0
    ticket_base_projecao = (ticket_2024 + ticket_2025) / 2.0

    honorarios_base = 528000.0

    return FOPMDrivers(
        ratio_incentivos_pct_rl=ratio_incentivos_pct_rl,
        ratio_outras_dir_pct_rl=ratio_outras_dir_pct_rl,
        ratio_rem_socios_pct_mc1=ratio_rem_socios_pct_mc1,
        ratio_outras_adm_pct_rl=ratio_outras_adm_pct_rl,
        custo_func_base=custo_func_base,
        horas_por_nf=horas_por_nf,
        ticket_base_projecao=ticket_base_projecao,
        honorarios_base=honorarios_base,
    )
