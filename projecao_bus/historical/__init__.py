"""
Camada histórica: bundle DRE + (futuro) base_year_extractor após migração de paths.
Hoje o carregamento principal permanece em ``projecao_bus.historical_dre`` por compatibilidade.
"""

from ..historical_dre import load_historical_dre_bundle

__all__ = ["load_historical_dre_bundle"]
