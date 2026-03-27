"""Facade: import estável `projecao_bus.year_config` → implementação em `config/year_config`."""

from __future__ import annotations

from projecao_bus.config.year_config import (
    YearConfig,
    get_active_year_config,
    get_base_year,
    get_historical_year_end,
    get_historical_year_start,
    get_projected_year_start,
    get_projected_years,
    reset_year_config,
    set_active_year_config,
)

__all__ = [
    "YearConfig",
    "get_active_year_config",
    "get_base_year",
    "get_historical_year_end",
    "get_historical_year_start",
    "get_projected_year_start",
    "get_projected_years",
    "reset_year_config",
    "set_active_year_config",
]
