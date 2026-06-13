import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import './PullToRefresh.css'

type PullToRefreshProps = {
  onRefresh: () => Promise<void>
  refreshing?: boolean
  disabled?: boolean
  children: ReactNode
}

const THRESHOLD = 72
const MAX_PULL = 96

export function PullToRefresh({
  onRefresh,
  refreshing = false,
  disabled = false,
  children,
}: PullToRefreshProps) {
  const [pullDistance, setPullDistance] = useState(0)
  const startYRef = useRef<number | null>(null)
  const pullingRef = useRef(false)
  const busyRef = useRef(false)

  useEffect(() => {
    busyRef.current = refreshing
  }, [refreshing])

  const reset = useCallback(() => {
    startYRef.current = null
    pullingRef.current = false
    setPullDistance(0)
  }, [])

  const handleTouchStart = useCallback((event: TouchEvent) => {
    if (disabled || busyRef.current) return
    if (window.scrollY > 4) return
    startYRef.current = event.touches[0]?.clientY ?? null
    pullingRef.current = true
  }, [disabled])

  const handleTouchMove = useCallback((event: TouchEvent) => {
    if (!pullingRef.current || startYRef.current == null || disabled || busyRef.current) return

    const currentY = event.touches[0]?.clientY ?? startYRef.current
    const delta = currentY - startYRef.current

    if (delta <= 0) {
      setPullDistance(0)
      return
    }

    if (window.scrollY > 4) {
      reset()
      return
    }

    event.preventDefault()
    setPullDistance(Math.min(delta * 0.45, MAX_PULL))
  }, [disabled, reset])

  const handleTouchEnd = useCallback(() => {
    if (!pullingRef.current || disabled || busyRef.current) {
      reset()
      return
    }

    const shouldRefresh = pullDistance >= THRESHOLD
    reset()

    if (shouldRefresh) {
      void onRefresh()
    }
  }, [disabled, onRefresh, pullDistance, reset])

  useEffect(() => {
    const opts: AddEventListenerOptions = { passive: false }
    document.addEventListener('touchstart', handleTouchStart, opts)
    document.addEventListener('touchmove', handleTouchMove, opts)
    document.addEventListener('touchend', handleTouchEnd)
    document.addEventListener('touchcancel', handleTouchEnd)

    return () => {
      document.removeEventListener('touchstart', handleTouchStart)
      document.removeEventListener('touchmove', handleTouchMove)
      document.removeEventListener('touchend', handleTouchEnd)
      document.removeEventListener('touchcancel', handleTouchEnd)
    }
  }, [handleTouchEnd, handleTouchMove, handleTouchStart])

  const progress = Math.min(pullDistance / THRESHOLD, 1)
  const visible = pullDistance > 0 || refreshing

  return (
    <div className="pull-to-refresh">
      <div
        className={`pull-to-refresh__indicator${visible ? ' pull-to-refresh__indicator--visible' : ''}${
          refreshing ? ' pull-to-refresh__indicator--refreshing' : ''
        }`}
        style={{ height: refreshing ? 44 : pullDistance }}
        aria-hidden="true"
      >
        <span
          className="pull-to-refresh__spinner"
          style={{ transform: refreshing ? undefined : `rotate(${progress * 320}deg)` }}
        />
        <span className="pull-to-refresh__label">
          {refreshing ? 'Обновляем…' : progress >= 1 ? 'Отпустите' : 'Потяните вниз'}
        </span>
      </div>
      {children}
    </div>
  )
}
