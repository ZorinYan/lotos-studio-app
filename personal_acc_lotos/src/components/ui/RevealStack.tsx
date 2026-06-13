import { useMemo } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import './PullToRefresh.css'

type RevealStackProps = {
  children: ReactNode
  className?: string
}

const STEP_MS = 70

export function RevealStack({ children, className = '' }: RevealStackProps) {
  const items = useMemo(() => {
    const array = Array.isArray(children) ? children : [children]
    return array.filter((child) => child != null && child !== false)
  }, [children])

  return (
    <div className={className}>
      {items.map((child, index) => (
        <div
          key={index}
          className="lotos-reveal"
          style={{ animationDelay: `${index * STEP_MS}ms` } as CSSProperties}
        >
          {child}
        </div>
      ))}
    </div>
  )
}
