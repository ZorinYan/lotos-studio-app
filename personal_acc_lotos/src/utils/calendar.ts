export type CalendarEventInput = {
  title: string
  startsAt: string
  endsAt: string
  trainer?: string
  studioName?: string
  note?: string
}

function escapeIcs(value: string): string {
  return value
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n')
}

function toIcsUtc(date: Date): string {
  return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')
}

function buildDescription(event: CalendarEventInput): string {
  const lines = [
    event.trainer ? `Тренер: ${event.trainer}` : null,
    event.note ?? null,
    'Lotos Studio',
  ].filter(Boolean)
  return lines.join('\n')
}

export function buildIcsContent(event: CalendarEventInput): string {
  const start = new Date(event.startsAt)
  const end = new Date(event.endsAt)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    throw new Error('Некорректная дата занятия')
  }

  const uid = `${start.getTime()}-${event.title.replace(/\s+/g, '-').toLowerCase()}@lotos-studio`
  const description = buildDescription(event)

  return [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Lotos Studio//RU',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:${escapeIcs(uid)}`,
    `DTSTAMP:${toIcsUtc(new Date())}`,
    `DTSTART:${toIcsUtc(start)}`,
    `DTEND:${toIcsUtc(end)}`,
    `SUMMARY:${escapeIcs(event.title)}`,
    `DESCRIPTION:${escapeIcs(description)}`,
    event.studioName ? `LOCATION:${escapeIcs(event.studioName)}` : null,
    'END:VEVENT',
    'END:VCALENDAR',
  ]
    .filter(Boolean)
    .join('\r\n')
}

export function downloadCalendarEvent(event: CalendarEventInput, filename = 'lotos-zanyatie.ics') {
  const content = buildIcsContent(event)
  const blob = new Blob([content], { type: 'text/calendar;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function openGoogleCalendar(event: CalendarEventInput) {
  const start = new Date(event.startsAt)
  const end = new Date(event.endsAt)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    throw new Error('Некорректная дата занятия')
  }

  const formatGoogle = (date: Date) => date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: event.title,
    dates: `${formatGoogle(start)}/${formatGoogle(end)}`,
    details: buildDescription(event),
  })
  if (event.studioName) {
    params.set('location', event.studioName)
  }

  window.open(`https://calendar.google.com/calendar/render?${params.toString()}`, '_blank', 'noopener,noreferrer')
}
