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
  phoneDisplay: string
  message: string
  class: ScheduleClass
}
