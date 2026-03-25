from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional local dependency
    load_dotenv = None  # type: ignore[assignment]

_ROOT_DIR = Path(__file__).resolve().parents[1]
if load_dotenv is not None:
    load_dotenv(_ROOT_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    agent_enabled: bool
    agent_max_context_tokens: int
    agent_max_output_tokens: int
    agent_timeout_seconds: float


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        agent_enabled=_env_bool("AGENT_ENABLED", True),
        agent_max_context_tokens=int(os.getenv("AGENT_MAX_CONTEXT_TOKENS", "18000")),
        agent_max_output_tokens=int(os.getenv("AGENT_MAX_OUTPUT_TOKENS", "900")),
        agent_timeout_seconds=float(os.getenv("AGENT_TIMEOUT_SECONDS", "20")),
    )
