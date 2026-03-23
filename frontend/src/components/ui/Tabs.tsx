import { type ReactNode, useState } from 'react'
import clsx from 'clsx'
import styles from './Tabs.module.css'

interface Tab {
  id: string
  label: string
  content: ReactNode
}

interface TabsProps {
  tabs: Tab[]
  defaultTab?: string
  className?: string
  onChange?: (tabId: string) => void
}

export function Tabs({ tabs, defaultTab, className, onChange }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id)

  const handleTabClick = (tabId: string) => {
    setActiveTab(tabId)
    onChange?.(tabId)
  }

  const activeContent = tabs.find((tab) => tab.id === activeTab)?.content

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.tabList} role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={clsx(styles.tab, activeTab === tab.id && styles.active)}
            onClick={() => handleTabClick(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className={styles.content} role="tabpanel">
        {activeContent}
      </div>
    </div>
  )
}
