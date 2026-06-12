import { apiFetch } from './client'

export type FavoriteTrainer = {
  id: number
  name: string
}

export type UserSettings = {
  favoriteTrainer: FavoriteTrainer | null
  notificationsEnabled: boolean
}

export function fetchSettings(vkUserId: number) {
  return apiFetch<UserSettings>(`/api/settings?vk_user_id=${vkUserId}`)
}

export function updateSettings(
  vkUserId: number,
  patch: {
    favoriteStaffId?: number
    favoriteStaffName?: string
    clearFavorite?: boolean
    notificationsEnabled?: boolean
  },
) {
  return apiFetch<UserSettings>('/api/settings', {
    method: 'PUT',
    body: JSON.stringify({
      vk_user_id: vkUserId,
      favorite_staff_id: patch.favoriteStaffId,
      favorite_staff_name: patch.favoriteStaffName,
      clear_favorite: patch.clearFavorite ?? false,
      notifications_enabled: patch.notificationsEnabled,
    }),
  })
}
