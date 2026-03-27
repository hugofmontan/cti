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
              className={clsx(
                styles.bubble,
                message.role === 'user' ? styles.bubbleUser : styles.bubbleAssistant,
                message.role === 'assistant' && message.dissertativeMode ? styles.bubbleAssistantWide : null,
              )}
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
            {message.role === 'assistant' && message.dataLineage && message.dataLineage.length > 0 ? (
              <details style={{ marginTop: 'var(--spacing-2)' }}>
                <summary style={{ cursor: 'pointer', color: 'var(--color-neutral-600)', fontWeight: 600 }}>
                  Rastreabilidade (data lineage)
                </summary>
                <ul style={{ margin: 'var(--spacing-2) 0 0', paddingLeft: '18px', color: 'var(--color-neutral-700)' }}>
                  {message.dataLineage.map((item, i) => (
                    <li key={`${item.label}-${i}`} style={{ marginBottom: 6 }}>
                      <span style={{ fontWeight: 600 }}>{item.label}:</span> {item.value}
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-neutral-500)' }}>
                        fonte: {item.source}
                        {item.scenario_id ? ` · cenário ${item.scenario_id}` : ''}
                      </div>
                    </li>
                  ))}
                </ul>
              </details>
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
