import bridgeImport from '@vkontakte/vk-bridge'

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

export function sendVkInit(): Promise<{ result: true }> {
  initPromise ??= bridge.send('VKWebAppInit') as Promise<{ result: true }>
  return initPromise
}

const MESSAGES_PERMISSION_KEY = 'lotos_vk_messages_allowed'
const NOTIFICATIONS_TIMEOUT_MS = 8_000

function isVkEnvironment(): boolean {
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

export async function requestVkNotificationsPermission(): Promise<boolean> {
  const stored = sessionStorage.getItem(MESSAGES_PERMISSION_KEY)
  if (stored !== null) {
    return stored === 'true'
  }

  if (import.meta.env.VITE_SKIP_VK_BRIDGE === 'true' || !isVkEnvironment()) {
    sessionStorage.setItem(MESSAGES_PERMISSION_KEY, 'false')
    return false
  }

  try {
    const result = (await withTimeout(
      bridge.send('VKWebAppAllowNotifications') as Promise<{ result?: boolean }>,
      NOTIFICATIONS_TIMEOUT_MS,
    )) as { result?: boolean }
    const allowed = result?.result === true
    sessionStorage.setItem(MESSAGES_PERMISSION_KEY, String(allowed))
    return allowed
  } catch {
    sessionStorage.setItem(MESSAGES_PERMISSION_KEY, 'false')
    return false
  }
}

function shouldInitEarly(): boolean {
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

if (shouldInitEarly()) {
  sendVkInit()
}
