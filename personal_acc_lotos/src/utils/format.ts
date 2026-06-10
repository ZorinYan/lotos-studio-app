/** Склонение «занятие» */
export function pluralizeLessons(count: number): string {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 19) return 'занятий'
  if (mod10 === 1) return 'занятие'
  if (mod10 >= 2 && mod10 <= 4) return 'занятия'
  return 'занятий'
}

/** Убирает эмодзи и лишние пробелы из строк статуса YClients */
export function cleanLabel(raw: string): string {
  return raw
    .replace(/[\u{1F300}-\u{1FAFF}\u2600-\u27BF]/gu, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export type AttendanceTone = 'waiting' | 'confirmed' | 'done' | 'missed' | 'neutral'

export function parseAttendance(raw: string): { label: string; tone: AttendanceTone } {
  const text = cleanLabel(raw).toLowerCase()
  if (text.includes('приш')) return { label: 'Пришёл', tone: 'done' }
  if (text.includes('подтверд')) return { label: 'Подтверждено', tone: 'confirmed' }
  if (text.includes('ожида')) return { label: 'Ожидаем', tone: 'waiting' }
  if (text.includes('не приш')) return { label: 'Не пришёл', tone: 'missed' }
  return { label: cleanLabel(raw) || 'Запись', tone: 'neutral' }
}

export type AbonementStatusTone = 'active' | 'frozen' | 'expired' | 'neutral'

export function parseAbonementStatus(status: string): { label: string; tone: AbonementStatusTone } {
  const text = status.toLowerCase()
  if (text.includes('замороз')) return { label: status, tone: 'frozen' }
  if (text.includes('просроч') || text.includes('законч') || text.includes('архив')) {
    return { label: status, tone: 'expired' }
  }
  if (text.includes('актив')) return { label: status, tone: 'active' }
  return { label: status, tone: 'neutral' }
}

/** Разбивает «Пн, 10 июня · 18:30» на дату и время */
export function splitDateTime(datetime: string): { date: string; time: string | null } {
  const parts = datetime.split('·').map((p) => p.trim())
  if (parts.length >= 2) {
    return { date: parts[0], time: parts[1] }
  }
  return { date: datetime, time: null }
}

export function formatMoney(amount: number): string {
  return `${amount.toLocaleString('ru-RU')} ₽`
}
