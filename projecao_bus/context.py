"""Facade: contexto de simulação em `application/context`."""

from __future__ import annotations

from projecao_bus.application.context import (
    DATA_SCIENCE_OCIOSIDADE_PADRAO,
    SimulationContext,
    build_simulation_context,
    default_simulation_context,
)

__all__ = [
    "DATA_SCIENCE_OCIOSIDADE_PADRAO",
    "SimulationContext",
    "build_simulation_context",
    "default_simulation_context",
]
