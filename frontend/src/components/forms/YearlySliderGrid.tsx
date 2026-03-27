import { useCallback, useEffect, useRef, useState } from 'react'
import type { YearKey } from '../../types'
import styles from './YearlySliderGrid.module.css'
import { useYearConfig } from '../../contexts/YearConfigContext'

function stepToDecimals(step: number) {
  const s = String(step)
  if (!s.includes('.')) return 0
  return Math.max(0, s.split('.')[1]?.length ?? 0)
}

interface YearlySliderItemProps {
  year: YearKey
  label: string
  raw: number
  onChangeRaw: (nextRaw: number) => void
  min: number
  max: number
  step: number
  hint?: string
  formatValue?: (value: number) => string
  showNumberInput: boolean
  numberInputScale: number
  numberInputStep?: number
}

function YearlySliderItem({
  year,
  label,
  raw,
  onChangeRaw,
  min,
  max,
  step,
  formatValue,
  showNumberInput,
  numberInputScale,
  numberInputStep,
}: YearlySliderItemProps) {
  const display = formatValue ? formatValue(raw) : String(raw)

  const displayDecimals = stepToDecimals(numberInputStep ?? step * numberInputScale)
  const displayForNumberInputRounded = Number((raw * numberInputScale).toFixed(displayDecimals))

  const inputStepResolved = numberInputStep ?? step * numberInputScale

  // --- Draft string for the number input (commit on blur / Enter) ---
  const [draft, setDraft] = useState<string>(String(displayForNumberInputRounded))
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    if (!editing) {
      setDraft(String(displayForNumberInputRounded))
    }
  }, [displayForNumberInputRounded, editing])

  const commitDraft = useCallback(() => {
    setEditing(false)
    const trimmed = draft.trim()
    if (trimmed === '' || !Number.isFinite(Number(trimmed))) return

    let nextRaw = Number(trimmed) / numberInputScale
    nextRaw = Math.min(max, Math.max(min, nextRaw))

    const rawStep = inputStepResolved / numberInputScale
    if (rawStep > 0) {
      nextRaw = Math.round(nextRaw / rawStep) * rawStep
    }

    onChangeRaw(nextRaw)
  }, [draft, numberInputScale, max, min, inputStepResolved, onChangeRaw])

  // --- Slider local state (commit on pointerup) ---
  const [sliderLocal, setSliderLocal] = useState(raw)
  const dragging = useRef(false)

  useEffect(() => {
    if (!dragging.current) {
      setSliderLocal(raw)
    }
  }, [raw])

  const handleSliderPointerDown = useCallback(() => {
    dragging.current = true
  }, [])

  const handleSliderChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const v = Number(e.target.value)
    setSliderLocal(v)
    if (!dragging.current) {
      onChangeRaw(v)
    }
  }, [onChangeRaw])

  const handleSliderPointerUp = useCallback(() => {
    if (dragging.current) {
      dragging.current = false
      onChangeRaw(sliderLocal)
    }
  }, [onChangeRaw, sliderLocal])

  return (
    <div className={styles.item}>
      <div className={styles.meta}>
        <span className={styles.year}>{year}</span>
        <span className={styles.label}>{label}</span>
      </div>
      <div className={styles.value}>{display}</div>

      <input
        className={styles.range}
        type="range"
        min={min}
        max={max}
        step={step}
        value={dragging.current ? sliderLocal : raw}
        onPointerDown={handleSliderPointerDown}
        onChange={handleSliderChange}
        onPointerUp={handleSliderPointerUp}
        onPointerCancel={handleSliderPointerUp}
        aria-label={`${year} - ${label}`}
      />

      {showNumberInput ? (
        <input
          className={styles.numberInput}
          type="text"
          inputMode="decimal"
          value={editing ? draft : String(displayForNumberInputRounded)}
          onFocus={() => setEditing(true)}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commitDraft}
          onKeyDown={(e) => { if (e.key === 'Enter') commitDraft() }}
          aria-label={`${year} - ${label} manual`}
        />
      ) : null}
    </div>
  )
}

interface YearlySliderGridProps {
  label: string
  values: Record<YearKey, number>
  onChange: (year: YearKey, value: number) => void
  min: number
  max: number
  step: number
  hint?: string
  formatValue?: (value: number) => string
  showNumberInput?: boolean
  /**
   * Escala usada apenas para o input numérico (ex.: ociosidade decimal 0.15 vira 15 no input).
   * O modelo continua guardando o valor em "raw" (decimal).
   */
  numberInputScale?: number
  numberInputStep?: number
}

export function YearlySliderGrid({
  label,
  values,
  onChange,
  min,
  max,
  step,
  hint,
  formatValue,
  showNumberInput = true,
  numberInputScale = 1,
  numberInputStep,
}: YearlySliderGridProps) {
  const { projectedYears } = useYearConfig()
  const years = projectedYears.map((y) => String(y) as YearKey)
  return (
    <div className={styles.container}>
      {hint ? <p className={styles.hint}>{hint}</p> : null}
      <div className={styles.grid}>
        {years.map((year) => {
          const raw = values[year] ?? 0
          return (
            <YearlySliderItem
              key={year}
              year={year}
              label={label}
              raw={raw}
              onChangeRaw={(nextRaw) => onChange(year, nextRaw)}
              min={min}
              max={max}
              step={step}
              formatValue={formatValue}
              showNumberInput={showNumberInput}
              numberInputScale={numberInputScale}
              numberInputStep={numberInputStep}
            />
          )
        })}
      </div>
    </div>
  )
}

