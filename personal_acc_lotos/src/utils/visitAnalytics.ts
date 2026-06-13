export type MonthlyVisitBucket = {
  key: string
  label: string
  count: number
}

export type VisitRhythm = {
  message: string
  detail: string | null
}

const MONTH_LABELS = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

function parseVisitDate(raw: string): Date | null {
  if (!raw) return null
  const iso = raw.slice(0, 10)
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
    const date = new Date(`${iso}T12:00:00`)
    return Number.isNaN(date.getTime()) ? null : date
  }
  return null
}

function uniqueSortedDates(dateIsos: string[]): Date[] {
  const seen = new Set<string>()
  const dates: Date[] = []

  for (const raw of dateIsos) {
    const date = parseVisitDate(raw)
    if (!date) continue
    const key = date.toISOString().slice(0, 10)
    if (seen.has(key)) continue
    seen.add(key)
    dates.push(date)
  }

  return dates.sort((a, b) => a.getTime() - b.getTime())
}

function monthKey(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}`
}

function weekKey(date: Date): string {
  const copy = new Date(date)
  const day = (copy.getDay() + 6) % 7
  copy.setDate(copy.getDate() - day)
  copy.setHours(12, 0, 0, 0)
  return copy.toISOString().slice(0, 10)
}

export function buildMonthlyVisitBuckets(dateIsos: string[], months = 3): MonthlyVisitBucket[] {
  const now = new Date()
  const buckets: MonthlyVisitBucket[] = []

  for (let offset = months - 1; offset >= 0; offset -= 1) {
    const anchor = new Date(now.getFullYear(), now.getMonth() - offset, 1, 12)
    const key = monthKey(anchor)
    buckets.push({
      key,
      label: MONTH_LABELS[anchor.getMonth()],
      count: 0,
    })
  }

  const bucketMap = new Map(buckets.map((item) => [item.key, item]))

  for (const date of uniqueSortedDates(dateIsos)) {
    const key = monthKey(date)
    const bucket = bucketMap.get(key)
    if (bucket) bucket.count += 1
  }

  return buckets
}

export function computeVisitRhythm(dateIsos: string[]): VisitRhythm | null {
  const dates = uniqueSortedDates(dateIsos)
  if (dates.length === 0) return null

  const now = new Date()
  const fourWeeksAgo = new Date(now)
  fourWeeksAgo.setDate(fourWeeksAgo.getDate() - 28)

  const recent = dates.filter((date) => date >= fourWeeksAgo)
  const weeklyPace = recent.length > 0 ? Math.round((recent.length / 4) * 10) / 10 : 0

  const weeksWithVisits = new Set(dates.map(weekKey))
  const sortedWeeks = [...weeksWithVisits].sort()

  let consecutiveWeeks = 0
  if (sortedWeeks.length > 0) {
    const currentWeek = weekKey(now)
    let cursor = currentWeek
    const weekSet = new Set(sortedWeeks)

    while (weekSet.has(cursor)) {
      consecutiveWeeks += 1
      const prev = new Date(`${cursor}T12:00:00`)
      prev.setDate(prev.getDate() - 7)
      cursor = prev.toISOString().slice(0, 10)
    }
  }

  if (consecutiveWeeks >= 2) {
    const weeksLabel =
      consecutiveWeeks === 1
        ? '1 неделю'
        : consecutiveWeeks < 5
          ? `${consecutiveWeeks} недели`
          : `${consecutiveWeeks} недель`
    return {
      message: `${weeksLabel} подряд в ритме`,
      detail: weeklyPace >= 1 ? `В среднем ${weeklyPace} раза в неделю` : null,
    }
  }

  if (weeklyPace >= 1) {
    const paceRounded = Math.max(1, Math.round(weeklyPace))
    const times =
      paceRounded === 1 ? '1 раз' : paceRounded < 5 ? `${paceRounded} раза` : `${paceRounded} раз`
    return {
      message: `Вы ходите ${times} в неделю`,
      detail: 'Стабильный ритм — отличная практика',
    }
  }

  if (dates.length >= 3) {
    return {
      message: 'Продолжайте практику',
      detail: `${dates.length} визитов в истории`,
    }
  }

  return {
    message: 'Начните свой ритм',
    detail: 'Каждый визит — шаг к привычке',
  }
}

export function collectVisitDateIsos(
  visitHistory: Array<{ dateIso: string }>,
  recentVisits: Array<{ dateIso?: string | null }>,
  usageVisits: Array<{ dateIso?: string | null }>,
): string[] {
  const values: string[] = []
  for (const item of visitHistory) values.push(item.dateIso)
  for (const item of recentVisits) {
    if (item.dateIso) values.push(item.dateIso)
  }
  for (const item of usageVisits) {
    if (item.dateIso) values.push(item.dateIso)
  }
  return values
}

export function estimateAbonementProgress(
  remaining: number | null,
  total: number | null,
): number {
  if (remaining == null || remaining < 0) return 0
  if (total != null && total > 0) {
    return Math.max(0, Math.min(remaining / total, 1))
  }
  return Math.max(0.12, Math.min(remaining / 12, 1))
}
