import type { CabinetData } from '../types/cabinet'
import { apiFetch } from './client'

export function fetchCabinet(vkUserId: number) {
  return apiFetch<CabinetData>(`/api/cabinet?vk_user_id=${vkUserId}`)
}
