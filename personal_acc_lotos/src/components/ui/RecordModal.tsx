import { useState } from 'react'
import { cancelRecord } from '../../api/records'
import { ApiError } from '../../api/client'
import type { CancelRecordResult, UserRecord } from '../../types/records'
import { parseAttendance } from '../../utils/format'
import { AddToCalendarButton } from './AddToCalendarButton'
import './RecordModal.css'

type ModalMode = 'details' | 'confirm' | 'success'

type RecordModalProps = {
  record: UserRecord
  vkUserId: number
  studioName: string
  onClose: () => void
  onCancelled: () => void
  onError: (message: string) => void
}

export function RecordModal({
  record,
  vkUserId,
  studioName,
  onClose,
  onCancelled,
  onError,
}: RecordModalProps) {
  const [mode, setMode] = useState<ModalMode>('details')
  const [cancelling, setCancelling] = useState(false)
  const [result, setResult] = useState<CancelRecordResult | null>(null)

  const attendance = parseAttendance(record.attendance)
  const canCancel = record.canCancel

  const handleClose = () => {
    if (cancelling) return
    if (mode === 'success') {
      onCancelled()
    }
    onClose()
  }

  const handleCancel = async () => {
    setCancelling(true)
    try {
      const response = await cancelRecord(vkUserId, record.id)
      setResult(response)
      setMode('success')
    } catch (err) {
      onError(err instanceof ApiError ? err.message : 'Не удалось отменить запись')
      setMode('details')
    } finally {
      setCancelling(false)
    }
  }

  return (
    <div className="record-modal" role="dialog" aria-modal="true" aria-labelledby="record-modal-title">
      <button
        type="button"
        className="record-modal__backdrop"
        aria-label="Закрыть"
        onClick={handleClose}
        disabled={cancelling}
      />
      <div className="record-modal__sheet lotos-card">
        <div className="record-modal__handle" aria-hidden="true" />
        <button
          type="button"
          className="record-modal__close"
          onClick={handleClose}
          aria-label="Закрыть"
          disabled={cancelling}
        >
          ×
        </button>

        {mode === 'success' && result ? (
          <div className="record-modal__success">
            <div className="record-modal__success-icon" aria-hidden="true">✓</div>
            <h2 className="record-modal__success-title">Запись отменена</h2>
            <p className="record-modal__success-text">{result.message}</p>
            <dl className="record-modal__success-summary">
              <div className="record-modal__detail">
                <dt>Занятие</dt>
                <dd>{result.record.service}</dd>
              </div>
              <div className="record-modal__detail">
                <dt>Дата и время</dt>
                <dd>{result.record.datetime}</dd>
              </div>
              <div className="record-modal__detail">
                <dt>Тренер</dt>
                <dd>{result.record.staff}</dd>
              </div>
            </dl>
            <p className="record-modal__hint">Ждём вас на других занятиях</p>
            <button
              type="button"
              className="lotos-btn lotos-btn--primary lotos-btn--stretched"
              onClick={handleClose}
            >
              Понятно
            </button>
          </div>
        ) : (
          <>
            <header className="record-modal__header">
              <p className="record-modal__eyebrow">
                {record.isUpcoming ? 'Предстоящая запись' : 'Прошедшая запись'}
                {record.time ? ` · ${record.time}` : ''}
              </p>
              <h2 id="record-modal-title" className="record-modal__title">
                {record.service}
              </h2>
              <span className={`record-modal__status record-modal__status--${attendance.tone}`}>
                {attendance.label}
              </span>
            </header>

            {mode === 'confirm' ? (
              <section className="record-modal__section">
                <h3 className="lotos-section-title">Подтвердите отмену</h3>
                <p className="record-modal__confirm-text">
                  Отменить запись на «{record.service}» {record.datetime}? Тренер: {record.staff}.
                </p>
                <div className="record-modal__actions">
                  <button
                    type="button"
                    className="lotos-btn lotos-btn--secondary"
                    disabled={cancelling}
                    onClick={() => setMode('details')}
                  >
                    Назад
                  </button>
                  <button
                    type="button"
                    className="lotos-btn lotos-btn--danger"
                    disabled={cancelling}
                    onClick={() => void handleCancel()}
                  >
                    {cancelling ? 'Отменяем…' : 'Да, отменить'}
                  </button>
                </div>
              </section>
            ) : (
              <>
                <section className="record-modal__section">
                  <h3 className="lotos-section-title">Детали записи</h3>
                  <dl className="record-modal__details">
                    <div className="record-modal__detail">
                      <dt>Тренер</dt>
                      <dd>{record.staff}</dd>
                    </div>
                    <div className="record-modal__detail">
                      <dt>Дата</dt>
                      <dd>{record.dateLabel ?? record.datetime}</dd>
                    </div>
                    {record.time && (
                      <div className="record-modal__detail">
                        <dt>Время</dt>
                        <dd>{record.time}</dd>
                      </div>
                    )}
                    {record.durationMinutes != null && record.durationMinutes > 0 && (
                      <div className="record-modal__detail">
                        <dt>Длительность</dt>
                        <dd>{record.durationMinutes} мин</dd>
                      </div>
                    )}
                    <div className="record-modal__detail">
                      <dt>Статус</dt>
                      <dd>{attendance.label}</dd>
                    </div>
                    {record.services.length > 1 && (
                      <div className="record-modal__detail">
                        <dt>Услуги</dt>
                        <dd>{record.services.map((item) => item.title).join(', ')}</dd>
                      </div>
                    )}
                  </dl>
                </section>

                {record.comment && (
                  <section className="record-modal__section">
                    <h3 className="lotos-section-title">Комментарий</h3>
                    <p className="record-modal__comment">{record.comment}</p>
                  </section>
                )}

                <div className="record-modal__actions record-modal__actions--stacked">
                  {canCancel && record.startsAt && record.endsAt && (
                    <AddToCalendarButton
                      stretched
                      event={{
                        title: record.service,
                        startsAt: record.startsAt,
                        endsAt: record.endsAt,
                        trainer: record.staff,
                        studioName,
                      }}
                    />
                  )}
                  {canCancel && (
                    <button
                      type="button"
                      className="lotos-btn lotos-btn--danger lotos-btn--stretched"
                      onClick={() => setMode('confirm')}
                    >
                      Отменить запись
                    </button>
                  )}
                  <button
                    type="button"
                    className={`lotos-btn lotos-btn--${canCancel ? 'secondary' : 'primary'} lotos-btn--stretched`}
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
