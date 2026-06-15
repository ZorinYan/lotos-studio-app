import { ApiError } from './client'

export const SESSION_EXPIRED_CODES = new Set(['not_authenticated', 'client_not_found'])

export type SessionExpiredHandler = (message: string) => void

let sessionExpiredHandler: SessionExpiredHandler | null = null
let handlingSessionExpiry = false

const SESSION_EXEMPT_PREFIXES = [
  '/api/auth/logout',
  '/api/auth/phone',
  '/api/auth/verify',
  '/api/auth/password',
  '/api/config/public',
  '/api/boot',
  '/api/schedule/guest-check',
]

export function isSessionExpiredError(error: unknown): boolean {
  return error instanceof ApiError && SESSION_EXPIRED_CODES.has(error.code)
}

export function shouldHandleSessionExpiry(path: string): boolean {
  return !SESSION_EXEMPT_PREFIXES.some((prefix) => path.startsWith(prefix))
}

export function registerSessionExpiredHandler(handler: SessionExpiredHandler): () => void {
  sessionExpiredHandler = handler
  return () => {
    if (sessionExpiredHandler === handler) {
      sessionExpiredHandler = null
    }
  }
}

export function notifySessionExpired(message: string, path: string): void {
  if (!sessionExpiredHandler || !shouldHandleSessionExpiry(path) || handlingSessionExpiry) {
    return
  }
  handlingSessionExpiry = true
  try {
    sessionExpiredHandler(message)
  } finally {
    window.setTimeout(() => {
      handlingSessionExpiry = false
    }, 1000)
  }
}
