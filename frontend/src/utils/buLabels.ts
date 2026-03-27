import { BU_NAMES } from './constants'

export function getBuLabel(buKey: string): string {
  const lower = buKey.toLowerCase()
  if (lower === 'administrativa' || lower.includes('administr')) return 'Administrativa'

  const known = (BU_NAMES as Record<string, string>)[lower] ?? (BU_NAMES as Record<string, string>)[buKey]
  return known ?? buKey
}
