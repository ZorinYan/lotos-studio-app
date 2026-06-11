import type { CabinetData } from '../types/cabinet'
import { apiFetch, withRefresh } from './client'

export function fetchCabinet(vkUserId: number, refresh = false) {
  return apiFetch<CabinetData>(
    withRefresh(`/api/cabinet?vk_user_id=${vkUserId}`, refresh),
  )
}
