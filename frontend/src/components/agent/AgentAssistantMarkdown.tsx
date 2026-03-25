import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import styles from './AgentAssistantMarkdown.module.css'

interface AgentAssistantMarkdownProps {
  content: string
}

export function AgentAssistantMarkdown({ content }: AgentAssistantMarkdownProps) {
  const normalizedContent = content
    .replace(/\\\[/g, '$$')
    .replace(/\\\]/g, '$$')

  return (
    <div className={styles.markdown}>
      <ReactMarkdown
        remarkPlugins={[[remarkMath, { singleDollarTextMath: false }]]}
        rehypePlugins={[rehypeKatex]}
        components={{
          p: ({ children }) => <p className={styles.p}>{children}</p>,
          ul: ({ children }) => <ul className={styles.ul}>{children}</ul>,
          ol: ({ children }) => <ol className={styles.ol}>{children}</ol>,
          li: ({ children }) => <li className={styles.li}>{children}</li>,
          strong: ({ children }) => <strong className={styles.strong}>{children}</strong>,
          code: ({ children, className }) => {
            const isBlock = Boolean(className)
            if (isBlock) {
              return (
                <pre className={styles.pre}>
                  <code className={styles.codeBlock}>{children}</code>
                </pre>
              )
            }
            return <code className={styles.codeInline}>{children}</code>
          },
          h1: ({ children }) => <h3 className={styles.heading}>{children}</h3>,
          h2: ({ children }) => <h3 className={styles.heading}>{children}</h3>,
          h3: ({ children }) => <h4 className={styles.subheading}>{children}</h4>,
          blockquote: ({ children }) => <blockquote className={styles.quote}>{children}</blockquote>,
          hr: () => <hr className={styles.hr} />,
        }}
      >
        {normalizedContent}
      </ReactMarkdown>
    </div>
  )
}
