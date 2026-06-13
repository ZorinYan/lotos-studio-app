import { useState } from 'react'
import { downloadCalendarEvent, openGoogleCalendar, type CalendarEventInput } from '../../utils/calendar'
import './AddToCalendarButton.css'

type AddToCalendarButtonProps = {
  event: CalendarEventInput
  stretched?: boolean
  label?: string
}

export function AddToCalendarButton({
  event,
  stretched = false,
  label = 'Добавить в календарь',
}: AddToCalendarButtonProps) {
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDownload = () => {
    try {
      setError(null)
      downloadCalendarEvent(event)
      setOpen(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать событие')
    }
  }

  const handleGoogle = () => {
    try {
      setError(null)
      openGoogleCalendar(event)
      setOpen(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось открыть календарь')
    }
  }

  if (!event.startsAt || !event.endsAt) {
    return null
  }

  return (
    <div className={`calendar-btn${stretched ? ' calendar-btn--stretched' : ''}`}>
      <button
        type="button"
        className={`lotos-btn lotos-btn--secondary${stretched ? ' lotos-btn--stretched' : ''}`}
        onClick={() => setOpen((value) => !value)}
      >
        {label}
      </button>

      {open && (
        <div className="calendar-btn__menu lotos-card">
          <button type="button" className="calendar-btn__option" onClick={handleDownload}>
            Скачать .ics
          </button>
          <button type="button" className="calendar-btn__option" onClick={handleGoogle}>
            Google Календарь
          </button>
        </div>
      )}

      {error && <p className="calendar-btn__error">{error}</p>}
    </div>
  )
}
