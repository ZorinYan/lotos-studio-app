const STORAGE_PREFIX = 'lotos_welcome_seen_'

export function hasSeenWelcomeBanner(vkUserId: number): boolean {
  try {
    return localStorage.getItem(`${STORAGE_PREFIX}${vkUserId}`) === '1'
  } catch {
    return false
  }
}

export function markWelcomeBannerSeen(vkUserId: number): void {
  try {
    localStorage.setItem(`${STORAGE_PREFIX}${vkUserId}`, '1')
  } catch {
    // ignore quota / private mode
  }
}
