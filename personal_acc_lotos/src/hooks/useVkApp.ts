import {
  parseURLSearchParamsForGetLaunchParams,
  type UserInfo,
} from '@vkontakte/vk-bridge'
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

const BROWSER_HINT =
  'Это мини-приложение ВКонтакте — откройте его через сообщество студии или кнопку «Открыть» в настройках приложения на dev.vk.com. Для теста в браузере добавьте ?vk_user_id=ваш_id к URL.'

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
    if (typeof bridge.isWebView === 'function' && bridge.isWebView()) {
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

function resolveLaunchUser(): VkUser | null {
  return userFromLaunchParams() ?? userFromQuery()
}

function testVkUser(): VkUser {
  return { id: DEV_VK_USER_ID, first_name: 'Тест' }
}

function shouldSkipBridge(): boolean {
  if (import.meta.env.VITE_SKIP_VK_BRIDGE !== 'true') {
    return false
  }
  return !isVkIframe() && !resolveLaunchUser()
}

function buildInitialState(): VkAppState {
  if (shouldSkipBridge()) {
    return { ready: true, vkUser: testVkUser(), error: null }
  }

  const launchUser = resolveLaunchUser()
  if (launchUser && isVkIframe()) {
    return { ready: true, vkUser: launchUser, error: null }
  }

  return { ready: false, vkUser: null, error: null }
}

export function useVkApp(): VkAppState {
  const [state, setState] = useState<VkAppState>(buildInitialState)

  useEffect(() => {
    let cancelled = false

    async function enrichUserName() {
      try {
        const userInfo = await withTimeout<UserInfo>(
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
        // оставляем пользователя из launch params
      }
    }

    async function init() {
      if (shouldSkipBridge()) {
        return
      }

      const launchUser = resolveLaunchUser()
      const inVk = isVkIframe()

      if (launchUser && inVk) {
        void enrichUserName()
        return
      }

      try {
        await withTimeout(sendVkInit(), BRIDGE_TIMEOUT_MS)

        if (launchUser) {
          if (!cancelled) {
            setState({ ready: true, vkUser: launchUser, error: null })
          }
          return
        }

        await enrichUserName()
      } catch {
        if (cancelled) return

        if (launchUser) {
          setState({ ready: true, vkUser: launchUser, error: null })
          return
        }

        if (import.meta.env.DEV) {
          setState({ ready: true, vkUser: testVkUser(), error: null })
          return
        }

        setState({
          ready: true,
          vkUser: null,
          error: inVk
            ? 'Не удалось подключиться к ВКонтакте. Закройте и откройте мини-приложение снова.'
            : BROWSER_HINT,
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
