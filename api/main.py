"""
API FastAPI: premissas e simulação consolidada + DCF.
Executar a partir da raiz do repositório:
  uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path

# Raiz do repositório no path para `import projecao_bus`
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from projecao_bus.orchestrator import premissas_padrao, resultado_para_json, run_simulation

app = FastAPI(title="Projeções calculadora", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulatePayload(BaseModel):
    premissas: dict | None = None


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/defaults")
def get_defaults():
    return premissas_padrao()


@app.post("/api/simulate")
def post_simulate(payload: SimulatePayload):
    resultado = run_simulation(premissas=payload.premissas)
    return resultado_para_json(resultado)
