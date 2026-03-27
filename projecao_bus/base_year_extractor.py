"""
Extrai valores de "base-year" (base_year) a partir do histórico (DRE + headcount)
para substituir âncoras hardcoded (ex.: CAIXA_BASE_2025, FB_AMS_2025, etc.).

Nesta etapa (to-do 2), implementamos:
- âncoras do DCF: caixa/base de BP/NCG no base_year (calculadas reprocessando
  o motor por 2026..base_year com âncoras padrão de 2025);
- âncoras de BU (AMS/Renov/VendaSW):
  - FB base a partir de FATURAMENTO BRUTO no base_year;
  - custo por funcionário base via média de gastos_pessoal/n_funcionarios
    nos últimos 3 anos disponíveis (ending base_year);
  - ticket/hora (AMS) via linhas operacionais do CSV (Ticket/Horas/Custo).

Observacao: esse mecanismo pressupõe que os CSVs de DRE do histórico
incluem o base_year em colunas e que as linhas operacionais do AMS existem.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .base_values import BaseValues, default_base_values
from .context import build_simulation_context
from .infrastructure.paths import data_original_dir, data_uploads_active_dir
from .year_config import (
    get_historical_year_start,
    get_historical_year_end,
    get_projected_years,
    YearConfig,
)


def _norm_label(s: str) -> str:
    return " ".join(str(s).strip().split()).upper()


def _cell_to_float(raw: Any) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, float) and np.isnan(raw):
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


def _get_val(pivot: pd.DataFrame, label_norm: str, year: int) -> float | None:
    col = str(year)
    if label_norm not in pivot.index or col not in pivot.columns:
        return None
    return _cell_to_float(pivot.loc[label_norm, col])


def _get_row_for_year(rows: list[dict[str, Any]], year: int) -> dict[str, Any] | None:
    return next((r for r in rows if int(r.get("ano", -1)) == year), None)


def _avg_last_3_years(
    rows: list[dict[str, Any]],
    base_year: int,
    value_fn,
) -> float:
    vals: list[float] = []
    for y in range(base_year - 2, base_year + 1):
        row = _get_row_for_year(rows, y)
        if not row:
            raise ValueError(f"Historico sem linha para ano {y} (base_year={base_year}).")
        v = value_fn(row, y)
        if v is None or (isinstance(v, float) and np.isnan(v)):
            raise ValueError(f"Valor base ausente para ano {y} (base_year={base_year}).")
        vals.append(float(v))
    return float(np.mean(vals))


def extract_base_year_values(
    historical_bundle: dict[str, Any],
    base_year: int,
    *,
    original_dir: Path | None = None,
) -> BaseValues:
    """
    Retorna BaseValues para substituir âncoras hardcoded do motor.
    """
    default_hist_end = get_historical_year_end()

    # Defaults atuais: se base_year já é o fim histórico padrão ativo, não recalcula.
    if base_year == default_hist_end:
        return default_base_values()

    if original_dir is None:
        active = data_uploads_active_dir()
        # Se existir upload ativo, as âncoras operacionais (AMS) precisam vir dele,
        # pois o base_year pode ter mudado (ex.: 2026) e os originais podem não ter
        # as linhas preenchidas para esse ano.
        original_dir = active if (active / "dre_ams_original.csv").exists() else data_original_dir()

    dre = historical_bundle.get("dre", {})

    # --- Âncoras BU via DRE (FB, gastos_pessoal, n_funcionarios) ---
    def fb_for(bu: str) -> float:
        rows = dre.get(bu, [])
        row = _get_row_for_year(rows, base_year)
        if not row:
            raise ValueError(f"Sem dados históricos para BU={bu} no ano base_year={base_year}.")
        v = row.get("receita_bruta")
        if v is None:
            raise ValueError(f"Sem receita_bruta para BU={bu} ano={base_year}.")
        return float(v)

    def custo_func_from_dre(row: dict[str, Any]) -> float | None:
        gastos = row.get("gastos_pessoal")
        funcs = row.get("n_funcionarios")
        if gastos is None or funcs in (None, 0):
            return None
        return float(gastos) / float(funcs)

    renov_rows = dre.get("renovacao", [])
    venda_rows = dre.get("venda_sw", [])
    ams_rows = dre.get("ams", [])

    if not renov_rows or not venda_rows or not ams_rows:
        raise ValueError("historical_bundle sem as BUs esperadas (ams/renovacao/venda_sw).")

    fb_ams_base = fb_for("ams")
    fb_renovacao_base = fb_for("renovacao")
    fb_venda_sw_base = fb_for("venda_sw")

    custo_func_renovacao_base = _avg_last_3_years(
        renov_rows,
        base_year,
        lambda row, _y: custo_func_from_dre(row),
    )
    custo_func_venda_sw_base = _avg_last_3_years(
        venda_rows,
        base_year,
        lambda row, _y: custo_func_from_dre(row),
    )

    # --- AMS: ticket/hora/custo (linhas operacionais no CSV) ---
    ams_csv = original_dir / "dre_ams_original.csv"
    if not ams_csv.exists():
        raise ValueError(f"Arquivo de AMS nao encontrado para extracao: {ams_csv}")

    pivot_ams = _load_pivot_csv(ams_csv)
    ticket_label = _norm_label("Ticket Médio / NF (R$)")
    custo_label = _norm_label("Custo / Funcionário (R$)")
    horas_nf_label = _norm_label("Horas / NF (média hist.)")

    def avg_operational(label_norm: str) -> float:
        """
        Média dos últimos 3 anos com valor numérico disponível (<= base_year).

        Motivo: ao trocar a fronteira histórico/projeção via upload, é comum que o
        "novo" último ano (ex.: 2026) tenha valores parciais/ausentes em linhas
        operacionais de premissas. O motor deve degradar graciosamente usando os
        anos anteriores, em vez de exigir base_year-2..base_year completos.
        """
        vals: list[float] = []
        # busca retroativa a partir do base_year, coletando 3 valores válidos
        for y in range(base_year, get_historical_year_start() - 1, -1):
            v = _get_val(pivot_ams, label_norm, y)
            if v is None:
                continue
            vals.append(v)
            if len(vals) >= 3:
                break
        if not vals:
            raise ValueError(f"Valor operacional AMS ausente: {label_norm} (sem valores <= {base_year})")
        return float(np.mean(list(reversed(vals))))

    ticket_ams_base = avg_operational(ticket_label)
    custo_func_ams_base = avg_operational(custo_label)
    horas_por_nf_ams = avg_operational(horas_nf_label)

    # --- Âncoras DCF (CAIXA/BP/NCG) calculadas rodando o motor até base_year ---
    # Calculamos CAIXA_BASE/base de BP/NCG para base_year usando DRE do historical_bundle.
    # Para isso, reprocessamos o motor no intervalo (primeiro_ano_projetado..base_year).
    projected_years = get_projected_years()
    projected_start = int(projected_years[0])
    anos_proj_calc = tuple(range(projected_start, base_year + 1))
    if not anos_proj_calc:
        raise ValueError("base_year nao suportado para calculo incremental de DCF.")

    yc_temp = YearConfig(
        historical_year_start=get_historical_year_start(),
        historical_year_end=default_hist_end,
        projected_years=tuple(anos_proj_calc),
    )
    ctx_temp = build_simulation_context(
        year_config=yc_temp,
        base_values=default_base_values(),
        premissas=None,
    )

    df_consolidado = pd.DataFrame(historical_bundle.get("consolidado", []))
    df_ams = pd.DataFrame(dre.get("ams", []))

    if "ano" not in df_consolidado.columns:
        raise ValueError("historical_bundle.consolidado sem coluna 'ano'.")
    if "ano" not in df_ams.columns:
        raise ValueError("historical_bundle.dre['ams'] sem coluna 'ano'.")
    if "irpj_csll" not in df_ams.columns:
        df_ams["irpj_csll"] = 0.0

    df_consolidado = df_consolidado[df_consolidado["ano"].isin(anos_proj_calc)]
    df_ams = df_ams[df_ams["ano"].isin(anos_proj_calc)]

    from .dcf.bp import montar_bp, total_func_operacional_com_historico
    from .dcf.fluxo import montar_fluxo
    from .dcf.ncgl import montar_ncgl

    total_func = total_func_operacional_com_historico(ctx_temp)
    df_bp = montar_bp(df_consolidado, total_func, ctx_temp, usar_custos_excl_gabarito=True)
    df_ncgl = montar_ncgl(df_bp, ctx_temp)
    df_fluxo = montar_fluxo(df_consolidado, df_bp, df_ncgl, df_ams, ctx_temp)

    row_bp = df_bp[df_bp["ano"] == base_year].iloc[0]
    row_ncgl = df_ncgl[df_ncgl["ano"] == base_year].iloc[0]
    row_fluxo = df_fluxo[df_fluxo["ano"] == base_year].iloc[0]

    caixa_base = float(row_fluxo["caixa_final"])
    imobilizado_base = float(row_bp["imobilizado"])
    depr_acum_base = float(row_bp["depr_acumulada"])
    ncg_base = float(row_ncgl["ncg"])
    ac_op_base = float(row_ncgl["ac_op"])
    pc_op_base = float(row_ncgl["pc_op"])

    return BaseValues(
        base_year=base_year,
        caixa_base=caixa_base,
        imobilizado_base=imobilizado_base,
        depr_acum_base=depr_acum_base,
        ncg_base=ncg_base,
        ac_op_base=ac_op_base,
        pc_op_base=pc_op_base,
        fb_ams_base=fb_ams_base,
        ticket_ams_base=ticket_ams_base,
        custo_func_ams_base=custo_func_ams_base,
        horas_por_nf_ams=horas_por_nf_ams,
        fb_renovacao_base=fb_renovacao_base,
        custo_func_renovacao_base=custo_func_renovacao_base,
        fb_venda_sw_base=fb_venda_sw_base,
        custo_func_venda_sw_base=custo_func_venda_sw_base,
    )

