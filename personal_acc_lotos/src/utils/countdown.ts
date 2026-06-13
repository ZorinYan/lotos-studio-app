export type CountdownState = {
  label: string
  /** Число для анимации смены (минуты до старта) */
  tick: number
  isPast: boolean
  isSoon: boolean
}

function pluralizeHours(h: number): string {
  const mod10 = h % 10
  const mod100 = h % 100
  if (mod100 >= 11 && mod100 <= 19) return 'часов'
  if (mod10 === 1) return 'час'
  if (mod10 >= 2 && mod10 <= 4) return 'часа'
  return 'часов'
}

function pluralizeMinutes(m: number): string {
  const mod10 = m % 10
  const mod100 = m % 100
  if (mod100 >= 11 && mod100 <= 19) return 'минут'
  if (mod10 === 1) return 'минута'
  if (mod10 >= 2 && mod10 <= 4) return 'минуты'
  return 'минут'
}

function pluralizeDays(d: number): string {
  const mod10 = d % 10
  const mod100 = d % 100
  if (mod100 >= 11 && mod100 <= 19) return 'дней'
  if (mod10 === 1) return 'день'
  if (mod10 >= 2 && mod10 <= 4) return 'дня'
  return 'дней'
}

export function formatCountdown(startsAt: string | null, now = Date.now()): CountdownState | null {
  if (!startsAt) return null

  const target = Date.parse(startsAt)
  if (Number.isNaN(target)) return null

  const diffMs = target - now
  if (diffMs <= 0) {
    return { label: 'Скоро начнётся', tick: 0, isPast: true, isSoon: true }
  }

  const totalMinutes = Math.floor(diffMs / 60_000)
  const days = Math.floor(diffMs / 86_400_000)
  const hours = Math.floor((diffMs % 86_400_000) / 3_600_000)
  const minutes = Math.floor((diffMs % 3_600_000) / 60_000)

  let label: string
  if (days > 0) {
    if (hours > 0) {
      label = `Через ${days} ${pluralizeDays(days)} ${hours} ${pluralizeHours(hours)}`
    } else {
      label = `Через ${days} ${pluralizeDays(days)}`
    }
  } else if (hours > 0) {
    label = `Через ${hours} ${pluralizeHours(hours)} ${minutes} ${pluralizeMinutes(minutes)}`
  } else if (minutes > 0) {
    label = `Через ${minutes} ${pluralizeMinutes(minutes)}`
  } else {
    const seconds = Math.max(1, Math.floor(diffMs / 1000))
    label = `Через ${seconds} сек`
  }

  return {
    label,
    tick: totalMinutes,
    isPast: false,
    isSoon: diffMs < 3_600_000,
  }
}

export function countdownIntervalMs(startsAt: string | null, now = Date.now()): number {
  if (!startsAt) return 60_000
  const diffMs = Date.parse(startsAt) - now
  if (Number.isNaN(diffMs)) return 60_000
  return diffMs < 3_600_000 ? 1_000 : 30_000
}
