import bridgeImport from '@vkontakte/vk-bridge'
import { getVkLaunchParams } from './vkLaunch'

type BridgeLike = {
  send: (method: string, props?: Record<string, unknown>) => Promise<unknown>
  isIframe?: () => boolean
  isWebView?: () => boolean
}

/** Vite/Rolldown иногда кладёт API в .default (vk-bridge#563). */
function resolveBridge(): BridgeLike {
  const mod = bridgeImport as BridgeLike & { default?: BridgeLike }
  if (typeof mod?.send === 'function') {
    return mod
  }
  if (typeof mod?.default?.send === 'function') {
    return mod.default
  }
  throw new Error('vk-bridge: send() недоступен')
}

export const bridge = resolveBridge()

let initPromise: Promise<{ result: true }> | null = null

export const MESSAGES_PERMISSION_KEY = 'lotos_vk_messages_allowed'
const NOTIFICATIONS_TIMEOUT_MS = 8_000

export function sendVkInit(): Promise<{ result: true }> {
  initPromise ??= bridge.send('VKWebAppInit') as Promise<{ result: true }>
  return initPromise
}

export function isVkEnvironment(): boolean {
  try {
    if (typeof bridge.isWebView === 'function' && bridge.isWebView()) {
      return true
    }
    if (typeof bridge.isIframe === 'function' && bridge.isIframe()) {
      return true
    }
  } catch {
    // ignore
  }
  return window.parent !== window
}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) => {
      window.setTimeout(() => reject(new Error('vk_bridge_timeout')), ms)
    }),
  ])
}

export function getCachedNotificationsPermission(): boolean | null {
  const stored = sessionStorage.getItem(MESSAGES_PERMISSION_KEY)
  if (stored === null) return null
  return stored === 'true'
}

export function setCachedNotificationsPermission(allowed: boolean): void {
  sessionStorage.setItem(MESSAGES_PERMISSION_KEY, String(allowed))
}

export function readNotificationsFromLaunch(): boolean | null {
  const value = getVkLaunchParams().vk_are_notifications_enabled
  if (value === '1') return true
  if (value === '0') return false
  return null
}

export function resolveInitialNotificationsEnabled(): boolean {
  return (
    getCachedNotificationsPermission()
    ?? readNotificationsFromLaunch()
    ?? false
  )
}

export async function setVkNotificationsEnabled(enabled: boolean): Promise<boolean> {
  if (import.meta.env.VITE_SKIP_VK_BRIDGE === 'true' || !isVkEnvironment()) {
    setCachedNotificationsPermission(false)
    return false
  }

  try {
    const method = enabled ? 'VKWebAppAllowNotifications' : 'VKWebAppDenyNotifications'
    const result = (await withTimeout(
      bridge.send(method) as Promise<{ result?: boolean }>,
      NOTIFICATIONS_TIMEOUT_MS,
    )) as { result?: boolean }
    const allowed = enabled && result?.result === true
    setCachedNotificationsPermission(allowed)
    return allowed
  } catch {
    if (!enabled) {
      setCachedNotificationsPermission(false)
      return false
    }
    return getCachedNotificationsPermission() ?? false
  }
}

export async function requestVkNotificationsPermission(): Promise<boolean> {
  const cached = getCachedNotificationsPermission()
  if (cached !== null) {
    return cached
  }

  if (import.meta.env.VITE_SKIP_VK_BRIDGE === 'true' || !isVkEnvironment()) {
    setCachedNotificationsPermission(false)
    return false
  }

  return setVkNotificationsEnabled(true)
}

function shouldInitEarly(): boolean {
  return isVkEnvironment()
}

if (shouldInitEarly()) {
  sendVkInit()
}

export async function openVkUrl(url: string): Promise<void> {
  if (!url) return

  if (import.meta.env.VITE_SKIP_VK_BRIDGE === 'true' || !isVkEnvironment()) {
    window.open(url, '_blank', 'noopener,noreferrer')
    return
  }

  try {
    await sendVkInit()
    await bridge.send('VKWebAppOpenURL', { url })
  } catch {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

export async function openVkWallPost(ownerId: number, postId: number): Promise<void> {
  if (import.meta.env.VITE_SKIP_VK_BRIDGE === 'true' || !isVkEnvironment()) {
    await openVkUrl(`https://vk.com/wall${ownerId}_${postId}`)
    return
  }

  try {
    await sendVkInit()
    await bridge.send('VKWebAppOpenWallPost', { owner_id: ownerId, post_id: postId })
  } catch {
    await openVkUrl(`https://vk.com/wall${ownerId}_${postId}`)
  }
}
