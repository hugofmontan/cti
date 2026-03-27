import { useCallback, useEffect, useRef, useState } from 'react'
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

  const clampedRaw = Math.min(max, Math.max(min, value))
  const displayValue = rawToDisplay(clampedRaw)
  const displayValueRounded = Number(displayValue.toFixed(displayDecimals))

  const displayText = formatDisplay
    ? formatDisplay(displayValueRounded)
    : `${displayValueRounded.toFixed(displayDecimals)}%`

  const inputDisplayMin = min * inputScaleResolved
  const inputDisplayMax = max * inputScaleResolved
  const numberStepResolved = inputStep ?? step * inputScaleResolved

  // --- Draft state for the number input (commit on blur) ---
  const [draft, setDraft] = useState<string>(String(displayValueRounded))
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    if (!editing) {
      setDraft(String(displayValueRounded))
    }
  }, [displayValueRounded, editing])

  const commitDraft = useCallback(() => {
    setEditing(false)
    const trimmed = draft.trim()
    if (trimmed === '' || !Number.isFinite(Number(trimmed))) return
    const typed = Number(trimmed)
    const nextRaw = typed / inputScaleResolved
    const nextClamped = Math.min(max, Math.max(min, nextRaw))
    onChange(nextClamped)
  }, [draft, inputScaleResolved, max, min, onChange])

  // --- Slider local state (commit on pointerup) ---
  const [sliderLocal, setSliderLocal] = useState(clampedRaw)
  const dragging = useRef(false)

  useEffect(() => {
    if (!dragging.current) {
      setSliderLocal(clampedRaw)
    }
  }, [clampedRaw])

  const handleSliderPointerDown = useCallback(() => {
    dragging.current = true
  }, [])

  const handleSliderChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const v = Number(e.target.value)
    setSliderLocal(v)
    if (!dragging.current) {
      onChange(v)
    }
  }, [onChange])

  const handleSliderPointerUp = useCallback(() => {
    if (dragging.current) {
      dragging.current = false
      onChange(sliderLocal)
    }
  }, [onChange, sliderLocal])

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
        value={dragging.current ? sliderLocal : clampedRaw}
        onPointerDown={handleSliderPointerDown}
        onChange={handleSliderChange}
        onPointerUp={handleSliderPointerUp}
        onPointerCancel={handleSliderPointerUp}
        aria-label={label}
      />

      <input
        className={styles.numberInput}
        type="text"
        inputMode="decimal"
        value={editing ? draft : String(displayValueRounded)}
        min={inputDisplayMin}
        max={inputDisplayMax}
        step={numberStepResolved}
        onFocus={() => setEditing(true)}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commitDraft}
        onKeyDown={(e) => { if (e.key === 'Enter') commitDraft() }}
        aria-label={`${label} manual`}
      />
    </div>
  )
}

