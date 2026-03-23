import clsx from 'clsx'
import styles from './LoadingSpinner.module.css'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
  return (
    <div className={clsx(styles.container, className)}>
      <svg
        className={clsx(styles.spinner, styles[size])}
        viewBox="0 0 24 24"
        aria-label="Carregando"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeDasharray="62.8"
          strokeDashoffset="20"
        />
      </svg>
    </div>
  )
}

interface LoadingOverlayProps {
  message?: string
}

export function LoadingOverlay({ message = 'Carregando...' }: LoadingOverlayProps) {
  return (
    <div className={styles.overlay}>
      <LoadingSpinner size="lg" />
      <span className={styles.message}>{message}</span>
    </div>
  )
}
