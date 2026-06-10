import { useState } from 'react'
import { bookScheduleClass } from '../../api/schedule'
import { ApiError } from '../../api/client'
import type { BookScheduleResult, ScheduleClass } from '../../types/schedule'
import { AddToCalendarButton } from './AddToCalendarButton'
import './ScheduleClassModal.css'

type ModalMode = 'details' | 'confirm' | 'success'

type ScheduleClassModalProps = {
  item: ScheduleClass
  dayLabel: string
  vkUserId: number
  studioName: string
  onClose: () => void
  onBooked: () => void
  onError: (message: string) => void
}

export function ScheduleClassModal({
  item,
  dayLabel,
  vkUserId,
  studioName,
  onClose,
  onBooked,
  onError,
}: ScheduleClassModalProps) {
  const [mode, setMode] = useState<ModalMode>('details')
  const [booking, setBooking] = useState(false)
  const [result, setResult] = useState<BookScheduleResult | null>(null)

  const isFull = item.isFull
  const canBook = !isFull

  const handleClose = () => {
    if (booking) return
    if (mode === 'success') {
      onBooked()
    }
    onClose()
  }

  const handleBook = async () => {
    setBooking(true)
    try {
      const response = await bookScheduleClass(vkUserId, item.id, item.date)
      setResult(response)
      setMode('success')
    } catch (err) {
      onError(err instanceof ApiError ? err.message : 'Не удалось записаться на занятие')
      setMode('details')
    } finally {
      setBooking(false)
    }
  }

  return (
    <div className="schedule-modal" role="dialog" aria-modal="true" aria-labelledby="schedule-modal-title">
      <button
        type="button"
        className="schedule-modal__backdrop"
        aria-label="Закрыть"
        onClick={handleClose}
        disabled={booking}
      />
      <div className="schedule-modal__sheet lotos-card">
        <div className="schedule-modal__handle" aria-hidden="true" />
        <button
          type="button"
          className="schedule-modal__close"
          onClick={handleClose}
          aria-label="Закрыть"
          disabled={booking}
        >
          ×
        </button>

        {mode === 'success' && result ? (
          <div className="schedule-modal__success">
            <div className="schedule-modal__success-icon" aria-hidden="true">✓</div>
            <h2 className="schedule-modal__success-title">Вы записаны!</h2>
            <p className="schedule-modal__success-text">{result.message}</p>
            <dl className="schedule-modal__success-summary">
              <div className="schedule-modal__detail">
                <dt>Занятие</dt>
                <dd>{result.class.serviceTitle}</dd>
              </div>
              <div className="schedule-modal__detail">
                <dt>Дата и время</dt>
                <dd>
                  {result.class.dateLabel}, {result.class.time}
                </dd>
              </div>
              <div className="schedule-modal__detail">
                <dt>Тренер</dt>
                <dd>{result.class.trainer}</dd>
              </div>
              <div className="schedule-modal__detail">
                <dt>Телефон</dt>
                <dd>{result.phoneDisplay}</dd>
              </div>
            </dl>
            <p className="schedule-modal__hint">До встречи в студии</p>
            <div className="schedule-modal__actions schedule-modal__actions--stacked">
              <AddToCalendarButton
                stretched
                event={{
                  title: result.class.serviceTitle,
                  startsAt: result.class.startsAt,
                  endsAt: result.class.endsAt,
                  trainer: result.class.trainer,
                  studioName,
                }}
              />
              <button
                type="button"
                className="lotos-btn lotos-btn--primary lotos-btn--stretched"
                onClick={handleClose}
              >
                Отлично
              </button>
            </div>
          </div>
        ) : (
          <>
            <header className="schedule-modal__header">
              <p className="schedule-modal__eyebrow">{dayLabel} · {item.time}</p>
              <h2 id="schedule-modal-title" className="schedule-modal__title">
                {item.serviceTitle}
              </h2>
              <span
                className={`schedule-modal__status schedule-modal__status--${
                  isFull ? 'full' : 'free'
                }`}
              >
                {isFull ? 'Нет мест' : 'Есть свободные места'}
              </span>
            </header>

            {mode === 'confirm' ? (
              <section className="schedule-modal__section">
                <h3 className="lotos-section-title">Подтвердите запись</h3>
                <p className="schedule-modal__confirm-text">
                  Записать вас на «{item.serviceTitle}» {item.dateLabel} в {item.time}?
                  Тренер: {item.trainer}.
                </p>
                <div className="schedule-modal__actions">
                  <button
                    type="button"
                    className="lotos-btn lotos-btn--secondary"
                    disabled={booking}
                    onClick={() => setMode('details')}
                  >
                    Назад
                  </button>
                  <button
                    type="button"
                    className="lotos-btn lotos-btn--primary"
                    disabled={booking}
                    onClick={() => void handleBook()}
                  >
                    {booking ? 'Записываем…' : 'Подтвердить'}
                  </button>
                </div>
              </section>
            ) : (
              <>
                <section className="schedule-modal__section">
                  <h3 className="lotos-section-title">Детали занятия</h3>
                  <dl className="schedule-modal__details">
                    <div className="schedule-modal__detail">
                      <dt>Тренер</dt>
                      <dd>{item.trainer}</dd>
                    </div>
                    <div className="schedule-modal__detail">
                      <dt>Дата</dt>
                      <dd>{item.dateLabel}</dd>
                    </div>
                    <div className="schedule-modal__detail">
                      <dt>Время</dt>
                      <dd>{item.time}</dd>
                    </div>
                    {item.durationMinutes != null && item.durationMinutes > 0 && (
                      <div className="schedule-modal__detail">
                        <dt>Длительность</dt>
                        <dd>{item.durationMinutes} мин</dd>
                      </div>
                    )}
                    {item.capacity > 0 && (
                      <>
                        <div className="schedule-modal__detail">
                          <dt>Всего мест</dt>
                          <dd>{item.capacity}</dd>
                        </div>
                        <div className="schedule-modal__detail">
                          <dt>Занято</dt>
                          <dd>{item.booked}</dd>
                        </div>
                        <div className="schedule-modal__detail">
                          <dt>Свободно</dt>
                          <dd>{isFull ? '0' : String(item.freeSpots ?? 0)}</dd>
                        </div>
                      </>
                    )}
                  </dl>
                </section>

                {item.comment && (
                  <section className="schedule-modal__section">
                    <h3 className="lotos-section-title">О занятии</h3>
                    <p className="schedule-modal__comment">{item.comment}</p>
                  </section>
                )}

                {isFull ? (
                  <p className="schedule-modal__hint schedule-modal__hint--muted">
                    Группа заполнена. Выберите другое время или напишите администратору студии.
                  </p>
                ) : null}

                <div className="schedule-modal__actions schedule-modal__actions--stacked">
                  {canBook && (
                    <button
                      type="button"
                      className="lotos-btn lotos-btn--primary lotos-btn--stretched"
                      onClick={() => setMode('confirm')}
                    >
                      Записаться
                    </button>
                  )}
                  <button
                    type="button"
                    className={`lotos-btn lotos-btn--${canBook ? 'secondary' : 'primary'} lotos-btn--stretched`}
                    onClick={handleClose}
                  >
                    Закрыть
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
