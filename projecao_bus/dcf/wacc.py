"""
Custo de capital próprio (Ke) por dois métodos e WACC (D=0 → média dos Ke).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .constants import (
    BETAS_DESALAVANCADOS,
    CRP_BR,
    ERP_EUA,
    INF_BR,
    INF_EUA,
    PRM,
    PREM_LIQUIDEZ,
    PREM_TAMANHO,
    RF_NTN_B,
    WACC_FIXO,
)


def carregar_faturamentos_bu(base_dir: Path, anos: Iterable[int]) -> dict[int, dict[str, float]]:
    """Faturamento bruto por BU e ano a partir das projeções."""
    proj = base_dir / "projecoes"
    arquivos = {
        "fopm": "projecao_fopm_brasil.csv",
        "renovacao": "projecao_renovacao.csv",
        "ams": "projecao_ams.csv",
        "venda_sw": "projecao_venda_softwares.csv",
        "data_science": "projecao_data_science.csv",
    }
    out: dict[int, dict[str, float]] = {a: {} for a in anos}
    for bu_key, nome in arquivos.items():
        df = pd.read_csv(proj / nome)
        df = df[df["ano"].isin(anos)]
        for _, row in df.iterrows():
            ano = int(row["ano"])
            out[ano][bu_key] = float(row["faturamento_bruto"])
    return out


def beta_ponderado_por_ano(
    faturamentos_por_ano: dict[int, dict[str, float]],
    betas: dict[str, float] | None = None,
) -> dict[int, float]:
    if betas is None:
        betas = BETAS_DESALAVANCADOS
    resultado: dict[int, float] = {}
    for ano, fbu in faturamentos_por_ano.items():
        total_fb = sum(fbu.values())
        if total_fb <= 0:
            resultado[ano] = 0.0
            continue
        resultado[ano] = sum(betas[k] * fbu[k] / total_fb for k in betas if k in fbu)
    return resultado


def ke_usd_spm_global(beta_u: float) -> float:
    """Ke USD (SPM Global) com Rf, ERP EUA, CRP Brasil e prêmios."""
    return RF_NTN_B + beta_u * ERP_EUA + CRP_BR + PREM_TAMANHO + PREM_LIQUIDEZ


def ke_brl_capm_global(ke_usd_spm: float) -> float:
    """Conversão Fisher para BRL."""
    return (1.0 + ke_usd_spm) * (1.0 + INF_BR) / (1.0 + INF_EUA) - 1.0


def ke_capm_brl_direto(beta_u: float) -> float:
    """CAPM em BRL com NTN-B e PRM."""
    return RF_NTN_B + beta_u * PRM + PREM_TAMANHO + PREM_LIQUIDEZ


def wacc_a_partir_de_beta(beta_u: float) -> float:
    """Média aritmética dos dois Ke (empresa sem dívida → WACC ≈ Ke)."""
    k1 = ke_brl_capm_global(ke_usd_spm_global(beta_u))
    k2 = ke_capm_brl_direto(beta_u)
    return (k1 + k2) / 2.0


def wacc_por_ano_projecao(
    base_dir: Path | None = None,
    anos: tuple[int, ...] = (2026, 2027, 2028, 2029, 2030),
) -> dict[int, float]:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    fat = carregar_faturamentos_bu(base_dir, anos)
    betas_u = beta_ponderado_por_ano(fat)
    return {a: wacc_a_partir_de_beta(betas_u[a]) for a in anos}


def wacc_para_dcf(usar_fixo: bool = True, ano_representativo: int = 2029) -> float:
    """
    Plano: pode usar WACC fixo 17,124% (β ~ ano representativo) ou série anual.
    """
    if usar_fixo:
        return WACC_FIXO
    base = Path(__file__).resolve().parent.parent
    serie = wacc_por_ano_projecao(base)
    return serie.get(ano_representativo, WACC_FIXO)
