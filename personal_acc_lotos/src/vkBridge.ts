import bridge from '@vkontakte/vk-bridge'

export { bridge }

let initPromise: Promise<{ result: true }> | null = null

export function sendVkInit(): Promise<{ result: true }> {
  initPromise ??= bridge.send('VKWebAppInit')
  return initPromise
}

// Как можно раньше при загрузке бандла (требование VK).
sendVkInit()
