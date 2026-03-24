from pathlib import Path
from typing import Iterable

import pandas as pd

INFLACAO_FOCUS = {
    2026: 0.0397,
    2027: 0.0380,
    2028: 0.0350,
    2029: 0.0350,
    2030: 0.0350,
}

ALIQUOTA_ISV = 0.1743


def _validar_anos(anos: Iterable[int]) -> list[int]:
    anos_list = list(anos)
    if not anos_list:
        raise ValueError("Lista de anos não pode ser vazia.")
    for ano in anos_list:
        if ano not in INFLACAO_FOCUS:
            raise ValueError(f"Ano {ano} não possui premissas cadastradas.")
    return sorted(anos_list)


def salvar_projecao_csv(
    df: pd.DataFrame,
    base_dir: Path | None = None,
    nome_arquivo: str = "projecao_fopm_brasil.csv",
) -> Path:
    """
    Salva o DataFrame de projeção no caminho padrão `projecoes/<nome_arquivo>`
    abaixo do diretório base informado (por padrão, o diretório deste pacote).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent

    destino_dir = base_dir / "projecoes"
    destino_dir.mkdir(parents=True, exist_ok=True)

    destino_arquivo = destino_dir / nome_arquivo
    df.to_csv(destino_arquivo, index=False)
    return destino_arquivo
