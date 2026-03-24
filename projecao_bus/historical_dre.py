"""
Carrega DREs a partir de `data/original/*.csv` (formato planilha: linha x anos).
Usado pela API para exibir série histórica (2018–2025) junto à projeção (2026–2030).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Último ano considerado "histórico" (dados realizados / fechados na base).
HISTORICAL_YEAR_END = 2025
HISTORICAL_YEAR_START = 2018


def _norm_label(s: str) -> str:
    return " ".join(str(s).strip().split()).upper()


# Labels da planilha (normalizados) → chave canônica (frontend / API)
_SINGLE_LINE_MAP: dict[str, str] = {
    _norm_label("FATURAMENTO BRUTO"): "receita_bruta",
    _norm_label("(-) IMPOSTOS SOBRE VENDA"): "deducoes",
    _norm_label("RECEITA LÍQUIDA"): "receita_liquida",
    _norm_label("INCENTIVOS DE PROSPECÇÃO E VENDAS"): "incentivos",
    _norm_label("GASTOS COM PESSOAL"): "gastos_pessoal",
    _norm_label("OUTRAS DESPESAS DIRETAS"): "outras_desp_diretas",
    _norm_label("MARGEM CONTRIBUIÇÃO I"): "mc1",
    _norm_label("REMUNERAÇÃO DIRETA DOS SÓCIOS"): "remuneracao_socios",
    _norm_label("MARGEM CONTRIBUIÇÃO II"): "mc2",
    _norm_label("OUTRAS DESPESAS ADMINISTRATIVAS"): "outras_desp_adm",
    _norm_label("EBITDA"): "ebitda",
    _norm_label("Depreciação/Amortização"): "da_consolidada",
    _norm_label("EBIT"): "ebit",
    _norm_label("Receita Financeira"): "receita_financeira",
    _norm_label("Despesa Financeira"): "despesa_financeira",
    _norm_label("LAIR"): "lair",
    _norm_label("IR/CSLL"): "irpj_csll",
    _norm_label("LUCRO LÍQUIDO"): "lucro_liquido",
}

_HONOR_LINES = (
    _norm_label("HONORÁRIOS ADM SÓCIOS DIRETORES"),
    _norm_label("HONORÁRIOS ADM SÓCIOS DIRETORES (Rateio)"),
)

# Headcount exibido no front (BUBreakdown): primeira linha encontrada no CSV da BU.
_N_FUNCIONARIOS_LABELS = (
    _norm_label("# Funcionários - Média"),
    _norm_label("N.º Funcionários"),
    _norm_label("N.º Funcionários (premissa)"),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _original_dir() -> Path:
    return _repo_root() / "data" / "original"


def _cell_to_float(raw: Any) -> float | None:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return None
    if isinstance(raw, str):
        t = raw.strip()
        if t in {"", "-", "—"}:
            return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _load_pivot_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    if "linha" not in df.columns:
        raise ValueError(f"CSV sem coluna 'linha': {path}")
    df["linha"] = df["linha"].map(lambda x: _norm_label(x) if pd.notna(x) else "")
    df = df[df["linha"] != ""]
    df = df.drop_duplicates(subset=["linha"], keep="first")
    return df.set_index("linha")


def _row_for_year(df: pd.DataFrame, year: int) -> dict[str, Any]:
    col = str(year)
    if col not in df.columns:
        return {"ano": year}

    out: dict[str, Any] = {"ano": year}

    for label_norm, key in _SINGLE_LINE_MAP.items():
        if label_norm not in df.index:
            continue
        v = _cell_to_float(df.loc[label_norm, col])
        if v is not None:
            out[key] = v

    hon_sum = 0.0
    hon_any = False
    for label_norm in _HONOR_LINES:
        if label_norm not in df.index:
            continue
        v = _cell_to_float(df.loc[label_norm, col])
        if v is not None:
            hon_sum += v
            hon_any = True
    if hon_any:
        out["honorarios_adm"] = hon_sum

    for label_norm in _N_FUNCIONARIOS_LABELS:
        if label_norm not in df.index:
            continue
        v = _cell_to_float(df.loc[label_norm, col])
        if v is not None:
            out["n_funcionarios"] = v
            break

    rl = out.get("receita_liquida")
    ebitda = out.get("ebitda")
    ll = out.get("lucro_liquido")
    if rl and rl != 0:
        if ebitda is not None:
            out["ebitda_pct_rl"] = ebitda / rl
        if ll is not None:
            out["lucro_liquido_pct_rl"] = ll / rl

    return out


def build_historical_series(
    df: pd.DataFrame,
    *,
    year_from: int = HISTORICAL_YEAR_START,
    year_to: int = HISTORICAL_YEAR_END,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for y in range(year_from, year_to + 1):
        col = str(y)
        if col not in df.columns:
            continue
        rows.append(_row_for_year(df, y))
    return rows


def load_historical_dre_bundle() -> dict[str, Any]:
    """
    Carrega consolidado + 5 BUs a partir de `data/original/`.
    """
    base = _original_dir()
    files: dict[str, Path] = {
        "consolidado": base / "consolidado_original.csv",
        "fopm": base / "dre_fopm_original.csv",
        "renovacao": base / "dre_renovacao_original.csv",
        "ams": base / "dre_ams_original.csv",
        "venda_sw": base / "dre_venda_softwares_original.csv",
        "data_science": base / "dre_data_science_original.csv",
    }

    out_dre: dict[str, list[dict[str, Any]]] = {}
    for key, path in files.items():
        if key == "consolidado":
            continue
        if not path.exists():
            out_dre[key] = []
            continue
        df = _load_pivot_csv(path)
        out_dre[key] = build_historical_series(df)

    consolidado: list[dict[str, Any]] = []
    cpath = files["consolidado"]
    if cpath.exists():
        consolidado = build_historical_series(_load_pivot_csv(cpath))

    from .rateio_administrativo import load_headcount_funcionarios_bu_csv

    hc_df = load_headcount_funcionarios_bu_csv()
    headcount_operacional_bu = hc_df.to_dict(orient="records")

    return {
        "consolidado": consolidado,
        "dre": out_dre,
        "headcount_operacional_bu": headcount_operacional_bu,
        "historical_year_start": HISTORICAL_YEAR_START,
        "historical_year_end": HISTORICAL_YEAR_END,
        "projected_year_start": 2026,
    }
