import type { ReactNode } from 'react'
import clsx from 'clsx'
import styles from './ChartContainer.module.css'

interface ChartContainerProps {
  title?: string
  height?: number
  children: ReactNode
  className?: string
}

export function ChartContainer({
  title,
  height = 300,
  children,
  className
}: ChartContainerProps) {
  return (
    <div className={clsx(styles.container, className)}>
      {title && <h4 className={styles.title}>{title}</h4>}
      <div className={styles.chart} style={{ height }}>
        {children}
      </div>
    </div>
  )
}
