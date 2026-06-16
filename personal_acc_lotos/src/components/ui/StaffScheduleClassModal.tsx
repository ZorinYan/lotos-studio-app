import { Snackbar } from '@vkontakte/vkui'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useModalOverlay } from '../../hooks/useModalOverlay'
import type { ScheduleClass } from '../../types/schedule'
import { fetchStaffActivityClients, type StaffActivityClient } from '../../api/staff'
import './StaffScheduleClassModal.css'

type StaffScheduleClassModalProps = {
  item: ScheduleClass
  dayLabel: string
  vkUserId: number
  studioName: string
  onClose: () => void
}

export function StaffScheduleClassModal({
  item,
  dayLabel,
  vkUserId,
  studioName,
  onClose,
}: StaffScheduleClassModalProps) {
  const sheetRef = useRef<HTMLDivElement>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [clients, setClients] = useState<StaffActivityClient[]>([])

  const isFull = item.isFull
  const bookedCount = item.booked ?? 0

  useModalOverlay(onClose, sheetRef)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setClients([])

    void (async () => {
      try {
        const res = await fetchStaffActivityClients(vkUserId, item.id, item.date)
        if (!cancelled) setClients(res.clients)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Не удалось загрузить клиентов')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [vkUserId, item.id, item.date])

  const clientsSorted = useMemo(() => {
    return [...clients].sort((a, b) => a.fullName.localeCompare(b.fullName, 'ru'))
  }, [clients])

  return (
    <div className="schedule-modal lotos-modal" role="dialog" aria-modal="true">
      <button
        type="button"
        className="schedule-modal__backdrop"
        aria-label="Закрыть"
        onClick={onClose}
        disabled={loading}
      />
      <div ref={sheetRef} className="schedule-modal__sheet lotos-modal__sheet lotos-card">
        <div className="schedule-modal__handle" aria-hidden="true" />
        <button
          type="button"
          className="schedule-modal__close"
          onClick={onClose}
          aria-label="Закрыть"
          disabled={loading}
        >
          ×
        </button>

        <header className="schedule-modal__header">
          <p className="schedule-modal__eyebrow">
            {dayLabel} · {item.time}
          </p>
          <h2 className="schedule-modal__title">{item.serviceTitle}</h2>
          <span className={`schedule-modal__status ${isFull ? 'full' : 'free'}`}>
            {isFull ? 'Нет мест' : 'Есть свободные места'}
          </span>
          <div className="schedule-modal__prices">
            <span className="schedule-modal__price">{studioName}</span>
            <span className="schedule-modal__price">{bookedCount} записей</span>
          </div>
        </header>

        <section className="schedule-modal__section">
          <h3 className="lotos-section-title">Информация о занятии</h3>
          <dl className="schedule-modal__details">
            <div className="schedule-modal__detail">
              <dt>Тренер</dt>
              <dd>{item.trainer}</dd>
            </div>
            <div className="schedule-modal__detail">
              <dt>Дата</dt>
              <dd>{item.dateLabel}</dd>
            </div>
            {item.durationMinutes != null && item.durationMinutes > 0 && (
              <div className="schedule-modal__detail">
                <dt>Длительность</dt>
                <dd>{item.durationMinutes} мин</dd>
              </div>
            )}
            {item.comment && (
              <div className="schedule-modal__detail">
                <dt>Комментарий</dt>
                <dd>{item.comment}</dd>
              </div>
            )}
          </dl>
        </section>

        <section className="schedule-modal__section staff-schedule-modal__clients">
          <h3 className="lotos-section-title">Записанные клиенты</h3>

          {loading ? (
            <p className="staff-schedule-modal__hint">Загружаем список…</p>
          ) : clientsSorted.length === 0 ? (
            <p className="staff-schedule-modal__hint staff-schedule-modal__hint--muted">
              На это занятие пока никто не записан.
            </p>
          ) : (
            <ul className="staff-schedule-modal__list">
              {clientsSorted.map((c) => (
                <li key={c.clientId} className="staff-schedule-modal__row">
                  <div className="staff-schedule-modal__name">{c.fullName}</div>
                  {c.phoneDisplay && (
                    <div className="staff-schedule-modal__phone">{c.phoneDisplay}</div>
                  )}
                  <div className="staff-schedule-modal__visits">
                    Визитов к тренеру: {c.visitsToTrainer}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {error && (
          <Snackbar onClose={() => setError(null)} duration={5000}>
            {error}
          </Snackbar>
        )}
      </div>
    </div>
  )
}

