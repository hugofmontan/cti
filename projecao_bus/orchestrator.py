"""Facade: orquestração em `application/orchestrator`."""

from __future__ import annotations

from projecao_bus.application.orchestrator import (
    premissas_padrao,
    resolve_base_values,
    resultado_para_json,
    run_simulation,
)

__all__ = [
    "premissas_padrao",
    "resolve_base_values",
    "resultado_para_json",
    "run_simulation",
]
