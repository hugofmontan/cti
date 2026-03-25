import { useEffect, useState } from 'react'
import type { YearKey } from '../../types'
import { YEARS } from '../../utils/constants'
import styles from './YearlySliderGrid.module.css'

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
  const displayForRange = raw
  const display = formatValue ? formatValue(displayForRange) : String(displayForRange)

  const displayDecimals = stepToDecimals(numberInputStep ?? step * numberInputScale)
  const displayForNumberInputRounded = Number((raw * numberInputScale).toFixed(displayDecimals))

  const inputMin = min * numberInputScale
  const inputMax = max * numberInputScale
  const inputStepResolved = numberInputStep ?? step * numberInputScale

  const [inputText, setInputText] = useState<string>(String(displayForNumberInputRounded))
  const [isEditing, setIsEditing] = useState(false)

  useEffect(() => {
    if (!isEditing) {
      setInputText(String(displayForNumberInputRounded))
    }
  }, [displayForNumberInputRounded, isEditing])

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
        value={raw}
        onChange={(e) => onChangeRaw(Number(e.target.value))}
        aria-label={`${year} - ${label}`}
      />

      {showNumberInput ? (
        <input
          className={styles.numberInput}
          type="number"
          min={inputMin}
          max={inputMax}
          step={inputStepResolved}
          value={inputText}
          onFocus={() => setIsEditing(true)}
          onBlur={() => setIsEditing(false)}
          onChange={(e) => {
            const nextText = e.target.value
            setInputText(nextText)

            if (nextText.trim() === '') return
            const typedDisplay = Number(nextText)
            if (!Number.isFinite(typedDisplay)) return

            let nextRaw = typedDisplay / numberInputScale
            nextRaw = Math.min(max, Math.max(min, nextRaw))

            // Snap para o mesmo "step" do input numérico (em display units).
            const rawStep = inputStepResolved / numberInputScale
            if (rawStep > 0) {
              nextRaw = Math.round(nextRaw / rawStep) * rawStep
            }

            onChangeRaw(nextRaw)
          }}
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
  return (
    <div className={styles.container}>
      {hint ? <p className={styles.hint}>{hint}</p> : null}
      <div className={styles.grid}>
        {YEARS.map((year) => {
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

