"""Normaliza JSON bruto do LLM antes da validação Pydantic."""

from __future__ import annotations

from typing import Any, Literal

Confidence = Literal["high", "medium", "low"]


def _confidence_from_any(value: Any) -> Confidence:
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("high", "medium", "low"):
            return v  # type: ignore[return-value]
    if isinstance(value, (int, float)):
        x = float(value)
        if x >= 0.75:
            return "high"
        if x >= 0.45:
            return "medium"
        return "low"
    return "medium"


def _str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        return [stripped]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            s = str(item).strip()
            if s:
                out.append(s)
        return out
    return [str(value)]


def normalize_agent_response_dict(raw: dict[str, Any]) -> dict[str, Any]:
    """Repara tipos comuns que quebram AgentQueryResponse."""
    out = dict(raw)
    if "answer_markdown" not in out or not isinstance(out.get("answer_markdown"), str):
        out["answer_markdown"] = str(out.get("answer_markdown") or out.get("answer") or "").strip() or "(resposta vazia)"
    if "confidence" in out:
        out["confidence"] = _confidence_from_any(out["confidence"])
    else:
        out["confidence"] = "medium"
    out["data_used"] = _str_list(out.get("data_used"))
    out["warnings"] = _str_list(out.get("warnings"))
    arts = out.get("artifacts")
    if arts is None:
        out["artifacts"] = []
    elif not isinstance(arts, list):
        out["artifacts"] = []
    return out
