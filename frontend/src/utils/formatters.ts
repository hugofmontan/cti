/**
 * Format number as Brazilian Real (BRL) currency
 */
export function fmtBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  }).format(value)
}

/**
 * Format number as Brazilian Real with decimal places
 */
export function fmtBRLFull(value: number, decimals = 2): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

/**
 * Format decimal as percentage (0.15 -> "15.00%")
 */
export function fmtPct(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * Format number with thousands separator (Brazilian format)
 */
export function fmtNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

/**
 * Format large numbers in millions (for charts)
 */
export function fmtMillions(value: number, decimals = 1): string {
  return `${(value / 1_000_000).toFixed(decimals)}M`
}

/**
 * Format large numbers in thousands (for charts)
 */
export function fmtThousands(value: number, decimals = 0): string {
  return `${(value / 1_000).toFixed(decimals)}K`
}

/**
 * Format value conditionally with color class based on positive/negative
 */
export function getValueColorClass(value: number): string {
  if (value > 0) return 'text-positive'
  if (value < 0) return 'text-negative'
  return ''
}

/**
 * Parse number input, handling empty strings and NaN
 */
export function parseNumberInput(value: string, fallback = 0): number {
  const parsed = Number(value)
  return isNaN(parsed) ? fallback : parsed
}
