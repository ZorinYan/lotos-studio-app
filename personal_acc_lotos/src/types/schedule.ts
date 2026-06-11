export type ScheduleDayOption = {
  date: string
  label: string
  isToday: boolean
}

export type ScheduleTrainerOption = {
  id: number
  name: string
}

export type ScheduleServiceOption = {
  id: number | null
  title: string
}

export type ScheduleFilterOptions = {
  trainers: ScheduleTrainerOption[]
  services: ScheduleServiceOption[]
}

export type RebookPrefs = {
  staffId: number
  staffName: string
  serviceTitle: string
  serviceId?: number | null
}

export type RebookData = {
  prefs: RebookPrefs
  classes: ScheduleClass[]
}

export type ScheduleClass = {
  id: number
  time: string
  date: string
  dateLabel: string
  serviceTitle: string
  serviceId?: number | null
  trainer: string
  staffId?: number | null
  capacity: number
  booked: number
  freeSpots: number | null
  isFull: boolean
  durationMinutes: number | null
  startsAt: string
  endsAt: string
  comment: string | null
  priceMin?: number | null
  trialPrice?: number | null
  hasTrial?: boolean
  requiresAbonement?: boolean
}

export type GuestCheckResult = {
  allowed: boolean
  reason: 'login_required' | null
  isFirstVisit: boolean
  message: string | null
}

export type BookingEligibility = {
  canBook: boolean
  isTrial: boolean
  requiresAbonement: boolean
  hasAbonement: boolean
  reason: 'abonement_required' | 'trial_unavailable' | null
  message: string | null
}

export type ScheduleData = {
  date: string
  dateLabel: string
  dayLabel: string
  classes: ScheduleClass[]
  days: ScheduleDayOption[]
}

export type BookScheduleResult = {
  success: boolean
  isTrial?: boolean
  phoneDisplay: string
  message: string
  class: ScheduleClass
}
