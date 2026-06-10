export type RecordFilter = 'all' | 'upcoming' | 'past'

export type RecordService = {
  id?: number
  title: string
}

export type UserRecord = {
  id: number
  datetime: string
  date: string | null
  time: string | null
  dateLabel: string | null
  service: string
  services: RecordService[]
  staff: string
  staffId?: number
  attendance: string
  attendanceCode: number
  durationMinutes: number | null
  startsAt: string | null
  endsAt: string | null
  comment: string | null
  activityId?: number
  isUpcoming: boolean
  canCancel: boolean
}

export type RecordsData = {
  filter: RecordFilter
  records: UserRecord[]
  counts: {
    all: number
    upcoming: number
    past: number
  }
}

export type CancelRecordResult = {
  success: boolean
  message: string
  record: UserRecord
}
