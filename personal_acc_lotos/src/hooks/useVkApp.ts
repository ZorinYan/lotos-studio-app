import bridge from '@vkontakte/vk-bridge'
import { useEffect, useState } from 'react'

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

export function useVkApp(): VkAppState {
  const [state, setState] = useState<VkAppState>({
    ready: false,
    vkUser: null,
    error: null,
  })

  useEffect(() => {
    let cancelled = false

    async function init() {
      try {
        if (import.meta.env.DEV && import.meta.env.VITE_SKIP_VK_BRIDGE === 'true') {
          if (!cancelled) {
            setState({
              ready: true,
              vkUser: { id: DEV_VK_USER_ID, first_name: 'Тест' },
              error: null,
            })
          }
          return
        }

        await bridge.send('VKWebAppInit')

        const userInfo = await bridge.send('VKWebAppGetUserInfo')
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
        if (!cancelled) {
          setState({
            ready: true,
            vkUser: import.meta.env.DEV ? { id: DEV_VK_USER_ID, first_name: 'Тест' } : null,
            error: import.meta.env.DEV
              ? null
              : 'Не удалось получить данные VK. Откройте приложение через ВКонтакте.',
          })
        }
      }
    }

    void init()

    return () => {
      cancelled = true
    }
  }, [])

  return state
}
