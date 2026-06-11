import type { HomeData } from '../types/home'
import { apiFetch, withRefresh } from './client'

export function fetchHome(vkUserId: number, refresh = false) {
  return apiFetch<HomeData>(
    withRefresh(`/api/home?vk_user_id=${vkUserId}`, refresh),
  )
}
