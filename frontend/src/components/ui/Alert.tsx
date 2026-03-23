import type { ReactNode } from 'react'
import clsx from 'clsx'
import styles from './Alert.module.css'

interface AlertProps {
  variant?: 'info' | 'warning' | 'error' | 'success'
  title?: string
  children: ReactNode
  className?: string
  onDismiss?: () => void
}

export function Alert({
  variant = 'info',
  title,
  children,
  className,
  onDismiss
}: AlertProps) {
  return (
    <div className={clsx(styles.alert, styles[variant], className)} role="alert">
      <div className={styles.icon}>
        <AlertIcon variant={variant} />
      </div>
      <div className={styles.content}>
        {title && <div className={styles.title}>{title}</div>}
        <div className={styles.message}>{children}</div>
      </div>
      {onDismiss && (
        <button
          type="button"
          className={styles.dismiss}
          onClick={onDismiss}
          aria-label="Fechar"
        >
          <CloseIcon />
        </button>
      )}
    </div>
  )
}

function AlertIcon({ variant }: { variant: string }) {
  if (variant === 'warning') {
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path
          d="M8 5V8M8 11H8.01M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    )
  }
  if (variant === 'error') {
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path
          d="M6 6L10 10M10 6L6 10M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    )
  }
  if (variant === 'success') {
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path
          d="M5 8L7 10L11 6M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    )
  }
  // info
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path
        d="M8 7V11M8 5H8.01M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path
        d="M4 4L10 10M10 4L4 10"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}
