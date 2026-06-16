import { useEffect, type RefObject } from 'react'
import { useBodyScrollLock } from './useBodyScrollLock'

const SWIPE_CLOSE_THRESHOLD_PX = 72
const SHEET_TRANSITION = 'transform 0.28s cubic-bezier(0.32, 0.72, 0, 1)'

export function useModalOverlay(
  onClose: () => void,
  sheetRef?: RefObject<HTMLElement | null>,
  options?: { swipeToClose?: boolean },
) {
  const swipeToClose = options?.swipeToClose ?? Boolean(sheetRef)

  useBodyScrollLock(true)

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  useEffect(() => {
    if (!swipeToClose || !sheetRef) {
      return
    }

    const sheet = sheetRef.current
    if (!sheet) {
      return
    }

    let startY = 0
    let tracking = false
    let pullDistance = 0

    function clearInlineMotion() {
      sheet!.style.transition = ''
      sheet!.style.transform = ''
      sheet!.style.animation = ''
    }

    function animateTransform(targetTransform: string, onDone?: () => void) {
      sheet!.style.animation = 'none'
      void sheet!.offsetHeight
      sheet!.style.transition = SHEET_TRANSITION
      sheet!.style.transform = targetTransform

      if (!onDone) {
        return
      }

      let finished = false
      const finish = () => {
        if (finished) {
          return
        }
        finished = true
        sheet!.removeEventListener('transitionend', onTransitionEnd)
        window.clearTimeout(fallbackTimer)
        onDone()
      }

      function onTransitionEnd(event: TransitionEvent) {
        if (event.target !== sheet || event.propertyName !== 'transform') {
          return
        }
        finish()
      }

      sheet!.addEventListener('transitionend', onTransitionEnd)
      const fallbackTimer = window.setTimeout(finish, 320)
    }

    function onTouchStart(event: TouchEvent) {
      if (sheet!.scrollTop > 0) {
        tracking = false
        return
      }
      tracking = true
      pullDistance = 0
      startY = event.touches[0]?.clientY ?? 0
      sheet!.style.animation = 'none'
      sheet!.style.transition = 'none'
    }

    function onTouchMove(event: TouchEvent) {
      if (!tracking) {
        return
      }
      const currentY = event.touches[0]?.clientY ?? 0
      const deltaY = Math.max(0, currentY - startY)
      pullDistance = Math.max(pullDistance, deltaY)
      if (deltaY > 0) {
        event.preventDefault()
      }
      sheet!.style.transform = `translateY(${deltaY}px)`
    }

    function onTouchEnd() {
      if (!tracking) {
        return
      }
      tracking = false

      if (pullDistance >= SWIPE_CLOSE_THRESHOLD_PX) {
        requestAnimationFrame(() => {
          animateTransform('translateY(100%)', onClose)
        })
        return
      }

      if (pullDistance > 0) {
        animateTransform('translateY(0)')
        return
      }

      clearInlineMotion()
    }

    sheet.addEventListener('touchstart', onTouchStart, { passive: true })
    sheet.addEventListener('touchmove', onTouchMove, { passive: false })
    sheet.addEventListener('touchend', onTouchEnd)
    sheet.addEventListener('touchcancel', onTouchEnd)

    return () => {
      sheet.removeEventListener('touchstart', onTouchStart)
      sheet.removeEventListener('touchmove', onTouchMove)
      sheet.removeEventListener('touchend', onTouchEnd)
      sheet.removeEventListener('touchcancel', onTouchEnd)
      clearInlineMotion()
    }
  }, [onClose, sheetRef, swipeToClose])
}
