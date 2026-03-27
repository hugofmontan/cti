from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


TECHNICAL_TERMS = [
    "wacc",
    "fcff",
    "fcfe",
    "perpetuidade",
    "terminal value",
    "ev/ebitda",
    "ebitda",
    "ev ebitda",
    "ev/ebitda",
    "ebit",
    "nopat",
    "capex",
    "delta_ncg",
    "dcf",
    "beta",
    "custo de capital",
    "alavancagem",
    "múltiplo",
    "multiplo",
]


@dataclass
class SessionMemory:
    # MVP: mantemos um conjunto pequeno de campos necessários
    premise_deltas: dict[str, Any] = field(default_factory=dict)
    scenario_history: list[dict[str, Any]] = field(default_factory=list)
    reasoning_thread: list[dict[str, str]] = field(default_factory=list)
    key_numbers: dict[str, Any] = field(default_factory=dict)

    technical_level: str = "auto"  # "high" | "auto"
    technical_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def session_memory_from_dict(payload: Optional[dict[str, Any]]) -> SessionMemory:
    if not payload:
        return SessionMemory()

    mem = SessionMemory()
    mem.premise_deltas = payload.get("premise_deltas") or payload.get("premise_deltas".upper()) or mem.premise_deltas
    mem.scenario_history = payload.get("scenario_history") or mem.scenario_history
    mem.reasoning_thread = payload.get("reasoning_thread") or mem.reasoning_thread
    mem.key_numbers = payload.get("key_numbers") or mem.key_numbers
    mem.technical_level = payload.get("technical_level") or mem.technical_level
    mem.technical_signals = payload.get("technical_signals") or mem.technical_signals
    return mem


def infer_technical_level(memory: SessionMemory, text: str) -> SessionMemory:
    q = (text or "").lower()
    hits = [t for t in TECHNICAL_TERMS if t and t in q]
    if hits:
        memory.technical_signals.extend(hits)

    if len(set(memory.technical_signals)) >= 3:
        memory.technical_level = "high"
    else:
        # Conservador: se não atingiu o threshold, mantém auto.
        memory.technical_level = "auto"

    return memory


def build_memory_context(memory: SessionMemory) -> str:
    if not memory.reasoning_thread and not memory.premise_deltas:
        return ""

    lines: list[str] = ["## Fio de raciocinio (memoria)"]

    if memory.reasoning_thread:
        recent = memory.reasoning_thread[-4:]
        for i, turn in enumerate(recent, 1):
            qsum = (turn.get("question_summary") or "").strip()
            rs = (turn.get("response_summary") or "").strip()
            if qsum or rs:
                lines.append(f"{i}. {qsum} -> {rs}")

    if memory.premise_deltas:
        lines.append("")
        lines.append("## Premissas alteradas na sessao")
        for k, v in memory.premise_deltas.items():
            lines.append(f"- {k}: {v}")

    return "\n".join(lines)

