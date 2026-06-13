import type {
  BookScheduleResult,
  BookingEligibility,
  GuestCheckResult,
  RebookData,
  ScheduleData,
  ScheduleFilterOptions,
} from '../types/schedule'
import { apiFetch, withRefresh } from './client'

export function fetchSchedule(date?: string, refresh = false) {
  const params = new URLSearchParams()
  if (date) params.set('day', date)
  const query = params.toString()
  const path = query ? `/api/schedule?${query}` : '/api/schedule'
  return apiFetch<ScheduleData>(withRefresh(path, refresh))
}

export function fetchScheduleFilters(refresh = false) {
  return apiFetch<ScheduleFilterOptions>(
    withRefresh('/api/schedule/filters', refresh),
  )
}

export function fetchRebookSlots(vkUserId: number) {
  return apiFetch<RebookData>(`/api/schedule/rebook?vk_user_id=${vkUserId}`)
}

export function checkGuestBooking(phone: string) {
  return apiFetch<GuestCheckResult>('/api/schedule/guest-check', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  })
}

export function checkBookingEligibility(
  vkUserId: number,
  activityId: number,
  activityDate?: string,
) {
  const params = new URLSearchParams({
    vk_user_id: String(vkUserId),
    activity_id: String(activityId),
  })
  if (activityDate) {
    params.set('activity_date', activityDate)
  }
  return apiFetch<BookingEligibility>(`/api/schedule/book/eligibility?${params}`)
}

export function bookScheduleClass(
  vkUserId: number,
  activityId: number,
  activityDate?: string,
  guest?: { phone: string; name: string; surname: string },
) {
  return apiFetch<BookScheduleResult>('/api/schedule/book', {
    method: 'POST',
    body: JSON.stringify({
      vk_user_id: vkUserId,
      activity_id: activityId,
      activity_date: activityDate ?? null,
      phone: guest?.phone ?? null,
      name: guest?.name ?? null,
      surname: guest?.surname ?? null,
    }),
  })
}
