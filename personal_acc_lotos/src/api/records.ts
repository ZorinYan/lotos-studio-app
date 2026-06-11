import type { CancelRecordResult, RecordFilter, RecordsData } from '../types/records'
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
