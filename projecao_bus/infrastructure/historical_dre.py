"""
Carrega DREs a partir de `data/original/*.csv` (formato planilha: linha x anos).
Usado pela API para exibir série histórica (2018–2025) junto à projeção (2026–2030).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from projecao_bus.config.year_config import (
    get_historical_year_end,
    get_historical_year_start,
    get_projected_year_start,
    get_projected_years,
)

from .paths import (
    data_historico_dir,
    data_original_dir,
    data_uploads_active_dir,
)


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
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[dict[str, Any]]:
    yf = get_historical_year_start() if year_from is None else int(year_from)
    yt = get_historical_year_end() if year_to is None else int(year_to)
    rows: list[dict[str, Any]] = []
    for y in range(yf, yt + 1):
        col = str(y)
        if col not in df.columns:
            continue
        rows.append(_row_for_year(df, y))
    return rows


_BP_ACCOUNT_MAP: dict[str, str] = {
    _norm_label("Total Ativo Circulante"): "ativo_circulante_total",
    _norm_label("Caixa e Equivalentes de Caixa"): "caixa",
    _norm_label("Contas a Receber (Clientes)"): "clientes",
    _norm_label("Partes Relacionadas"): "partes_relacionadas",
    _norm_label("Adiantamentos"): "adiantamentos",
    _norm_label("Impostos a Recuperar"): "impostos_recuperar",
    _norm_label("Outros Ativos Circulantes"): "outros_ac",
    _norm_label("Total Ativo Não Circulante"): "ativo_nao_circulante_total",
    _norm_label("Ativo Fiscal Diferido"): "ativo_fiscal_diferido",
    _norm_label("Imobilizado e Intangível (Bruto)"): "imobilizado",
    _norm_label("Depreciação e Amortização Acumulada"): "depr_acumulada",
    _norm_label("Total do Ativo"): "total_ativo",
    _norm_label("Total Passivo Circulante"): "passivo_circulante_total",
    _norm_label("Contas a Pagar"): "contas_a_pagar",
    _norm_label("Fornecedores"): "fornecedores",
    _norm_label("Obrigações Trabalhistas e Sociais"): "obrig_trabalhistas",
    _norm_label("Obrigações Fiscais"): "obrig_fiscais",
    _norm_label("Provisões"): "provisoes",
    _norm_label("Outras Obrigações"): "outras_obrigacoes",
    _norm_label("Total Passivo Não Circulante"): "passivo_nao_circulante_total",
    _norm_label("Receitas Diferidas"): "receitas_diferidas",
    _norm_label("Patrimônio Líquido"): "pl",
    _norm_label("Total do Passivo e PL"): "total_passivo_pl",
}


def load_historical_bp(path: Path | None = None) -> list[dict[str, Any]]:
    if path is not None:
        bp_path = path
    else:
        active_path = data_uploads_active_dir() / "balanco_patrimonial.csv"
        bp_path = active_path if active_path.exists() else (data_historico_dir() / "balanco_patrimonial.csv")
    if not bp_path.exists():
        return []

    df = pd.read_csv(bp_path, encoding="utf-8")
    if "conta" not in df.columns:
        raise ValueError(f"CSV de BP sem coluna 'conta': {bp_path}")

    df["conta_norm"] = df["conta"].map(lambda x: _norm_label(x) if pd.notna(x) else "")
    year_cols = sorted(int(c) for c in df.columns if isinstance(c, str) and c.isdigit())
    rows: list[dict[str, Any]] = []
    for year in year_cols:
        col = str(year)
        row: dict[str, Any] = {"ano": year}
        for _, rec in df.iterrows():
            key = _BP_ACCOUNT_MAP.get(str(rec["conta_norm"]))
            if not key:
                continue
            v = _cell_to_float(rec[col]) if col in df.columns else None
            if v is not None:
                row[key] = v
        rows.append(row)
    return rows


def load_historical_dre_bundle() -> dict[str, Any]:
    """
    Carrega consolidado + BUs a partir de `data/uploads/active/` (se existir),
    senão cai em `data/original/`.
    """
    active = data_uploads_active_dir()
    base = active if (active / "consolidado_original.csv").exists() else data_original_dir()
    files: dict[str, Path] = {
        "consolidado": base / "consolidado_original.csv",
        "fopm": base / "dre_fopm_original.csv",
        "renovacao": base / "dre_renovacao_original.csv",
        "ams": base / "dre_ams_original.csv",
        "venda_sw": base / "dre_venda_softwares_original.csv",
        "data_science": base / "dre_data_science_original.csv",
        "administrativa": base / "dre_administrativa_original.csv",
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

    from projecao_bus.rateio_administrativo import load_headcount_funcionarios_bu_csv

    hc_df = load_headcount_funcionarios_bu_csv()
    headcount_operacional_bu = hc_df.to_dict(orient="records")

    return {
        "consolidado": consolidado,
        "dre": out_dre,
        "bp": load_historical_bp(),
        "headcount_operacional_bu": headcount_operacional_bu,
        "historical_year_start": get_historical_year_start(),
        "historical_year_end": get_historical_year_end(),
        "projected_year_start": get_projected_year_start(),
        "projected_years": list(get_projected_years()),
        "projected_year_end": get_projected_years()[-1],
    }
