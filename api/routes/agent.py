from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Request, status

from api.config import get_settings
from api.schemas import AgentQueryPayload, AgentQueryResponse
from api.services.agent_orchestrator import run_agent_query
from api.services.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/agent", tags=["agent"])
logger = logging.getLogger(__name__)


@router.post("/query", response_model=AgentQueryResponse)
async def post_agent_query(payload: AgentQueryPayload, request: Request) -> AgentQueryResponse:
    settings = get_settings()
    print(
        "[agent-debug] pergunta_recebida",
        {
            "question": payload.question,
            "question_len": len(payload.question),
            "history_len": len(payload.history),
            "agent_enabled": settings.agent_enabled,
            "openai_model": settings.openai_model,
        },
    )
    if not settings.agent_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aba agêntica desabilitada por configuração.",
        )
    identity = request.client.host if request.client else "unknown"
    if not check_rate_limit(identity):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas consultas ao agente. Aguarde alguns segundos e tente novamente.",
        )

    if len(payload.question.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pergunta inválida. Informe ao menos 3 caracteres.",
        )

    history = [item.model_dump() for item in payload.history]
    started = time.perf_counter()
    try:
        response = await run_agent_query(
            payload.question,
            payload.premissas,
            history,
            dissertative_mode=payload.dissertative_mode,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        print(
            "[agent-debug] resposta_enviada",
            {
                "status": "ok",
                "latency_ms": elapsed_ms,
                "confidence": response.confidence,
                "artifacts": len(response.artifacts),
                "warnings": len(response.warnings),
                "tools_executed": response.tools_executed,
            },
        )
        logger.info(
            "agent_query success artifacts=%s latency_ms=%s question_len=%s tools=%s",
            len(response.artifacts),
            elapsed_ms,
            len(payload.question),
            response.tools_executed,
        )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        print(
            "[agent-debug] resposta_enviada",
            {"status": "error", "latency_ms": elapsed_ms, "error": str(exc)},
        )
        logger.exception("agent_query error latency_ms=%s", elapsed_ms)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Falha ao processar consulta do agente: {exc}",
        ) from exc
