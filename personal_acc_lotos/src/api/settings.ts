import { apiFetch } from './client'

export type FavoriteTrainer = {
  id: number
  name: string
}

export type ColorScheme = 'light' | 'dark'

export type UserSettings = {
  favoriteTrainer: FavoriteTrainer | null
  notificationsEnabled: boolean
  colorScheme: ColorScheme
  welcomeBannerSeen: boolean
}

type RawSettings = {
  favoriteTrainer?: FavoriteTrainer | null
  favorite_trainer?: FavoriteTrainer | null
  notificationsEnabled?: boolean
  notifications_enabled?: boolean
  colorScheme?: string
  color_scheme?: string
  welcomeBannerSeen?: boolean
  welcome_banner_seen?: boolean
}

function normalizeUserSettings(raw: RawSettings): UserSettings {
  const favoriteTrainer = raw.favoriteTrainer ?? raw.favorite_trainer ?? null
  const scheme = raw.colorScheme ?? raw.color_scheme

  return {
    favoriteTrainer,
    notificationsEnabled: Boolean(raw.notificationsEnabled ?? raw.notifications_enabled),
    colorScheme: scheme === 'dark' ? 'dark' : 'light',
    welcomeBannerSeen: Boolean(raw.welcomeBannerSeen ?? raw.welcome_banner_seen),
  }
}

export function fetchSettings(vkUserId: number) {
  return apiFetch<RawSettings>(`/api/settings?vk_user_id=${vkUserId}`).then(normalizeUserSettings)
}

export function updateSettings(
  vkUserId: number,
  patch: {
    favoriteStaffId?: number
    favoriteStaffName?: string
    clearFavorite?: boolean
    notificationsEnabled?: boolean
    colorScheme?: ColorScheme
    welcomeBannerSeen?: boolean
  },
) {
  return apiFetch<RawSettings>('/api/settings', {
    method: 'PUT',
    body: JSON.stringify({
      vk_user_id: vkUserId,
      favorite_staff_id: patch.favoriteStaffId,
      favorite_staff_name: patch.favoriteStaffName,
      clear_favorite: patch.clearFavorite ?? false,
      notifications_enabled: patch.notificationsEnabled,
      color_scheme: patch.colorScheme,
      welcome_banner_seen: patch.welcomeBannerSeen,
    }),
  }).then(normalizeUserSettings)
}
