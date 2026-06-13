import type { ReactNode } from 'react'
import './ProgressRing.css'

type ProgressRingProps = {
  progress: number
  size?: number
  strokeWidth?: number
  children?: ReactNode
  label?: string
}

export function ProgressRing({
  progress,
  size = 76,
  strokeWidth = 6,
  children,
  label,
}: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = Math.max(0, Math.min(progress, 1))
  const offset = circumference * (1 - clamped)

  return (
    <div
      className="progress-ring"
      style={{ width: size, height: size }}
      role="img"
      aria-label={label}
    >
      <svg
        className="progress-ring__svg"
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        aria-hidden="true"
      >
        <circle
          className="progress-ring__track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          className="progress-ring__fill"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      {children && <div className="progress-ring__content">{children}</div>}
    </div>
  )
}
