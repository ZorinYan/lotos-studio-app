import { updateSettings } from '../api/settings'

export async function markWelcomeBannerSeen(vkUserId: number): Promise<void> {
  try {
    await updateSettings(vkUserId, { welcomeBannerSeen: true })
  } catch {
    // баннер уже закрыт в UI; повторная запись не критична
  }
}
