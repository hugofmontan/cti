import type { ButtonHTMLAttributes, ReactNode } from 'react'
import clsx from 'clsx'
import styles from './Button.module.css'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  children: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        styles.button,
        styles[variant],
        styles[size],
        loading && styles.loading,
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <LoadingSpinner />}
      <span className={clsx(loading && styles.hiddenText)}>{children}</span>
    </button>
  )
}

function LoadingSpinner() {
  return (
    <svg
      className={styles.spinner}
      width="16"
      height="16"
      viewBox="0 0 16 16"
      aria-hidden="true"
    >
      <circle
        cx="8"
        cy="8"
        r="6"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeDasharray="31.4"
        strokeDashoffset="10"
      />
    </svg>
  )
}
