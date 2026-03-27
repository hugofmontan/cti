"""
Configuração de anos usada pelo motor de projeção/DT (histórico vs projeção).

Este módulo existe para remover "hardcodes" espalhados (ex.: 2025/2026–2030)
e permitir que a fronteira histórico/projeção mude quando o usuário importar
novos CSVs.

Neste passo (fase 1.1-1.2), mantemos o comportamento padrão atual:
- histórico: 2018..2025
- projeção: 2026..2030

A função `set_active_year_config` será usada pelo endpoint de upload (fase 1.5+).
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Iterable, Tuple


@dataclass(frozen=True)
class YearConfig:
    historical_year_start: int
    historical_year_end: int
    projected_years: Tuple[int, ...]

    @property
    def base_year(self) -> int:
        # Base do modelo para ancorar a primeira etapa de projeção (hoje: último ano histórico).
        return self.historical_year_end


_DEFAULT_CONFIG = YearConfig(
    historical_year_start=2018,
    historical_year_end=2025,
    projected_years=(2026, 2027, 2028, 2029, 2030),
)

_lock = RLock()
_active_config: YearConfig = _DEFAULT_CONFIG


def get_active_year_config() -> YearConfig:
    with _lock:
        return _active_config


def reset_year_config() -> None:
    """Volta para o padrão (dados em `data/original`)."""
    global _active_config
    with _lock:
        _active_config = _DEFAULT_CONFIG


def set_active_year_config(historical_year_start: int, historical_year_end: int, projected_years: Iterable[int]) -> None:
    """Define a fronteira histórico/projeção em runtime (por upload)."""
    global _active_config
    projected = tuple(int(y) for y in projected_years)
    if not projected:
        raise ValueError("projected_years nao pode ser vazio")
    if projected[0] <= historical_year_end:
        raise ValueError("projected_years[0] deve ser > historical_year_end")

    with _lock:
        _active_config = YearConfig(
            historical_year_start=int(historical_year_start),
            historical_year_end=int(historical_year_end),
            projected_years=projected,
        )


def get_historical_year_start() -> int:
    return get_active_year_config().historical_year_start


def get_historical_year_end() -> int:
    return get_active_year_config().historical_year_end


def get_projected_years() -> Tuple[int, ...]:
    return get_active_year_config().projected_years


def get_projected_year_start() -> int:
    return get_active_year_config().projected_years[0]


def get_base_year() -> int:
    return get_active_year_config().base_year
