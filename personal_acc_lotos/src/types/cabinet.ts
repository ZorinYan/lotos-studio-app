import type { UserRecord } from './records'

export type CabinetProfile = {
  name: string
  phone: string
  phoneDisplay: string
  visits: number
  spent: number
  discount: number
  firstVisitDate: string | null
  lastVisitDate: string | null
}

export type AbonementServiceBalance = {
  title: string
  remaining: number
}

export type AbonementUsageVisit = {
  datetime: string
  service: string
  staff: string
}

export type CabinetAbonement = {
  id?: number
  title: string
  balanceRemaining: number | null
  services: AbonementServiceBalance[]
  isUnitedBalance: boolean
  status: string
  statusIcon: string
  number: string
  expiry: string | null
  expiryDate: string | null
  activatedDate: string | null
  createdDate: string | null
  isFrozen: boolean
  allowFreeze: boolean
  freezeLimit: number | null
  typeCost: number | null
  freezeLines: string[]
}

export type CabinetVisit = {
  date: string
  service: string
  staff: string
}

export type CabinetData = {
  profile: CabinetProfile
  abonements: CabinetAbonement[]
  abonementUsageVisits: AbonementUsageVisit[]
  upcomingRecords: UserRecord[]
  recentVisits: CabinetVisit[]
}
