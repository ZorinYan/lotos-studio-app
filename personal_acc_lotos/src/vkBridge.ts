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

export const MESSAGES_PERMISSION_KEY = 'lotos_vk_community_messages_allowed'
const PUSH_NOTIFICATIONS_KEY = 'lotos_vk_push_notifications_allowed'
const PERMISSION_TIMEOUT_MS = 8_000

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

export function readMessagesFromLaunch(): boolean | null {
  const value = getVkLaunchParams().vk_messages_allowed
  if (value === '1') return true
  if (value === '0') return false
  return null
}

export function resolveInitialMessagesEnabled(): boolean {
  sessionStorage.removeItem('lotos_vk_notifications_allowed')
  return getCachedNotificationsPermission() ?? readMessagesFromLaunch() ?? false
}

export function resolveInitialNotificationsEnabled(): boolean {
  const cached = sessionStorage.getItem(PUSH_NOTIFICATIONS_KEY)
  if (cached !== null) {
    return cached === 'true'
  }
  return readNotificationsFromLaunch() ?? false
}

export async function requestVkCommunityMessagesPermission(
  groupId: number,
): Promise<boolean> {
  if (!Number.isFinite(groupId) || groupId <= 0) {
    setCachedNotificationsPermission(false)
    return false
  }

  const cached = getCachedNotificationsPermission()
  if (cached === true) {
    return true
  }

  if (import.meta.env.VITE_SKIP_VK_BRIDGE === 'true' || !isVkEnvironment()) {
    setCachedNotificationsPermission(false)
    return false
  }

  try {
    await sendVkInit()
    const result = (await withTimeout(
      bridge.send('VKWebAppAllowMessagesFromGroup', {
        group_id: Math.abs(groupId),
      }) as Promise<{ result?: boolean }>,
      PERMISSION_TIMEOUT_MS,
    )) as { result?: boolean }
    const allowed = result?.result === true
    setCachedNotificationsPermission(allowed)
    return allowed
  } catch {
    return getCachedNotificationsPermission() ?? false
  }
}

export async function requestVkNotificationsPermission(): Promise<boolean> {
  const cached = sessionStorage.getItem(PUSH_NOTIFICATIONS_KEY)
  if (cached !== null) {
    return cached === 'true'
  }

  if (import.meta.env.VITE_SKIP_VK_BRIDGE === 'true' || !isVkEnvironment()) {
    sessionStorage.setItem(PUSH_NOTIFICATIONS_KEY, 'false')
    return false
  }

  try {
    await sendVkInit()
    const result = (await withTimeout(
      bridge.send('VKWebAppAllowNotifications') as Promise<{ result?: boolean }>,
      PERMISSION_TIMEOUT_MS,
    )) as { result?: boolean }
    const allowed = result?.result === true
    sessionStorage.setItem(PUSH_NOTIFICATIONS_KEY, String(allowed))
    return allowed
  } catch {
    return sessionStorage.getItem(PUSH_NOTIFICATIONS_KEY) === 'true'
  }
}

/** Push-уведомления VK (настройки), не путать с ЛС от сообщества для OTP. */
export async function setVkNotificationsEnabled(enabled: boolean): Promise<boolean> {
  if (!enabled) {
    sessionStorage.setItem(PUSH_NOTIFICATIONS_KEY, 'false')
    return true
  }

  sessionStorage.removeItem(PUSH_NOTIFICATIONS_KEY)
  return requestVkNotificationsPermission()
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

export async function copyVkText(text: string): Promise<boolean> {
  if (!text) return false

  if (import.meta.env.VITE_SKIP_VK_BRIDGE === 'true' || !isVkEnvironment()) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      return false
    }
  }

  try {
    await sendVkInit()
    const result = (await bridge.send('VKWebAppCopyText', { text })) as { result?: boolean }
    return result?.result === true
  } catch {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      return false
    }
  }
}

export function buildVkGroupMessagesUrl(groupId: number): string {
  const id = Math.abs(groupId)
  return `https://vk.com/im?sel=-${id}`
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
