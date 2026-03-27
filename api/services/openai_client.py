"""
Agent v2 — OpenAI Client com tool-use loop.

Substitui o client v1 (generate_structured, sem tools) por
generate_with_tools (loop automático de tool calls).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable

from api.config import Settings

logger = logging.getLogger(__name__)

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore[assignment,misc]

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent_system_prompt.md"
DISSERTATIVE_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent_dissertative_prompt.md"

MAX_TOOL_ROUNDS = 5


class OpenAIClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: Any = None
        if AsyncOpenAI and settings.openai_api_key:
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=settings.agent_timeout_seconds,
            )

    def is_enabled(self) -> bool:
        return bool(self._settings.agent_enabled and self._client)

    def status(self) -> dict[str, Any]:
        return {
            "agent_enabled_flag": self._settings.agent_enabled,
            "has_openai_sdk": AsyncOpenAI is not None,
            "has_api_key": bool(self._settings.openai_api_key),
            "client_initialized": self._client is not None,
            "model": self._settings.openai_model,
        }

    async def generate_with_tools(
        self,
        question: str,
        context: dict[str, Any],
        tools: list[dict],
        tool_executor: Callable[[str, dict], dict],
        dissertative_mode: bool = False,
    ) -> dict[str, Any]:
        """
        Chamada ao LLM com tool-use loop.

        1. Envia pergunta + contexto + tools
        2. Se LLM faz tool calls, executa no backend
        3. Retorna resultados ao LLM
        4. Repete até LLM retornar resposta final (ou max rounds)

        Retorna dict com answer_markdown, confidence, data_used, warnings.
        Também popula context["_tools_executed"] com lista de tools chamadas.
        """
        if not self._client:
            raise RuntimeError("OpenAI indisponível: defina OPENAI_API_KEY e instale pacote openai.")

        prompt_path = DISSERTATIVE_PROMPT_PATH if dissertative_mode else SYSTEM_PROMPT_PATH
        system_prompt = prompt_path.read_text(encoding="utf-8")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Inserir histórico de sessão como mensagens (antes da pergunta atual)
        for entry in context.get("session", {}).get("history_summary", []):
            role = entry.get("role", "user")
            content = entry.get("content_preview", "")
            if content and role in ("user", "assistant"):
                messages.append({"role": role, "content": content})

        messages.append({
            "role": "user",
            "content": _build_user_message(question, context),
        })

        model = self._settings.openai_model
        is_gpt5 = str(model).startswith("gpt-5")
        max_tokens_value = self._settings.agent_max_output_tokens
        if is_gpt5 and dissertative_mode:
            # Dissertative mode asks for longer analytical answers; GPT-5 can spend
            # a large portion of completion budget on reasoning before final text.
            max_tokens_value = max(max_tokens_value, 2600)

        tools_executed: list[str] = []
        empty_content_retry_used = False

        for round_num in range(MAX_TOOL_ROUNDS):
            request_kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
                "temperature": 0.2,
            }

            if is_gpt5:
                request_kwargs["max_completion_tokens"] = max_tokens_value
            else:
                request_kwargs["max_tokens"] = max_tokens_value

            logger.info(
                "LLM call round=%d model=%s messages=%d",
                round_num, model, len(messages),
            )

            response = await self._client.chat.completions.create(**request_kwargs)

            choice = response.choices[0]
            message = choice.message

            if not message.tool_calls:
                final_content = _coerce_message_content(message.content).strip()
                if not final_content and not empty_content_retry_used:
                    empty_content_retry_used = True
                    logger.warning(
                        "LLM returned empty assistant content without tool calls; retrying once with explicit JSON instruction."
                    )
                    messages.append(_message_to_dict(message))
                    messages.append({
                        "role": "user",
                        "content": (
                            "Sua última resposta veio vazia. "
                            "Retorne agora APENAS um JSON válido com as chaves "
                            "`answer_markdown`, `confidence`, `data_used` e `warnings`."
                        ),
                    })
                    continue
                context["_tools_executed"] = tools_executed
                return _parse_final_response(final_content)

            # Processar tool calls
            messages.append(_message_to_dict(message))

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                logger.info(
                    "Tool call [round %d]: %s(%s)",
                    round_num, func_name,
                    json.dumps(func_args, ensure_ascii=False)[:200],
                )

                tools_executed.append(func_name)

                try:
                    result = tool_executor(func_name, func_args)
                except Exception as e:
                    logger.error("Erro executando tool %s: %s", func_name, e)
                    result = {"error": str(e)}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

        logger.warning("Tool-use loop esgotou %d rounds", MAX_TOOL_ROUNDS)
        context["_tools_executed"] = tools_executed

        last_content = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
                last_content = msg["content"]
                break
        if not last_content:
            last_content = messages[-1].get("content", "{}") if isinstance(messages[-1], dict) else "{}"

        return _parse_final_response(last_content)


def _message_to_dict(message: Any) -> dict[str, Any]:
    """Converte um ChatCompletionMessage para dict serializable."""
    d: dict[str, Any] = {
        "role": message.role,
        "content": _coerce_message_content(message.content),
    }
    if message.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]
    return d


def _build_user_message(question: str, context: dict) -> str:
    current_state = context.get("current_state", {})

    parts = [
        f"## Pergunta\n{question}",
        f"\n## Cenário Atual (scenario_id: {current_state.get('scenario_id', 'N/A')})",
        "\n### Premissas",
        f"```json\n{json.dumps(current_state.get('premissas_atuais', {}), indent=2, ensure_ascii=False)}\n```",
        "\n### Consolidado (projeção)",
        f"```json\n{json.dumps(current_state.get('consolidado', {}), indent=2, ensure_ascii=False)}\n```",
        "\n### Por BU (2026 vs 2030)",
        f"```json\n{json.dumps(current_state.get('por_bu', {}), indent=2, ensure_ascii=False)}\n```",
        "\n### DCF",
        f"```json\n{json.dumps(current_state.get('dcf', {}), indent=2, ensure_ascii=False)}\n```",
        "\n### Referência de domínio (fonte única — use só estes dados para BUs, métricas, ranges e lógica do motor)",
        f"```json\n{json.dumps(context.get('domain_reference', {}), indent=2, ensure_ascii=False)}\n```",
    ]

    return "\n".join(parts)


def _coerce_message_content(content: Any) -> str:
    """Normaliza formatos de content retornados pelo SDK para string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    pieces.append(text)
            elif isinstance(item, str):
                pieces.append(item)
        return "\n".join(pieces)
    return ""


def _parse_final_response(content: str) -> dict[str, Any]:
    """
    Parseia a resposta final do LLM.
    Robustez contra JSON mal-formado.
    """
    if not content:
        return {
            "answer_markdown": "Sem resposta do modelo.",
            "confidence": "low",
            "data_used": [],
            "warnings": ["Resposta vazia"],
        }

    # Tentar parse direto
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Remover code fences
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Extrair primeiro {...}
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(cleaned[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {
        "answer_markdown": content,
        "confidence": "low",
        "data_used": [],
        "warnings": ["Resposta não veio em JSON válido"],
    }
