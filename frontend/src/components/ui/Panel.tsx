import { type ReactNode, useState } from 'react'
import clsx from 'clsx'
import styles from './Panel.module.css'

interface PanelProps {
  title: string
  children: ReactNode
  defaultOpen?: boolean
  collapsible?: boolean
  className?: string
}

export function Panel({
  title,
  children,
  defaultOpen = true,
  collapsible = true,
  className
}: PanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  if (!collapsible) {
    return (
      <div className={clsx(styles.panel, className)}>
        <div className={styles.header}>
          <h3 className={styles.title}>{title}</h3>
        </div>
        <div className={styles.content}>{children}</div>
      </div>
    )
  }

  return (
    <div className={clsx(styles.panel, className)}>
      <button
        type="button"
        className={styles.header}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <h3 className={styles.title}>{title}</h3>
        <span className={clsx(styles.chevron, isOpen && styles.open)}>
          <ChevronIcon />
        </span>
      </button>
      {isOpen && <div className={styles.content}>{children}</div>}
    </div>
  )
}

function ChevronIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M4 6L8 10L12 6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
