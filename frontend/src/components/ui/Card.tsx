import type { ReactNode } from 'react'
import clsx from 'clsx'
import styles from './Card.module.css'

interface CardProps {
  label: string
  value: string | number
  subValue?: string
  variant?: 'default' | 'highlight' | 'positive' | 'negative'
  className?: string
}

export function Card({ label, value, subValue, variant = 'default', className }: CardProps) {
  return (
    <div className={clsx(styles.card, styles[variant], className)}>
      <div className={styles.label}>{label}</div>
      <div className={styles.value}>{value}</div>
      {subValue && <div className={styles.subValue}>{subValue}</div>}
    </div>
  )
}

interface CardGroupProps {
  children: ReactNode
  columns?: 2 | 3 | 4
  className?: string
}

export function CardGroup({ children, columns = 4, className }: CardGroupProps) {
  return (
    <div
      className={clsx(styles.cardGroup, className)}
      style={{ '--columns': columns } as React.CSSProperties}
    >
      {children}
    </div>
  )
}
