import { useCallback, useRef, useState } from 'react'
import type { AgentMessage, AgentQueryResponse, Premissas } from '../types'
import { API_BASE_URL } from '../utils/constants'

interface UseAgentQueryReturn {
  messages: AgentMessage[]
  loading: boolean
  error: string | null
  lastResponse: AgentQueryResponse | null
  ask: (question: string, premissas: Premissas | null) => Promise<void>
}

export function useAgentQuery(): UseAgentQueryReturn {
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastResponse, setLastResponse] = useState<AgentQueryResponse | null>(null)
  const messagesRef = useRef<AgentMessage[]>([])

  const ask = useCallback(async (question: string, premissas: Premissas | null) => {
    const trimmed = question.trim()
    if (!trimmed) return

    const userMessage: AgentMessage = { role: 'user', content: trimmed }
    const prior = messagesRef.current
    const historyForApi = prior.slice(-10).map(({ role, content }) => ({ role, content }))

    messagesRef.current = [...prior, userMessage]
    setMessages([...messagesRef.current])
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/agent/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: trimmed,
          premissas,
          history: historyForApi,
          locale: 'pt-BR',
        }),
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(text)
      }

      const data: AgentQueryResponse = await response.json()
      setLastResponse(data)
      const assistantMessage: AgentMessage = {
        role: 'assistant',
        content: data.answer_markdown,
        artifacts: data.artifacts?.length ? data.artifacts : undefined,
        warnings: data.warnings?.length ? data.warnings : undefined,
        responseSource: data.response_source,
        intent: data.intent ?? undefined,
        scenarioId: data.scenario_id ?? undefined,
        validationRepaired: data.validation_repaired,
      }
      messagesRef.current = [...messagesRef.current, assistantMessage]
      setMessages([...messagesRef.current])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Falha ao consultar agente')
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    messages,
    loading,
    error,
    lastResponse,
    ask,
  }
}
