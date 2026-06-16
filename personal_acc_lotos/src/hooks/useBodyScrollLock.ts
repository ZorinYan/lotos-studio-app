import { useEffect } from 'react'

let lockCount = 0
let savedScrollY = 0

type SavedStyles = {
  position: string
  top: string
  left: string
  right: string
  width: string
  overflow: string
}

let savedBodyStyles: SavedStyles | null = null
let savedHtmlOverflow = ''

function lockBody() {
  if (lockCount === 0) {
    savedScrollY = window.scrollY
    const body = document.body
    savedBodyStyles = {
      position: body.style.position,
      top: body.style.top,
      left: body.style.left,
      right: body.style.right,
      width: body.style.width,
      overflow: body.style.overflow,
    }
    savedHtmlOverflow = document.documentElement.style.overflow

    body.style.position = 'fixed'
    body.style.top = `-${savedScrollY}px`
    body.style.left = '0'
    body.style.right = '0'
    body.style.width = '100%'
    body.style.overflow = 'hidden'
    document.documentElement.style.overflow = 'hidden'
  }
  lockCount += 1
}

function unlockBody() {
  if (lockCount <= 0) {
    return
  }
  lockCount -= 1
  if (lockCount > 0 || !savedBodyStyles) {
    return
  }

  const body = document.body
  body.style.position = savedBodyStyles.position
  body.style.top = savedBodyStyles.top
  body.style.left = savedBodyStyles.left
  body.style.right = savedBodyStyles.right
  body.style.width = savedBodyStyles.width
  body.style.overflow = savedBodyStyles.overflow
  document.documentElement.style.overflow = savedHtmlOverflow
  window.scrollTo(0, savedScrollY)
  savedBodyStyles = null
}

export function useBodyScrollLock(locked: boolean) {
  useEffect(() => {
    if (!locked) {
      return
    }
    lockBody()
    return () => {
      unlockBody()
    }
  }, [locked])
}
