import io
import shutil
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from projecao_bus.historical_dre import load_historical_dre_bundle
from projecao_bus.context import build_simulation_context
from projecao_bus.infrastructure.paths import data_uploads_active_dir
from projecao_bus.orchestrator import premissas_padrao, resolve_base_values, resultado_para_json, run_simulation
from projecao_bus.base_values import reset_base_values
from projecao_bus.year_config import get_active_year_config, reset_year_config, set_active_year_config

from ..schemas import SimulatePayload

router = APIRouter(prefix="/api", tags=["simulation"])


def _norm_label(s: str) -> str:
    return " ".join(str(s).strip().split()).upper()


def _load_csv_bytes_as_df(content: bytes) -> pd.DataFrame:
    try:
        return pd.read_csv(io.BytesIO(content), encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(io.BytesIO(content), encoding="utf-8", errors="ignore")  # type: ignore[call-arg]


def _get_numeric_year_columns(df: pd.DataFrame) -> list[int]:
    cols: list[int] = []
    for c in df.columns:
        if isinstance(c, str) and c.strip().isdigit():
            cols.append(int(c.strip()))
    return sorted(cols)


def _detect_last_year_with_numeric_values(df: pd.DataFrame, year_cols: list[int]) -> int:
    last: int | None = None
    for y in year_cols:
        col = str(y)
        s = pd.to_numeric(df[col], errors="coerce")
        if s.notna().any():
            last = y
    if last is None:
        raise ValueError("CSV nao possui valores numericos nas colunas de anos.")
    return int(last)


def _validate_csv_shape_and_rows(df: pd.DataFrame, *, required_bu: bool) -> None:
    if "linha" not in df.columns:
        raise ValueError("CSV deve conter coluna 'linha'.")

    linhas_norm = set(_norm_label(v) for v in df["linha"].dropna().astype(str).tolist())

    required_lines = [
        _norm_label("FATURAMENTO BRUTO"),
        _norm_label("RECEITA LÍQUIDA"),
        _norm_label("GASTOS COM PESSOAL"),
        _norm_label("EBITDA"),
        _norm_label("EBIT"),
        _norm_label("LUCRO LÍQUIDO"),
    ]

    missing = [lab for lab in required_lines if lab not in linhas_norm]
    if missing:
        raise ValueError(
            f"CSV faltando linhas obrigatorias: {missing[:3]}{'...' if len(missing) > 3 else ''}"
        )

    if required_bu:
        headcount_ok = any(
            opt in linhas_norm
            for opt in (
                _norm_label("# Funcionários - Média"),
                _norm_label("N.º Funcionários"),
                _norm_label("N.º Funcionários (premissa)"),
            )
        )
        if not headcount_ok:
            raise ValueError("CSV BU faltando linha de headcount ('# Funcionários - Média' ou equivalente).")


def _validate_bp_csv_shape(df: pd.DataFrame) -> None:
    required_cols = {"categoria", "conta", "tipo"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError("CSV de BP deve conter colunas: categoria, conta, tipo.")
    year_cols = _get_numeric_year_columns(df)
    if not year_cols:
        raise ValueError("CSV de BP sem colunas numéricas de anos.")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/defaults")
def get_defaults() -> dict:
    yc = get_active_year_config()
    ctx = build_simulation_context(
        year_config=yc,
        base_values=resolve_base_values(yc),
        premissas=None,
    )
    return premissas_padrao(ctx)


@router.get("/historical-dre")
def get_historical_dre() -> dict:
    """Série histórica (2018–2025) a partir de `data/original/*.csv`."""
    return load_historical_dre_bundle()


@router.post("/simulate")
def post_simulate(payload: SimulatePayload) -> dict:
    resultado = run_simulation(premissas=payload.premissas)
    return resultado_para_json(resultado)


@router.post("/upload-historical")
async def upload_historical(
    consolidado: UploadFile = File(...),
    fopm: UploadFile = File(...),
    renovacao: UploadFile = File(...),
    ams: UploadFile = File(...),
    venda_sw: UploadFile = File(...),
    data_science: UploadFile = File(...),
    administrativa: UploadFile = File(...),
    balanco_patrimonial: UploadFile | None = File(None),
) -> dict[str, Any]:
    """
    Recebe 7 CSVs no formato pivot (coluna 'linha' + colunas de anos),
    salva em `data/uploads/active/` e ajusta `year_config` em memória.
    """
    uploads: dict[str, UploadFile] = {
        "consolidado": consolidado,
        "fopm": fopm,
        "renovacao": renovacao,
        "ams": ams,
        "venda_sw": venda_sw,
        "data_science": data_science,
        "administrativa": administrativa,
    }
    filenames = {
        "consolidado": "consolidado_original.csv",
        "fopm": "dre_fopm_original.csv",
        "renovacao": "dre_renovacao_original.csv",
        "ams": "dre_ams_original.csv",
        "venda_sw": "dre_venda_softwares_original.csv",
        "data_science": "dre_data_science_original.csv",
        "administrativa": "dre_administrativa_original.csv",
    }
    optional_uploads: dict[str, UploadFile | None] = {
        "balanco_patrimonial": balanco_patrimonial,
    }
    optional_filenames = {
        "balanco_patrimonial": "balanco_patrimonial.csv",
    }

    received: dict[str, dict[str, Any]] = {}
    detected_years: list[int] = []
    raw_contents: dict[str, bytes] = {}

    # 1) Lê + valida
    for key, upl in uploads.items():
        content = await upl.read()
        if not content:
            raise HTTPException(status_code=400, detail=f"Arquivo vazio: {key}")
        raw_contents[key] = content

        df = _load_csv_bytes_as_df(content)
        year_cols = _get_numeric_year_columns(df)
        if not year_cols:
            raise HTTPException(status_code=400, detail=f"CSV sem colunas numericas de anos: {key}")

        _validate_csv_shape_and_rows(df, required_bu=(key != "consolidado"))
        last_year = _detect_last_year_with_numeric_values(df, year_cols)
        first_year = int(min(year_cols))

        detected_years.append(last_year)
        received[key] = {"first_year": first_year, "last_year": last_year}

    for key, upl in optional_uploads.items():
        if upl is None:
            continue
        content = await upl.read()
        if not content:
            continue
        raw_contents[key] = content
        if key == "balanco_patrimonial":
            df = _load_csv_bytes_as_df(content)
            _validate_bp_csv_shape(df)

    # 2) Detecta consistencia: todos terminam no mesmo historical_year_end
    unique_last = sorted(set(detected_years))
    if len(unique_last) != 1:
        raise HTTPException(status_code=400, detail=f"Anos finais inconsistentes entre arquivos: {unique_last}")
    historical_year_end = int(unique_last[0])

    historical_year_start = int(received["consolidado"]["first_year"])
    projected_years = tuple(range(historical_year_end + 1, historical_year_end + 6))

    # 3) Salva
    active_dir = data_uploads_active_dir()
    if active_dir.exists():
        shutil.rmtree(active_dir)
    active_dir.mkdir(parents=True, exist_ok=True)

    for key in uploads.keys():
        target_path = active_dir / filenames[key]
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(raw_contents[key])
    for key, upl in optional_uploads.items():
        if upl is None:
            continue
        content = raw_contents.get(key)
        if not content:
            continue
        target_path = active_dir / optional_filenames[key]
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)

    # 4) Ajusta year_config em memória e reseta caches de base-values
    set_active_year_config(
        historical_year_start=historical_year_start,
        historical_year_end=historical_year_end,
        projected_years=projected_years,
    )
    reset_base_values()

    return {
        "historical_year_start": historical_year_start,
        "historical_year_end": historical_year_end,
        "projected_year_start": historical_year_end + 1,
        "projected_year_end": historical_year_end + 5,
        "files_received": list(uploads.keys()) + [k for k in optional_uploads if raw_contents.get(k)],
    }


@router.post("/reset-historical")
def reset_historical() -> dict[str, Any]:
    """Remove `data/uploads/active/` e volta `year_config` ao padrão."""
    active_dir = data_uploads_active_dir()
    if active_dir.exists():
        shutil.rmtree(active_dir)
    reset_year_config()
    reset_base_values()
    return {"status": "ok"}
