"""Persistência de DataFrames de projeção em CSV."""

from pathlib import Path

import pandas as pd


def salvar_projecao_csv(
    df: pd.DataFrame,
    base_dir: Path | None = None,
    nome_arquivo: str = "projecao_fopm_brasil.csv",
) -> Path:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent

    destino_dir = base_dir / "projecoes"
    destino_dir.mkdir(parents=True, exist_ok=True)

    destino_arquivo = destino_dir / nome_arquivo
    df.to_csv(destino_arquivo, index=False)
    return destino_arquivo
