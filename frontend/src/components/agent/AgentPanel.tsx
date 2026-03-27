import { useCallback, useRef, useState, type KeyboardEvent } from 'react'
import type { Premissas } from '../../types'
import { useAgentQuery } from '../../hooks'
import { Alert, Button } from '../ui'
import { AgentChatThread } from './AgentChatThread'
import styles from './AgentPanel.module.css'

interface AgentPanelProps {
  premissas: Premissas | null
}

export function AgentPanel({ premissas }: AgentPanelProps) {
  const [question, setQuestion] = useState('')
  const [dissertativeMode, setDissertativeMode] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { ask, messages, loading, error } = useAgentQuery()

  const onSubmit = useCallback(async () => {
    const q = question.trim()
    if (!q || loading) return
    await ask(q, premissas, dissertativeMode)
    setQuestion('')
    textareaRef.current?.focus()
  }, [question, loading, ask, premissas, dissertativeMode])

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void onSubmit()
    }
  }

  return (
    <div className={styles.shell} aria-label="Chat com Analista IA">
      <header className={styles.header}>
        <div className={styles.headerTop}>
          <div>
            <h2 className={styles.title}>Analista IA</h2>
            <p className={styles.subtitle}>
              {dissertativeMode
                ? 'Modo dissertativo ativo: resposta textual com raciocinio aprofundado.'
                : 'Pergunte sobre projeções, BUs e valuation. As respostas usam a simulação atual.'}
            </p>
          </div>
          <label className={styles.modeToggle}>
            <input
              type="checkbox"
              checked={dissertativeMode}
              onChange={(e) => setDissertativeMode(e.target.checked)}
              disabled={loading}
              aria-label="Ativar modo dissertativo"
            />
            <span className={styles.modeToggleText}>Modo Dissertativo</span>
          </label>
        </div>
      </header>

      <div className={styles.chatArea}>
        <AgentChatThread messages={messages} loading={loading} />
      </div>

      <footer className={styles.composer}>
        {error ? (
          <Alert variant="error" title="Falha ao consultar agente">
            {error}
          </Alert>
        ) : null}
        <div className={styles.inputRow}>
          <textarea
            ref={textareaRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Digite sua pergunta… (Enter envia, Shift+Enter nova linha)"
            className={styles.textarea}
            rows={1}
            disabled={loading}
            aria-label="Mensagem para o analista"
          />
          <Button
            type="button"
            variant="primary"
            onClick={() => void onSubmit()}
            loading={loading}
            disabled={!question.trim() || loading}
            className={styles.sendBtn}
          >
            Enviar
          </Button>
        </div>
        <p className={styles.hint}>Premissas vêm do painel &quot;Dashboard&quot; — use Recalcular para atualizar o cenário.</p>
      </footer>
    </div>
  )
}
