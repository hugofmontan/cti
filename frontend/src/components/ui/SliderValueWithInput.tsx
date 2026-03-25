import type { ChangeEvent } from 'react'
import styles from './SliderValueWithInput.module.css'

interface SliderValueWithInputProps {
  label: string
  value: number
  onChange: (next: number) => void
  min: number
  max: number
  step: number
  hint?: string

  /**
   * Como o valor deve ser exibido para o usuário.
   * Ex.: WACC em decimal 0.1712 com displayScale=100 vira 17.12%.
   */
  displayScale?: number
  formatDisplay?: (displayValue: number) => string

  /**
   * Escala usada no input numérico manual.
   * Por padrão igual ao displayScale.
   */
  inputScale?: number
  inputStep?: number

  /**
   * Quantidade de casas decimais para exibir no input numérico (manual).
   * Ex.: WACC decimal 0.1724 com displayScale=100 pode virar 17.199999999...
   */
  displayDecimals?: number
}

export function SliderValueWithInput({
  label,
  value,
  onChange,
  min,
  max,
  step,
  hint,
  displayScale = 100,
  formatDisplay,
  inputScale,
  inputStep,
  displayDecimals = 2,
}: SliderValueWithInputProps) {
  const scale = displayScale
  const inputScaleResolved = inputScale ?? scale

  const rawToDisplay = (raw: number) => raw * scale
  const displayToRaw = (display: number) => display / inputScaleResolved

  const clampedRaw = Math.min(max, Math.max(min, value))
  const displayValue = rawToDisplay(clampedRaw)
  const displayValueRounded = Number(displayValue.toFixed(displayDecimals))

  const displayText = formatDisplay
    ? formatDisplay(displayValueRounded)
    : `${displayValueRounded.toFixed(displayDecimals)}%`

  const inputDisplayMin = min * inputScaleResolved
  const inputDisplayMax = max * inputScaleResolved

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.value.trim() === '') return
    const typed = Number(e.target.value)
    if (!Number.isFinite(typed)) return
    const nextRaw = displayToRaw(typed)
    const nextClamped = Math.min(max, Math.max(min, nextRaw))
    onChange(nextClamped)
  }

  const numberStepResolved = inputStep ?? step * inputScaleResolved

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>{label}</div>
        <div className={styles.value}>{displayText}</div>
      </div>

      {hint ? <div className={styles.hint}>{hint}</div> : null}

      <input
        className={styles.range}
        type="range"
        min={min}
        max={max}
        step={step}
        value={clampedRaw}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={label}
      />

      <input
        className={styles.numberInput}
        type="number"
        value={displayValueRounded}
        min={inputDisplayMin}
        max={inputDisplayMax}
        step={numberStepResolved}
        onChange={handleInputChange}
        aria-label={`${label} manual`}
      />
    </div>
  )
}

