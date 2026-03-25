import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { AgentArtifact, AgentChartArtifact, AgentTableArtifact } from '../../types'
import { CHART_COLORS } from '../../utils/constants'
import { Table } from '../ui'
import { ChartContainer } from '../charts'
import styles from './AgentArtifactRenderer.module.css'

interface AgentArtifactRendererProps {
  artifacts: AgentArtifact[]
}

function renderTable(artifact: AgentTableArtifact) {
  const columns = artifact.columns.map((column, index) => ({
    key: `col-${index}`,
    header: column,
    align: index === 0 ? 'left' as const : 'right' as const,
  }))
  const data = artifact.rows.map((row, rowIdx) =>
    row.reduce<Record<string, string | number | null>>((acc, value, colIdx) => {
      acc[`col-${colIdx}`] = value
      acc._id = rowIdx
      return acc
    }, {}),
  )

  return (
    <div className={styles.block}>
      <h4>{artifact.title}</h4>
      <Table columns={columns} data={data} keyField="_id" />
    </div>
  )
}

function renderChart(artifact: AgentChartArtifact) {
  const data = artifact.x.map((xVal, idx) => {
    const row: Record<string, string | number> = { x: xVal }
    artifact.series.forEach((series) => {
      row[series.name] = series.values[idx] ?? 0
    })
    return row
  })
  const colors = [CHART_COLORS.primary, CHART_COLORS.secondary, CHART_COLORS.tertiary, CHART_COLORS.quaternary]

  return (
    <ChartContainer title={artifact.title} height={320}>
      <ResponsiveContainer width="100%" height="100%">
        {artifact.chart_type === 'bar' ? (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="x" />
            <YAxis />
            <Tooltip />
            <Legend />
            {artifact.series.map((series, idx) => (
              <Bar key={series.name} dataKey={series.name} fill={colors[idx % colors.length]} />
            ))}
          </BarChart>
        ) : (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="x" />
            <YAxis />
            <Tooltip />
            <Legend />
            {artifact.series.map((series, idx) => (
              <Line key={series.name} type="monotone" dataKey={series.name} stroke={colors[idx % colors.length]} strokeWidth={2} />
            ))}
          </LineChart>
        )}
      </ResponsiveContainer>
    </ChartContainer>
  )
}

export function AgentArtifactRenderer({ artifacts }: AgentArtifactRendererProps) {
  if (!artifacts.length) return null
  return (
    <div className={styles.container}>
      {artifacts.map((artifact, idx) => {
        if (artifact.type === 'table') return <div key={idx}>{renderTable(artifact)}</div>
        if (artifact.type === 'chart') return <div key={idx}>{renderChart(artifact)}</div>
        return (
          <div key={idx} className={styles.kpi}>
            <strong>{artifact.title}</strong>
            <span>{artifact.value}</span>
            {artifact.subtitle ? <small>{artifact.subtitle}</small> : null}
          </div>
        )
      })}
    </div>
  )
}
