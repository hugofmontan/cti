import type { ReactNode } from 'react'
import clsx from 'clsx'
import styles from './Table.module.css'

interface Column<T> {
  key: keyof T | string
  header: string
  align?: 'left' | 'right' | 'center'
  width?: string
  render?: (row: T, index: number) => ReactNode
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyField?: keyof T
  className?: string
  striped?: boolean
  compact?: boolean
  highlightRows?: (row: T, index: number) => boolean
}

export function Table<T extends Record<string, unknown>>({
  columns,
  data,
  keyField,
  className,
  striped = true,
  compact = false,
  highlightRows,
}: TableProps<T>) {
  return (
    <div className={styles.wrapper}>
      <table className={clsx(
        styles.table,
        striped && styles.striped,
        compact && styles.compact,
        className
      )}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                style={{
                  textAlign: col.align || 'right',
                  width: col.width
                }}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr
              key={keyField ? String(row[keyField]) : index}
              className={clsx(highlightRows?.(row, index) && styles.highlighted)}
            >
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  style={{ textAlign: col.align || 'right' }}
                >
                  {col.render
                    ? col.render(row, index)
                    : String(row[col.key as keyof T] ?? '')
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
