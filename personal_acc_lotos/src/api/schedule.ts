import type {
  BookScheduleResult,
  RebookData,
  ScheduleData,
  ScheduleFilterOptions,
} from '../types/schedule'
import { apiFetch } from './client'

export function fetchSchedule(date?: string) {
  const query = date ? `?day=${encodeURIComponent(date)}` : ''
  return apiFetch<ScheduleData>(`/api/schedule${query}`)
}

export function fetchScheduleFilters() {
  return apiFetch<ScheduleFilterOptions>('/api/schedule/filters')
}

export function fetchRebookSlots(vkUserId: number) {
  return apiFetch<RebookData>(`/api/schedule/rebook?vk_user_id=${vkUserId}`)
}

export function bookScheduleClass(
  vkUserId: number,
  activityId: number,
  activityDate?: string,
) {
  return apiFetch<BookScheduleResult>('/api/schedule/book', {
    method: 'POST',
    body: JSON.stringify({
      vk_user_id: vkUserId,
      activity_id: activityId,
      activity_date: activityDate ?? null,
    }),
  })
}
