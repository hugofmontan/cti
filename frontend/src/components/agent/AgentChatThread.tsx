import { useEffect, useRef } from 'react'
import clsx from 'clsx'
import type { AgentMessage } from '../../types'
import { AgentAssistantMarkdown } from './AgentAssistantMarkdown'
import { AgentArtifactRenderer } from './AgentArtifactRenderer'
import styles from './AgentChatThread.module.css'

interface AgentChatThreadProps {
  messages: AgentMessage[]
  loading: boolean
}

export function AgentChatThread({ messages, loading }: AgentChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <div className={styles.thread} role="log" aria-live="polite" aria-relevant="additions">
      {messages.length === 0 && !loading ? (
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>Analista IA</p>
          <p className={styles.emptyText}>
            Faça perguntas sobre DRE, BUs, margens e valuation. As respostas usam a simulação atual
            (premissas do painel e último recálculo).
          </p>
        </div>
      ) : null}

      {messages.map((message, idx) => (
        <div
          key={`msg-${idx}-${message.role}`}
          className={clsx(styles.row, message.role === 'user' ? styles.rowUser : styles.rowAssistant)}
        >
          <div className={styles.avatar} aria-hidden="true">
            {message.role === 'user' ? 'Você' : 'IA'}
          </div>
          <div className={styles.bubbleWrap}>
            <div
              className={clsx(styles.bubble, message.role === 'user' ? styles.bubbleUser : styles.bubbleAssistant)}
            >
              {message.role === 'user' ? (
                <p className={styles.userText}>{message.content}</p>
              ) : (
                <AgentAssistantMarkdown content={message.content} />
              )}
            </div>
            {message.role === 'assistant' && message.warnings && message.warnings.length > 0 ? (
              <ul className={styles.warnings}>
                {message.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            ) : null}
            {message.role === 'assistant' && message.artifacts && message.artifacts.length > 0 ? (
              <div className={styles.artifacts}>
                <AgentArtifactRenderer artifacts={message.artifacts} />
              </div>
            ) : null}
            {message.role === 'assistant' && message.responseSource ? (
              <p className={styles.trace} title="Origem da resposta e cenário">
                {message.responseSource === 'deterministic' && 'Dados do modelo'}
                {message.responseSource === 'openai' && 'LLM + contexto'}
                {message.responseSource === 'fallback' && 'Fallback'}
                {message.intent ? ` · ${message.intent}` : ''}
                {message.scenarioId ? ` · cenário ${message.scenarioId}` : ''}
              </p>
            ) : null}
          </div>
        </div>
      ))}

      {loading ? (
        <div className={clsx(styles.row, styles.rowAssistant)}>
          <div className={styles.avatar} aria-hidden="true">
            IA
          </div>
          <div className={styles.bubbleWrap}>
            <div className={clsx(styles.bubble, styles.bubbleAssistant, styles.typing)}>
              <span className={styles.dot} />
              <span className={styles.dot} />
              <span className={styles.dot} />
            </div>
          </div>
        </div>
      ) : null}

      <div ref={bottomRef} />
    </div>
  )
}
