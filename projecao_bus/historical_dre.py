"""Facade: carga de histórico DRE/BP em `infrastructure/historical_dre`."""

from __future__ import annotations

from projecao_bus.infrastructure.historical_dre import (
    build_historical_series,
    load_historical_bp,
    load_historical_dre_bundle,
)

__all__ = [
    "build_historical_series",
    "load_historical_bp",
    "load_historical_dre_bundle",
]
