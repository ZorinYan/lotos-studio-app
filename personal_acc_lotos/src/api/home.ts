import type { HomeData } from '../types/home'
import { apiFetch } from './client'

export function fetchHome(vkUserId: number) {
  return apiFetch<HomeData>(`/api/home?vk_user_id=${vkUserId}`)
}
