"""Única fonte de paths do repositório e pastas de dados (evita duplicar Path parents)."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Raiz do repositório (pasta que contém `data/`, `api/`, etc.)."""
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return repo_root() / "data"


def data_original_dir() -> Path:
    return data_dir() / "original"


def data_uploads_active_dir() -> Path:
    return data_dir() / "uploads" / "active"


def data_historico_dir() -> Path:
    return data_dir() / "historico"


def projecao_bus_package_root() -> Path:
    """Diretório do pacote `projecao_bus` (o que antes era `Path(orchestrator.__file__).parent`)."""
    return Path(__file__).resolve().parent.parent
