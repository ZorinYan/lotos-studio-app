import type { CabinetAbonement } from './cabinet'
import type { UserRecord } from './records'

export type HomeHintAction =
  | 'schedule'
  | 'contact_renew'
  | 'contact_freeze'
  | 'contact_reschedule'
  | 'contact_payment'
  | 'rebook'
  | 'help'

export type HomeHint = {
  type: 'low_balance' | 'expiring' | 'inactive'
  message: string
  detail?: string
  action: HomeHintAction
  actionLabel: string
  daysLeft?: number
}

export type RhythmPlan = {
  message: string
  detail: string | null
  slotsCount: number
  nextDateLabel: string | null
  serviceTitle: string | null
  staffName: string | null
  weekdayPattern: string | null
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
  alerts: HomeHint[]
  rhythmPlan: RhythmPlan | null
  isFirstVisit: boolean
  rebook: HomeRebook
}

/** @deprecated use HomeHint */
export type HomeAlert = HomeHint
