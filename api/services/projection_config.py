"""Anos projetados alinhados ao `year_config` ativo do motor."""

from __future__ import annotations

from projecao_bus.year_config import get_projected_years


def get_projection_years() -> list[int]:
    return list(get_projected_years())
