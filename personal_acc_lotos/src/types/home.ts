import type { CabinetAbonement } from './cabinet'
import type { UserRecord } from './records'

export type HomeAlert = {
  type: 'low_balance' | 'expiring'
  message: string
  daysLeft?: number
}

export type RebookPrefs = {
  staffId: number
  staffName: string
  serviceTitle: string
  serviceId?: number | null
}

export type HomeRebook = {
  available: boolean
  slotsCount?: number
  prefs?: RebookPrefs
}

export type HomeData = {
  studioName: string
  abonement: CabinetAbonement | null
  nextRecord: UserRecord | null
  alerts: HomeAlert[]
  rebook: HomeRebook
}
