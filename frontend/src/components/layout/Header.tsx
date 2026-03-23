import styles from './Header.module.css'

export function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <div className={styles.brand}>
          <h1 className={styles.title}>Calculadora de Projecoes - DCF</h1>
          <span className={styles.subtitle}>Dashboard Financeiro</span>
        </div>
      </div>
    </header>
  )
}
