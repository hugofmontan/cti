import type { YearKey } from '../../types'
import { YEARS } from '../../utils/constants'
import { Input } from '../ui/Input'
import styles from './YearlyInputGrid.module.css'

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
  step = 1,
  min,
  max,
  hint,
}: YearlyInputGridProps) {
  return (
    <div className={styles.container}>
      {hint && <p className={styles.hint}>{hint}</p>}
      <div className={styles.grid}>
        {YEARS.map((year) => (
          <Input
            key={year}
            label={`${year} - ${label}`}
            type="number"
            step={step}
            min={min}
            max={max}
            value={values[year] ?? ''}
            onChange={(e) => onChange(year, Number(e.target.value))}
            size="sm"
          />
        ))}
      </div>
    </div>
  )
}
