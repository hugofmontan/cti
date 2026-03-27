import { useCallback, useEffect, useState } from 'react'
import type { YearKey } from '../../types'
import { Input } from '../ui/Input'
import styles from './YearlyInputGrid.module.css'
import { useYearConfig } from '../../contexts/YearConfigContext'

interface YearlyInputItemProps {
  year: YearKey
  label: string
  value: number
  onChange: (v: number) => void
  min?: number
  max?: number
}

function YearlyInputItem({ year, label, value, onChange, min, max }: YearlyInputItemProps) {
  const [draft, setDraft] = useState(String(value))
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    if (!editing) {
      setDraft(String(value))
    }
  }, [value, editing])

  const commitDraft = useCallback(() => {
    setEditing(false)
    const trimmed = draft.trim()
    if (trimmed === '' || !Number.isFinite(Number(trimmed))) return
    let v = Number(trimmed)
    if (min != null) v = Math.max(min, v)
    if (max != null) v = Math.min(max, v)
    onChange(v)
  }, [draft, min, max, onChange])

  return (
    <Input
      label={`${year} - ${label}`}
      type="text"
      inputMode="decimal"
      value={editing ? draft : String(value)}
      onFocus={() => setEditing(true)}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commitDraft}
      onKeyDown={(e) => { if (e.key === 'Enter') commitDraft() }}
      size="sm"
    />
  )
}

interface YearlyInputGridProps {
  label: string
  values: Record<YearKey, number>
  onChange: (year: YearKey, value: number) => void
  step?: number
  min?: number
  max?: number
  hint?: string
}

export function YearlyInputGrid({
  label,
  values,
  onChange,
  min,
  max,
  hint,
}: YearlyInputGridProps) {
  const { projectedYears } = useYearConfig()
  const years = projectedYears.map((y) => String(y) as YearKey)
  return (
    <div className={styles.container}>
      {hint && <p className={styles.hint}>{hint}</p>}
      <div className={styles.grid}>
        {years.map((year) => (
          <YearlyInputItem
            key={year}
            year={year}
            label={label}
            value={values[year] ?? 0}
            onChange={(v) => onChange(year, v)}
            min={min}
            max={max}
          />
        ))}
      </div>
    </div>
  )
}
