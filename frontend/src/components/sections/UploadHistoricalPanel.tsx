import { useMemo, useState, type ChangeEvent } from 'react'
import { Alert, Button, Input } from '../ui'
import { CsvUploadGuide } from './CsvUploadGuide'
import styles from './UploadHistoricalPanel.module.css'
import type { HistoricalDREBundle } from '../../hooks/useHistoricalDRE'
import { API_BASE_URL, HISTORICAL_YEARS, HISTORICAL_YEAR_END } from '../../utils/constants'

type UploadFieldKey = 'consolidado' | 'fopm' | 'renovacao' | 'ams' | 'venda_sw' | 'data_science' | 'administrativa'
type OptionalUploadFieldKey = 'balanco_patrimonial'

export interface UploadHistoricalPanelProps {
  historical: HistoricalDREBundle | null
  loadingHistorical: boolean
  loadingSimulation: boolean
  onReloadHistorical: () => Promise<void>
  onRunSimulation: () => Promise<void>
}

const FILE_SPECS: Array<{ key: UploadFieldKey; label: string }> = [
  { key: 'consolidado', label: 'Consolidado' },
  { key: 'fopm', label: 'FOPM' },
  { key: 'renovacao', label: 'Renovacao' },
  { key: 'ams', label: 'AMS' },
  { key: 'venda_sw', label: 'Venda SW' },
  { key: 'data_science', label: 'Data Science' },
  { key: 'administrativa', label: 'Administrativa' },
]
const OPTIONAL_FILE_SPECS: Array<{ key: OptionalUploadFieldKey; label: string }> = [
  { key: 'balanco_patrimonial', label: 'Balanço Patrimonial (opcional)' },
]

export function UploadHistoricalPanel({
  historical,
  loadingHistorical,
  loadingSimulation,
  onReloadHistorical,
  onRunSimulation,
}: UploadHistoricalPanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [files, setFiles] = useState<Record<UploadFieldKey, File | null>>({
    consolidado: null,
    fopm: null,
    renovacao: null,
    ams: null,
    venda_sw: null,
    data_science: null,
    administrativa: null,
  })
  const [optionalFiles, setOptionalFiles] = useState<Record<OptionalUploadFieldKey, File | null>>({
    balanco_patrimonial: null,
  })

  const activeSourceLabel = useMemo(() => {
    if (loadingHistorical) return 'Carregando fonte...'
    if (!historical) return 'Sem histórico carregado'

    const defaultStart = Number(HISTORICAL_YEARS[0])
    const isLikelyActive =
      historical.historical_year_start !== defaultStart || historical.historical_year_end !== HISTORICAL_YEAR_END

    if (isLikelyActive) return 'Fonte: uploads ativos'
    return 'Fonte: data/original'
  }, [historical, loadingHistorical])

  const yearRangeLabel = useMemo(() => {
    if (!historical) return ''
    return `(${historical.historical_year_start}–${historical.historical_year_end} + ${historical.projected_year_start}–${historical.projected_year_end ?? ''})`
  }, [historical])

  const canSubmit = FILE_SPECS.every(({ key }) => Boolean(files[key]))

  const resetMessages = () => {
    setError(null)
    setSuccess(null)
  }

  const onPickFile = (key: UploadFieldKey) => (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null
    setFiles((prev) => ({ ...prev, [key]: f }))
    resetMessages()
  }
  const onPickOptionalFile = (key: OptionalUploadFieldKey) => (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null
    setOptionalFiles((prev) => ({ ...prev, [key]: f }))
    resetMessages()
  }

  const validateBeforeUpload = (): string | null => {
    for (const { key } of FILE_SPECS) {
      if (!files[key]) return `Selecione o arquivo CSV para: ${key}.`
      const name = files[key]!.name.toLowerCase()
      if (!name.endsWith('.csv')) return `O arquivo "${files[key]!.name}" não parece ser um CSV (.csv).`
    }
    for (const { key } of OPTIONAL_FILE_SPECS) {
      const f = optionalFiles[key]
      if (!f) continue
      const name = f.name.toLowerCase()
      if (!name.endsWith('.csv')) return `O arquivo "${f.name}" não parece ser um CSV (.csv).`
    }
    return null
  }

  const upload = async () => {
    resetMessages()
    const validationError = validateBeforeUpload()
    if (validationError) {
      setError(validationError)
      return
    }

    setUploading(true)
    try {
      const formData = new FormData()
      for (const { key } of FILE_SPECS) {
        // Backend espera campos com estes nomes.
        formData.append(key, files[key] as File)
      }
      for (const { key } of OPTIONAL_FILE_SPECS) {
        const f = optionalFiles[key]
        if (f) formData.append(key, f)
      }

      const res = await fetch(`${API_BASE_URL}/upload-historical`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        throw new Error(await res.text())
      }

      const data = (await res.json()) as {
        historical_year_end: number
        projected_year_start: number
        projected_year_end: number
      }

      setSuccess(`Upload OK. Novo histórico vai até ${data.historical_year_end}.`)

      await onReloadHistorical()
      await onRunSimulation()
      setIsOpen(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Falha no upload dos CSVs.')
    } finally {
      setUploading(false)
    }
  }

  const resetToOriginals = async () => {
    resetMessages()
    if (!confirm('Resetar histórico para data/original? Isso vai substituir os uploads ativos.')) return

    setUploading(true)
    try {
      const res = await fetch(`${API_BASE_URL}/reset-historical`, { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())

      setSuccess('Histórico resetado para data/original.')

      await onReloadHistorical()
      await onRunSimulation()
      setIsOpen(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Falha no reset do histórico.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.sourceRow}>
        <div>
          <div className={styles.sourceTitle}>Dados Históricos (CSV)</div>
          <div className={styles.sourceSub}>
            {activeSourceLabel} {yearRangeLabel && <span>{yearRangeLabel}</span>}
          </div>
        </div>

        <div className={styles.sourceActions}>
          <Button variant="secondary" onClick={() => setIsOpen(true)} loading={uploading} disabled={uploading}>
            Substituir CSVs
          </Button>
          <Button
            variant="ghost"
            onClick={() => void resetToOriginals()}
            loading={uploading}
            disabled={uploading || loadingSimulation}
          >
            Resetar originais
          </Button>
        </div>
      </div>

      {isOpen && (
        <div className={styles.overlay} role="dialog" aria-modal="true">
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <div>
                <div className={styles.modalTitle}>Substituir dados históricos</div>
                <div className={styles.modalSubtitle}>
                  Sete CSVs obrigatórios (DRE em pivot) + balanço opcional. O guia abaixo explica colunas, rótulos aceitos,
                  nomes dos campos no upload e exemplos — use o índice à esquerda para navegar.
                </div>
              </div>
              <Button variant="ghost" onClick={() => setIsOpen(false)} disabled={uploading}>
                Fechar
              </Button>
            </div>

            <div className={styles.formGrid}>
              {FILE_SPECS.map(({ key, label }) => (
                <Input
                  key={key}
                  type="file"
                  label={label}
                  accept=".csv,text/csv"
                  onChange={onPickFile(key)}
                  hint={files[key] ? files[key]!.name : 'Selecione o CSV'}
                  disabled={uploading}
                />
              ))}
              {OPTIONAL_FILE_SPECS.map(({ key, label }) => (
                <Input
                  key={key}
                  type="file"
                  label={label}
                  accept=".csv,text/csv"
                  onChange={onPickOptionalFile(key)}
                  hint={optionalFiles[key] ? optionalFiles[key]!.name : 'Opcional'}
                  disabled={uploading}
                />
              ))}
            </div>

            {error ? <Alert variant="error" title="Erro no upload">{error}</Alert> : null}
            {success ? <Alert variant="success" title="Status">{success}</Alert> : null}

            <div className={styles.modalFooter}>
              <Button variant="secondary" onClick={() => void upload()} loading={uploading} disabled={!canSubmit || uploading}>
                Enviar e recalcular
              </Button>
            </div>

            <CsvUploadGuide />
          </div>
        </div>
      )}
    </div>
  )
}

