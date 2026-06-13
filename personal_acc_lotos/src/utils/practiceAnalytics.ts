import type { CabinetProfile, CabinetVisit, AbonementUsageVisit, VisitHistoryEntry } from '../types/cabinet'
import {
  buildMonthlyVisitBuckets,
  computeVisitRhythm,
  type MonthlyVisitBucket,
  type VisitRhythm,
} from './visitAnalytics'

export type PracticeVisit = {
  dateIso: string
  service: string
}

export type ServiceBucket = {
  title: string
  count: number
}

export type HeatmapWeek = {
  key: string
  days: number[]
}

export type HeatmapData = {
  weeks: HeatmapWeek[]
  dayLabels: string[]
}

export type WeeklyStripBucket = {
  key: string
  label: string
  count: number
  level: 0 | 1 | 2
}

export type WeeklyTrendPoint = {
  key: string
  label: string
  count: number
}

export type MonthComparison = {
  delta: number
  text: string
}

export type MonthlyGoal = {
  current: number
  goal: number
  progress: number
}

export type PracticeDashboardData = {
  tenureLine: string | null
  monthComparison: MonthComparison | null
  monthlyBuckets: MonthlyVisitBucket[]
  serviceBuckets: ServiceBucket[]
  heatmap: HeatmapData
  weeklyStrip: WeeklyStripBucket[]
  monthlyGoal: MonthlyGoal | null
  weeklyTrend: WeeklyTrendPoint[]
  rhythm: VisitRhythm | null
  hasActivity: boolean
}

const DAY_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const MONTH_GENITIVE = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
]

function parseIsoDate(raw: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return null
  const date = new Date(`${raw}T12:00:00`)
  return Number.isNaN(date.getTime()) ? null : date
}

function isoFromDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function startOfWeekMonday(date: Date): Date {
  const copy = new Date(date)
  const day = (copy.getDay() + 6) % 7
  copy.setDate(copy.getDate() - day)
  copy.setHours(12, 0, 0, 0)
  return copy
}

function monthKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

export function collectPracticeVisits(
  visitHistory: VisitHistoryEntry[],
  recentVisits: CabinetVisit[],
  usageVisits: AbonementUsageVisit[],
): PracticeVisit[] {
  const seen = new Set<string>()
  const visits: PracticeVisit[] = []

  const push = (dateIso: string | null | undefined, service: string) => {
    if (!dateIso) return
    const key = `${dateIso}|${service}`
    if (seen.has(key)) return
    seen.add(key)
    visits.push({ dateIso, service: service || 'Занятие' })
  }

  for (const item of visitHistory) push(item.dateIso, item.service ?? 'Занятие')
  for (const item of recentVisits) push(item.dateIso, item.service)
  for (const item of usageVisits) push(item.dateIso, item.service)

  return visits.sort((a, b) => a.dateIso.localeCompare(b.dateIso))
}

function visitsPerDay(visits: PracticeVisit[]): Map<string, number> {
  const map = new Map<string, number>()
  for (const visit of visits) {
    map.set(visit.dateIso, (map.get(visit.dateIso) ?? 0) + 1)
  }
  return map
}

function formatTenureLine(profile: CabinetProfile, visits: PracticeVisit[]): string | null {
  const total = profile.visits > 0 ? profile.visits : visits.length
  if (total === 0) return null

  let earliest: Date | null = null
  for (const visit of visits) {
    const date = parseIsoDate(visit.dateIso)
    if (!date) continue
    if (!earliest || date < earliest) earliest = date
  }

  if (!earliest) {
    if (profile.firstVisitDate) {
      return `В Lotos · ${total} ${pluralVisits(total)}`
    }
    return null
  }

  const month = MONTH_GENITIVE[earliest.getMonth()]
  const year = earliest.getFullYear()
  return `В Lotos с ${month} ${year} · ${total} ${pluralVisits(total)}`
}

function pluralVisits(count: number): string {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 19) return 'визитов'
  if (mod10 === 1) return 'визит'
  if (mod10 >= 2 && mod10 <= 4) return 'визита'
  return 'визитов'
}

export function computeMonthComparison(dateIsos: string[]): MonthComparison | null {
  const now = new Date()
  const currentKey = monthKey(now)
  const prev = new Date(now.getFullYear(), now.getMonth() - 1, 1, 12)
  const prevKey = monthKey(prev)

  let current = 0
  let previous = 0

  for (const raw of dateIsos) {
    const date = parseIsoDate(raw)
    if (!date) continue
    const key = monthKey(date)
    if (key === currentKey) current += 1
    if (key === prevKey) previous += 1
  }

  if (current === 0 && previous === 0) return null

  const delta = current - previous
  if (delta > 0) {
    return { delta, text: `+${delta} к прошлому месяцу` }
  }
  if (delta < 0) {
    return { delta, text: `${delta} к прошлому месяцу` }
  }
  return { delta: 0, text: 'Как в прошлом месяце' }
}

export function buildServiceBuckets(visits: PracticeVisit[], limit = 5): ServiceBucket[] {
  const counts = new Map<string, number>()
  for (const visit of visits) {
    const title = visit.service.trim() || 'Занятие'
    counts.set(title, (counts.get(title) ?? 0) + 1)
  }

  return [...counts.entries()]
    .map(([title, count]) => ({ title, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
}

export function buildActivityHeatmap(visits: PracticeVisit[], weeks = 16): HeatmapData {
  const perDay = visitsPerDay(visits)
  const now = new Date()
  const endWeek = startOfWeekMonday(now)
  const startWeek = new Date(endWeek)
  startWeek.setDate(startWeek.getDate() - (weeks - 1) * 7)

  const heatmapWeeks: HeatmapWeek[] = []

  for (let w = 0; w < weeks; w += 1) {
    const weekStart = new Date(startWeek)
    weekStart.setDate(weekStart.getDate() + w * 7)
    const days: number[] = []

    for (let d = 0; d < 7; d += 1) {
      const day = new Date(weekStart)
      day.setDate(day.getDate() + d)
      if (day > now) {
        days.push(0)
        continue
      }
      const count = perDay.get(isoFromDate(day)) ?? 0
      days.push(count >= 3 ? 3 : count)
    }

    heatmapWeeks.push({
      key: isoFromDate(weekStart),
      days,
    })
  }

  return { weeks: heatmapWeeks, dayLabels: DAY_LABELS }
}

export function buildWeeklyStrip(visits: PracticeVisit[], weeks = 8): WeeklyStripBucket[] {
  const perDay = visitsPerDay(visits)
  const now = new Date()
  const endWeek = startOfWeekMonday(now)
  const buckets: WeeklyStripBucket[] = []

  for (let offset = weeks - 1; offset >= 0; offset -= 1) {
    const weekStart = new Date(endWeek)
    weekStart.setDate(weekStart.getDate() - offset * 7)
    let count = 0
    for (let d = 0; d < 7; d += 1) {
      const day = new Date(weekStart)
      day.setDate(day.getDate() + d)
      if (day > now) continue
      count += perDay.get(isoFromDate(day)) ?? 0
    }

    const label = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' }).format(weekStart)
    const level: 0 | 1 | 2 = count === 0 ? 0 : count === 1 ? 1 : 2

    buckets.push({
      key: isoFromDate(weekStart),
      label,
      count,
      level,
    })
  }

  return buckets
}

export function buildWeeklyTrend(visits: PracticeVisit[], weeks = 12): WeeklyTrendPoint[] {
  const perDay = visitsPerDay(visits)
  const now = new Date()
  const endWeek = startOfWeekMonday(now)
  const points: WeeklyTrendPoint[] = []

  for (let offset = weeks - 1; offset >= 0; offset -= 1) {
    const weekStart = new Date(endWeek)
    weekStart.setDate(weekStart.getDate() - offset * 7)
    let count = 0
    for (let d = 0; d < 7; d += 1) {
      const day = new Date(weekStart)
      day.setDate(day.getDate() + d)
      if (day > now) continue
      count += perDay.get(isoFromDate(day)) ?? 0
    }

    points.push({
      key: isoFromDate(weekStart),
      label: new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' }).format(weekStart),
      count,
    })
  }

  return points
}

export function computeMonthlyGoal(visits: PracticeVisit[]): MonthlyGoal | null {
  const now = new Date()
  const currentKey = monthKey(now)
  let current = 0
  const monthCounts = new Map<string, number>()

  for (const visit of visits) {
    const date = parseIsoDate(visit.dateIso)
    if (!date) continue
    const key = monthKey(date)
    monthCounts.set(key, (monthCounts.get(key) ?? 0) + 1)
    if (key === currentKey) current += 1
  }

  const priorMonths: number[] = []
  for (let offset = 1; offset <= 3; offset += 1) {
    const anchor = new Date(now.getFullYear(), now.getMonth() - offset, 1, 12)
    priorMonths.push(monthCounts.get(monthKey(anchor)) ?? 0)
  }

  const nonZero = priorMonths.filter((value) => value > 0)
  const avg = nonZero.length > 0
    ? nonZero.reduce((sum, value) => sum + value, 0) / nonZero.length
    : 0
  const goal = Math.max(1, Math.round(avg) || 4)
  const progress = Math.max(0, Math.min(current / goal, 1))

  if (current === 0 && priorMonths.every((value) => value === 0)) {
    return null
  }

  return { current, goal, progress }
}

export function buildPracticeDashboard(
  profile: CabinetProfile,
  visitHistory: VisitHistoryEntry[],
  recentVisits: CabinetVisit[],
  usageVisits: AbonementUsageVisit[],
): PracticeDashboardData {
  const practiceVisits = collectPracticeVisits(visitHistory, recentVisits, usageVisits)
  const dateIsos = practiceVisits.map((item) => item.dateIso)

  return {
    tenureLine: formatTenureLine(profile, practiceVisits),
    monthComparison: computeMonthComparison(dateIsos),
    monthlyBuckets: buildMonthlyVisitBuckets(dateIsos, 3),
    serviceBuckets: buildServiceBuckets(practiceVisits),
    heatmap: buildActivityHeatmap(practiceVisits),
    weeklyStrip: buildWeeklyStrip(practiceVisits),
    monthlyGoal: computeMonthlyGoal(practiceVisits),
    weeklyTrend: buildWeeklyTrend(practiceVisits),
    rhythm: computeVisitRhythm(dateIsos),
    hasActivity: practiceVisits.length > 0 || profile.visits > 0,
  }
}
