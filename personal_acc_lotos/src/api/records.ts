import type { CancelRecordResult, RecordFilter, RecordsData, RescheduleResult, RescheduleSlotsData } from '../types/records'
import { apiFetch, withRefresh } from './client'

export function fetchRecords(
  vkUserId: number,
  filter: RecordFilter = 'all',
  refresh = false,
) {
  const query = new URLSearchParams({
    vk_user_id: String(vkUserId),
    filter,
  })
  return apiFetch<RecordsData>(withRefresh(`/api/records?${query}`, refresh))
}

export function cancelRecord(vkUserId: number, recordId: number) {
  return apiFetch<CancelRecordResult>('/api/records/cancel', {
    method: 'POST',
    body: JSON.stringify({
      vk_user_id: vkUserId,
      record_id: recordId,
    }),
  })
}

export function fetchRescheduleSlots(vkUserId: number, recordId: number) {
  const query = new URLSearchParams({
    vk_user_id: String(vkUserId),
    record_id: String(recordId),
  })
  return apiFetch<RescheduleSlotsData>(`/api/records/reschedule-slots?${query}`)
}

export function rescheduleRecord(
  vkUserId: number,
  recordId: number,
  activityId: number,
  activityDate: string | null,
) {
  return apiFetch<RescheduleResult>('/api/records/reschedule', {
    method: 'POST',
    body: JSON.stringify({
      vk_user_id: vkUserId,
      record_id: recordId,
      activity_id: activityId,
      activity_date: activityDate,
    }),
  })
}
