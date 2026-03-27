import { useCallback, useEffect, useState } from 'react'
import clsx from 'clsx'
import styles from './Input.module.css'

interface PercentInputProps {
  label?: string
  hint?: string
  /** Raw decimal value from the model (e.g. 0.0958 for 9.58%). */
  rawValue: number
  /** Callback receiving the raw decimal (e.g. 0.0958). */
  onChange: (nextRaw: number) => void
  displayScale?: number
  displayDecimals?: number
  /** Min / max / step in *display* units (e.g. 0–30 for a 0–30% range). */
  min?: number
  max?: number
  step?: number
  size?: 'sm' | 'md'
  className?: string
}

export function PercentInput({
  label,
  hint,
  rawValue,
  onChange,
  displayScale = 100,
  displayDecimals = 2,
  min,
  max,
  step,
  size = 'md',
  className,
}: PercentInputProps) {
  const displayValue = Number((rawValue * displayScale).toFixed(displayDecimals))

  const [draft, setDraft] = useState(String(displayValue))
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    if (!editing) {
      setDraft(String(displayValue))
    }
  }, [displayValue, editing])

  const commitDraft = useCallback(() => {
    setEditing(false)
    const trimmed = draft.trim()
    if (trimmed === '' || !Number.isFinite(Number(trimmed))) return
    let display = Number(trimmed)
    if (min != null) display = Math.max(min, display)
    if (max != null) display = Math.min(max, display)
    if (step != null && step > 0) {
      display = Math.round(display / step) * step
    }
    onChange(display / displayScale)
  }, [draft, min, max, step, displayScale, onChange])

  const inputId = label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className={clsx(styles.field, className)}>
      {label && (
        <label htmlFor={inputId} className={styles.label}>
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={clsx(styles.input, styles[size])}
        type="text"
        inputMode="decimal"
        value={editing ? draft : String(displayValue)}
        onFocus={() => setEditing(true)}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commitDraft}
        onKeyDown={(e) => { if (e.key === 'Enter') commitDraft() }}
      />
      {hint && <span className={styles.hint}>{hint}</span>}
    </div>
  )
}
