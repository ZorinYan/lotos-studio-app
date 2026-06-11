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
