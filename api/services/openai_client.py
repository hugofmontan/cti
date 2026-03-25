from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.config import Settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency in local env
    OpenAI = None  # type: ignore[assignment]


class OpenAIClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = None
        if OpenAI and settings.openai_api_key:
            self._client = OpenAI(api_key=settings.openai_api_key, timeout=settings.agent_timeout_seconds)

    def is_enabled(self) -> bool:
        return bool(self._settings.agent_enabled and self._client)

    def status(self) -> dict[str, Any]:
        return {
            "agent_enabled_flag": self._settings.agent_enabled,
            "has_openai_sdk": OpenAI is not None,
            "has_api_key": bool(self._settings.openai_api_key),
            "client_initialized": self._client is not None,
            "model": self._settings.openai_model,
        }

    def generate_structured(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("OpenAI indisponivel: defina OPENAI_API_KEY e instale pacote openai.")
        print(
            "[agent-debug] openai_request",
            {
                "model": self._settings.openai_model,
                "question_len": len(prompt),
                "scenario_id": context.get("meta_context", {}).get("scenario_id"),
                "has_markdown_context": bool(context.get("system_context_markdown")),
            },
        )

        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "agent_system_prompt.md"
        system_prompt = prompt_path.read_text(encoding="utf-8")

        response = self._client.chat.completions.create(
            model=self._settings.openai_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Pergunta do usuario:\n{prompt}\n\n"
                        "Contexto estruturado em markdown (fonte principal):\n"
                        f"{context.get('system_context_markdown', '')}\n\n"
                        "Metadados auxiliares em JSON:\n"
                        f"{json.dumps({k: v for k, v in context.items() if k != 'system_context_markdown'}, ensure_ascii=True)}\n\n"
                        "Retorne JSON com campos: answer_markdown, confidence, artifacts, data_used, warnings.\n"
                        "Use artifacts apenas quando o usuario pedir explicitamente grafico, tabela ou visualizacao."
                    ),
                },
            ],
            max_tokens=self._settings.agent_max_output_tokens,
        )
        text = response.choices[0].message.content or ""
        print(
            "[agent-debug] openai_response",
            {"content_len": len(text), "finish_reason": response.choices[0].finish_reason},
        )
        return json.loads(text)
