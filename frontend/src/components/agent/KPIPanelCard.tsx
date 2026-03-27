import type { AgentKPIPanelArtifact } from '../../types'
import { Card, CardGroup } from '../ui'

interface KPIPanelCardProps {
  artifact: AgentKPIPanelArtifact
}

export function KPIPanelCard({ artifact }: KPIPanelCardProps) {
  return (
    <div>
      {artifact.title ? <h4 style={{ marginBottom: 'var(--spacing-2)' }}>{artifact.title}</h4> : null}
      <CardGroup columns={4}>
        {artifact.items.map((item, idx) => (
          <Card
            key={`${item.title}-${idx}`}
            label={item.title}
            value={item.value}
            subValue={item.subtitle ?? undefined}
            variant={artifact.highlight_index === idx ? 'highlight' : 'default'}
          />
        ))}
      </CardGroup>
    </div>
  )
}

