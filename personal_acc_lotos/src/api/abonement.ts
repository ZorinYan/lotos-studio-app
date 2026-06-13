import type { CabinetAbonement } from '../types/cabinet'
import type { HomeAlert } from '../types/home'
import { apiFetch } from './client'

export type AbonementsData = {
  abonements: CabinetAbonement[]
  primary: CabinetAbonement | null
  alerts: HomeAlert[]
}

/** Остаток занятий — всегда без кэша на сервере. */
export function fetchAbonements(vkUserId: number) {
  return apiFetch<AbonementsData>(`/api/abonement?vk_user_id=${vkUserId}`)
}
