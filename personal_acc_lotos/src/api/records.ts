import type { CancelRecordResult, RecordFilter, RecordsData } from '../types/records'
import { apiFetch } from './client'

export function fetchRecords(vkUserId: number, filter: RecordFilter = 'all') {
  const query = new URLSearchParams({
    vk_user_id: String(vkUserId),
    filter,
  })
  return apiFetch<RecordsData>(`/api/records?${query}`)
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
