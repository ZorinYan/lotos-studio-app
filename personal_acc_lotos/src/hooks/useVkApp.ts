import { parseURLSearchParamsForGetLaunchParams } from '@vkontakte/vk-bridge'
import { useEffect, useState } from 'react'
import { bridge, sendVkInit } from '../vkBridge'

export type VkUser = {
  id: number
  first_name?: string
  last_name?: string
}

type VkAppState = {
  ready: boolean
  vkUser: VkUser | null
  error: string | null
}

const DEV_VK_USER_ID = Number(import.meta.env.VITE_DEV_VK_USER_ID ?? '1')
const BRIDGE_TIMEOUT_MS = 15_000

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) => {
      window.setTimeout(() => reject(new Error('vk_bridge_timeout')), ms)
    }),
  ])
}

function isVkIframe(): boolean {
  try {
    if (typeof bridge.isIframe === 'function' && bridge.isIframe()) {
      return true
    }
  } catch {
    // ignore
  }
  return window.parent !== window
}

function userFromLaunchParams(): VkUser | null {
  const params = parseURLSearchParamsForGetLaunchParams(window.location.search)
  const id = Number(params.vk_user_id)
  if (!Number.isFinite(id) || id <= 0) {
    return null
  }
  return { id, first_name: 'Пользователь' }
}

function userFromQuery(): VkUser | null {
  const raw = new URLSearchParams(window.location.search).get('vk_user_id')
  const id = Number(raw)
  if (!raw || !Number.isFinite(id) || id <= 0) {
    return null
  }
  return { id, first_name: 'Гость' }
}

function testVkUser(): VkUser {
  return { id: DEV_VK_USER_ID, first_name: 'Тест' }
}

function shouldSkipBridge(): boolean {
  if (import.meta.env.VITE_SKIP_VK_BRIDGE !== 'true') {
    return false
  }
  return !isVkIframe() && !userFromLaunchParams()
}

export function useVkApp(): VkAppState {
  const [state, setState] = useState<VkAppState>({
    ready: false,
    vkUser: null,
    error: null,
  })

  useEffect(() => {
    let cancelled = false

    async function init() {
      if (shouldSkipBridge()) {
        if (!cancelled) {
          setState({ ready: true, vkUser: testVkUser(), error: null })
        }
        return
      }

      const launchUser = userFromLaunchParams() ?? userFromQuery()

      try {
        await withTimeout(sendVkInit(), BRIDGE_TIMEOUT_MS)

        if (launchUser) {
          if (!cancelled) {
            setState({ ready: true, vkUser: launchUser, error: null })
          }
          return
        }

        const userInfo = await withTimeout(
          bridge.send('VKWebAppGetUserInfo'),
          BRIDGE_TIMEOUT_MS,
        )
        if (!cancelled) {
          setState({
            ready: true,
            vkUser: {
              id: userInfo.id,
              first_name: userInfo.first_name,
              last_name: userInfo.last_name,
            },
            error: null,
          })
        }
      } catch {
        if (cancelled) return

        const fallback =
          launchUser ??
          (import.meta.env.DEV || shouldSkipBridge() ? testVkUser() : null)

        setState({
          ready: true,
          vkUser: fallback,
          error: fallback
            ? null
            : 'Не удалось подключиться к ВКонтакте. Закройте и откройте мини-приложение снова.',
        })
      }
    }

    void init()

    return () => {
      cancelled = true
    }
  }, [])

  return state
}
