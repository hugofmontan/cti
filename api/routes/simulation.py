from fastapi import APIRouter

from projecao_bus.historical_dre import load_historical_dre_bundle
from projecao_bus.orchestrator import premissas_padrao, resultado_para_json, run_simulation

from ..schemas import SimulatePayload

router = APIRouter(prefix="/api", tags=["simulation"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/defaults")
def get_defaults() -> dict:
    return premissas_padrao()


@router.get("/historical-dre")
def get_historical_dre() -> dict:
    """Série histórica (2018–2025) a partir de `data/original/*.csv`."""
    return load_historical_dre_bundle()


@router.post("/simulate")
def post_simulate(payload: SimulatePayload) -> dict:
    resultado = run_simulation(premissas=payload.premissas)
    return resultado_para_json(resultado)
