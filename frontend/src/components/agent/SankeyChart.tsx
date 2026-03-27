import { useRef, useEffect, useState, useMemo, useCallback } from 'react'
import {
  sankey as d3Sankey,
  sankeyLinkHorizontal,
  sankeyJustify,
} from 'd3-sankey'
import type { SankeyGraph, SankeyNode as D3SankeyNode, SankeyLink as D3SankeyLink } from 'd3-sankey'
import type { AgentSankeyArtifact } from '../../types'
import { fmtBRL, fmtMillions } from '../../utils/formatters'
import styles from './SankeyChart.module.css'

interface SankeyChartProps {
  artifact: AgentSankeyArtifact
}

interface SNode {
  id: string
  label: string
  color: string
}

interface SLink {
  source: string
  target: string
  value: number
  label?: string
}

type LayoutNode = D3SankeyNode<SNode, SLink>
type LayoutLink = D3SankeyLink<SNode, SLink>

const NODE_COLORS: Record<string, string> = {
  receita_bruta: '#2563eb',
  receita_liquida: '#60a5fa',
  mc1: '#059669',
  mc2: '#34d399',
  ebitda: '#059669',
  ebit: '#d97706',
  lair: '#d97706',
  lucro_liquido: '#16a34a',
  // drains
  impostos: '#94a3b8',
  custos_diretos: '#94a3b8',
  rem_socios: '#94a3b8',
  desp_adm: '#94a3b8',
  da: '#94a3b8',
  resultado_fin: '#94a3b8',
  irpj_csll: '#f87171',
  // BU composition
  fopm: '#2563eb',
  renovacao: '#059669',
  ams: '#d97706',
  venda_sw: '#7c3aed',
  data_science: '#dc2626',
  custos_totais: '#94a3b8',
  abaixo_ebitda: '#94a3b8',
}

function getNodeColor(node: { id: string; color?: string }): string {
  if (node.color) return node.color
  return NODE_COLORS[node.id] ?? '#64748b'
}

const CHART_HEIGHT = 480
const PADDING = { top: 24, right: 170, bottom: 24, left: 170 }
const NODE_WIDTH = 18
const NODE_PADDING = 20

interface TooltipState {
  visible: boolean
  x: number
  y: number
  label: string
  value: number
  pctOfSource?: number
}

export function SankeyChart({ artifact }: SankeyChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(700)
  const [hoveredLinkIdx, setHoveredLinkIdx] = useState<number | null>(null)
  const [tooltip, setTooltip] = useState<TooltipState>({ visible: false, x: 0, y: 0, label: '', value: 0 })

  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width
      if (w > 0) setWidth(Math.max(500, w))
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  const layout = useMemo((): SankeyGraph<SNode, SLink> | null => {
    if (!artifact.nodes.length || !artifact.links.length) return null

    const nodes: SNode[] = artifact.nodes.map((n) => ({
      id: n.id,
      label: n.label,
      color: getNodeColor(n),
    }))

    const nodeIds = new Set(nodes.map((n) => n.id))
    const links: SLink[] = artifact.links
      .filter((l) => nodeIds.has(l.source) && nodeIds.has(l.target) && l.value > 0)
      .map((l) => ({ ...l }))

    if (!links.length) return null

    try {
      const generator = d3Sankey<SNode, SLink>()
        .nodeId((d) => d.id)
        .nodeWidth(NODE_WIDTH)
        .nodePadding(NODE_PADDING)
        .nodeAlign(sankeyJustify)
        .extent([
          [PADDING.left, PADDING.top],
          [width - PADDING.right, CHART_HEIGHT - PADDING.bottom],
        ])

      return generator({
        nodes: nodes.map((n) => ({ ...n })),
        links: links.map((l) => ({ ...l })),
      })
    } catch {
      return null
    }
  }, [artifact, width])

  const linkPathGen = useMemo(() => sankeyLinkHorizontal(), [])

  const handleLinkEnter = useCallback(
    (e: React.MouseEvent<SVGPathElement>, link: LayoutLink, idx: number) => {
      setHoveredLinkIdx(idx)
      const rect = containerRef.current?.getBoundingClientRect()
      if (!rect) return

      const sourceNode = link.source as LayoutNode
      const targetNode = link.target as LayoutNode
      const sourceValue = sourceNode.value ?? 1
      const pct = sourceValue > 0 ? link.value / sourceValue : 0

      setTooltip({
        visible: true,
        x: e.clientX - rect.left + 12,
        y: e.clientY - rect.top - 10,
        label: `${sourceNode.label} → ${targetNode.label}`,
        value: link.value,
        pctOfSource: pct,
      })
    },
    [],
  )

  const handleLinkLeave = useCallback(() => {
    setHoveredLinkIdx(null)
    setTooltip((t) => ({ ...t, visible: false }))
  }, [])

  const handleNodeEnter = useCallback(
    (e: React.MouseEvent<SVGRectElement>, node: LayoutNode) => {
      const rect = containerRef.current?.getBoundingClientRect()
      if (!rect) return
      setTooltip({
        visible: true,
        x: e.clientX - rect.left + 12,
        y: e.clientY - rect.top - 10,
        label: node.label,
        value: node.value ?? 0,
      })
    },
    [],
  )

  const handleNodeLeave = useCallback(() => {
    setTooltip((t) => ({ ...t, visible: false }))
  }, [])

  if (!layout) {
    return (
      <div className={styles.container}>
        <h4 className={styles.title}>{artifact.title}</h4>
        <p className={styles.subtitle}>Dados insuficientes para gerar o Sankey.</p>
      </div>
    )
  }

  const yearBuLabel = [
    artifact.year ? `Ano ${artifact.year}` : null,
    artifact.bu && artifact.bu !== 'consolidado'
      ? artifact.bu.toUpperCase()
      : artifact.bu === 'consolidado'
        ? 'Consolidado'
        : null,
  ]
    .filter(Boolean)
    .join(' — ')

  return (
    <div ref={containerRef} className={styles.container}>
      <h4 className={styles.title}>{artifact.title}</h4>
      {yearBuLabel && <p className={styles.subtitle}>{yearBuLabel}</p>}

      <div className={styles.svgWrap}>
        <svg
          className={styles.svg}
          width={width}
          height={CHART_HEIGHT}
          viewBox={`0 0 ${width} ${CHART_HEIGHT}`}
        >
          <defs>
            {layout.links.map((link, idx) => {
              const src = link.source as LayoutNode
              const tgt = link.target as LayoutNode
              return (
                <linearGradient
                  key={`grad-${idx}`}
                  id={`sankey-grad-${idx}`}
                  gradientUnits="userSpaceOnUse"
                  x1={src.x1}
                  x2={tgt.x0}
                >
                  <stop offset="0%" stopColor={src.color} />
                  <stop offset="100%" stopColor={tgt.color} />
                </linearGradient>
              )
            })}
          </defs>

          {/* Links */}
          <g>
            {layout.links.map((link, idx) => {
              const d = linkPathGen(link as any)
              if (!d) return null
              const isHovered = hoveredLinkIdx === idx
              const isDimmed = hoveredLinkIdx !== null && !isHovered
              const opacity = isHovered ? 0.7 : isDimmed ? 0.08 : 0.35

              return (
                <path
                  key={`link-${idx}`}
                  d={d}
                  fill="none"
                  stroke={`url(#sankey-grad-${idx})`}
                  strokeWidth={Math.max(1, link.width ?? 1)}
                  strokeOpacity={opacity}
                  style={{ transition: 'stroke-opacity 200ms ease' }}
                  onMouseEnter={(e) => handleLinkEnter(e, link, idx)}
                  onMouseMove={(e) => {
                    const rect = containerRef.current?.getBoundingClientRect()
                    if (!rect) return
                    setTooltip((t) => ({
                      ...t,
                      x: e.clientX - rect.left + 12,
                      y: e.clientY - rect.top - 10,
                    }))
                  }}
                  onMouseLeave={handleLinkLeave}
                />
              )
            })}
          </g>

          {/* Nodes */}
          <g>
            {layout.nodes.map((node) => {
              const x0 = node.x0 ?? 0
              const y0 = node.y0 ?? 0
              const x1 = node.x1 ?? 0
              const y1 = node.y1 ?? 0
              const h = y1 - y0
              const w = x1 - x0

              const isLeftColumn = x0 <= PADDING.left + NODE_WIDTH + 1
              const labelX = isLeftColumn ? x0 - 8 : x1 + 8
              const labelAnchor = isLeftColumn ? 'end' : 'start'
              const labelY = y0 + h / 2

              return (
                <g key={node.id}>
                  <rect
                    x={x0}
                    y={y0}
                    width={w}
                    height={h}
                    rx={3}
                    fill={node.color}
                    fillOpacity={0.9}
                    onMouseEnter={(e) => handleNodeEnter(e, node)}
                    onMouseLeave={handleNodeLeave}
                    style={{ cursor: 'default' }}
                  />
                  <text
                    x={labelX}
                    y={labelY - 6}
                    textAnchor={labelAnchor}
                    dominantBaseline="auto"
                    style={{
                      fontSize: 12,
                      fontFamily: 'var(--font-family-sans)',
                      fontWeight: 600,
                      fill: 'var(--color-neutral-700)',
                    }}
                  >
                    {node.label}
                  </text>
                  <text
                    x={labelX}
                    y={labelY + 8}
                    textAnchor={labelAnchor}
                    dominantBaseline="auto"
                    style={{
                      fontSize: 11,
                      fontFamily: 'var(--font-family-mono)',
                      fill: 'var(--color-neutral-500)',
                    }}
                  >
                    {fmtMillions(node.value ?? 0)}
                  </text>
                </g>
              )
            })}
          </g>
        </svg>
      </div>

      {/* Tooltip */}
      <div
        className={`${styles.tooltip} ${tooltip.visible ? styles.tooltipVisible : ''}`}
        style={{ left: tooltip.x, top: tooltip.y }}
      >
        <div className={styles.tooltipLabel}>{tooltip.label}</div>
        <div>
          <span className={styles.tooltipValue}>{fmtBRL(tooltip.value)}</span>
          {tooltip.pctOfSource != null && (
            <span className={styles.tooltipPct}>
              ({(tooltip.pctOfSource * 100).toFixed(1)}% da origem)
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
