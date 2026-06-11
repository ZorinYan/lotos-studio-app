import { parseURLSearchParamsForGetLaunchParams } from '@vkontakte/vk-bridge'

let cachedLaunch: Record<string, string> | null = null

function shouldAttachLaunchParams(): boolean {
  if (import.meta.env.VITE_SKIP_VK_BRIDGE === 'true') {
    return false
  }
  return true
}

export function getVkLaunchParams(): Record<string, string> {
  if (!shouldAttachLaunchParams()) {
    return {}
  }

  if (!cachedLaunch) {
    const parsed = parseURLSearchParamsForGetLaunchParams(window.location.search)
    cachedLaunch = Object.fromEntries(
      Object.entries(parsed).map(([key, value]) => [key, value == null ? '' : String(value)]),
    )
  }
  return cachedLaunch
}

export function vkLaunchHeaders(): Record<string, string> {
  const params = getVkLaunchParams()
  if (!params.sign) {
    return {}
  }
  return { 'X-VK-Launch-Params': btoa(JSON.stringify(params)) }
}
