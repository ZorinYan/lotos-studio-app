import type { StudioFeed } from '../types/studio'
import { apiFetch, withRefresh } from './client'

export function fetchStudioFeed(vkUserId: number, refresh = false) {
  return apiFetch<StudioFeed>(
    withRefresh(`/api/studio/feed?vk_user_id=${vkUserId}`, refresh),
  )
}
