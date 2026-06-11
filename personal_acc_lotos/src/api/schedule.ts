import type {
  BookScheduleResult,
  BookingEligibility,
  GuestCheckResult,
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
  guest?: { phone: string; name: string },
) {
  return apiFetch<BookScheduleResult>('/api/schedule/book', {
    method: 'POST',
    body: JSON.stringify({
      vk_user_id: vkUserId,
      activity_id: activityId,
      activity_date: activityDate ?? null,
      phone: guest?.phone ?? null,
      name: guest?.name ?? null,
    }),
  })
}
